#!/usr/bin/env python3
"""
agent/phaseP/locate_in_file.py -- 3 Nov 2026 (t16 translation claims). Read-only.

For each group listed in --groups FILE (first column = group_id), and for each row side whose filename contains one of
the --match substrings, report WHERE in that TEI file the aligned span sits: the last two <head> texts before the span,
and whether the span lies inside a <note> element. Used to tell Neri's chapters from Merret's observations and
Kunckel's remarks in Holbach's Art de la verrerie, Wallerius from Holbach's notes, Toland from Holbach's notice,
Shaftesbury from Diderot's notes, Théophraste from La Bruyère's Discours.

Run from the TextPAIR root:
  python3 -u agent/phaseP/locate_in_file.py --groups agent/phaseP/t16_trans_groups.txt \
      --match "Art de la verrerie" --match "Minéralogie" --match "Lettres philosophiques" \
      --match "mérite et la vertu" --match "Théophraste" > agent/phaseP/t16_locate.tsv
(--match is tested against the row's title, case-insensitively.)
"""
import configparser, re, sys, html
import psycopg2

args = sys.argv[1:]
gfile = args[args.index("--groups") + 1]
matches = [args[i + 1].lower() for i, a in enumerate(args) if a == "--match"]
groups = []
for line in open(gfile, encoding="utf-8"):
    f = line.split("\t")[0].strip()
    if f.isdigit(): groups.append(int(f))

cfg = configparser.ConfigParser(); cfg.read("/etc/text-pair/global_settings.ini"); D = cfg["DATABASE"]
cn = psycopg2.connect(user=D["database_user"], password=D["database_password"], database=D["database_name"])
cur = cn.cursor()

cache = {}
HEAD = re.compile(rb"<head[^>]*>(.*?)</head>", re.S)
NOTE_O = re.compile(rb"<note\b[^>]*>")
NOTE_C = re.compile(rb"</note>")
def index(path):
    if path in cache: return cache[path]
    try: b = open(path, "rb").read()
    except Exception as e:
        cache[path] = None; print(f"# cannot read {path}: {e}", file=sys.stderr); return None
    heads = [(m.start(), re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(1).decode("utf-8", "replace")))).strip())
             for m in HEAD.finditer(b)]
    opens = [m.start() for m in NOTE_O.finditer(b)]; closes = [m.end() for m in NOTE_C.finditer(b)]
    notes = []
    ci = 0
    for o in opens:
        while ci < len(closes) and closes[ci] < o: ci += 1
        if ci < len(closes): notes.append((o, closes[ci]))
    cache[path] = (heads, notes); return cache[path]

print("group\trowid\tside\tfile\tstart\tend\thead_before_2\thead_before_1\tin_note")
for g in groups:
    cur.execute("""SELECT rowid, source_title, source_filename, source_start_byte, source_end_byte,
                          target_title, target_filename, target_start_byte, target_end_byte
                   FROM combined_align WHERE group_id = %s ORDER BY rowid""", (g,))
    rows = cur.fetchall()
    if not rows: print(f"{g}\t\t\t(group not live)"); continue
    seen = set()
    for rid, st, sf, ss, se, tt, tf, ts, te in rows:
        for side, title, fn, s, e in (("S", st, sf, ss, se), ("T", tt, tf, ts, te)):
            if not fn or not any(m in (title or "").lower() for m in matches): continue
            if (fn, s) in seen: continue
            seen.add((fn, s))
            ix = index(fn)
            if not ix: print(f"{g}\t{rid}\t{side}\t{fn}\t{s}\t{e}\t\t(file unreadable)\t"); continue
            heads, notes = ix
            before = [h for h in heads if h[0] <= (s or 0)]
            h1 = before[-1][1][:90] if before else ""; h2 = before[-2][1][:90] if len(before) > 1 else ""
            inn = "Y" if any(o <= (s or 0) < c for o, c in notes) else "N"
            print(f"{g}\t{rid}\t{side}\t{fn.rsplit('/',1)[-1]}\t{s}\t{e}\t{h2}\t{h1}\t{inn}")
