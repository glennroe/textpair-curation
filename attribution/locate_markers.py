#!/usr/bin/env python3
"""
agent/phaseP/locate_markers.py -- 3 Nov 2026 (t16 translation claims, second pass). Read-only.

Like locate_in_file.py, but (1) selects row sides by FILENAME or TITLE substring (--match, case-insensitive), and
(2) inside the TEI file reports the last editorial marker before the aligned span -- "Remarques de ...",
"Observations de ...", "Note(s) du traducteur", "REMARQUES", "OBSERVATIONS", "NOTE" -- with its byte offset, plus the
last <head>. Tells Neri's chapter text from Merret's observations and Kunckel's remarks inside one chapter (they carry no
<head> of their own), and Wallerius's text from Holbach's notes.
It also prints, for every listed group, the titles and filenames of ALL its rows (so a group the --match missed shows
which file to match next time).

Run from the TextPAIR root:
  python3 -u agent/phaseP/locate_markers.py --groups agent/phaseP/t16_trans_groups.txt \
      --match verrerie --match mineralog --match theophraste --match "théophraste" --match "caracteres" \
      --match "caractères" --match "merite" --match "mérite" > agent/phaseP/t16_markers.tsv
"""
import configparser, re, sys, html
import psycopg2

args = sys.argv[1:]
gfile = args[args.index("--groups") + 1]
matches = [args[i + 1].lower() for i, a in enumerate(args) if a == "--match"]
groups = [int(l.split("\t")[0]) for l in open(gfile, encoding="utf-8") if l.split("\t")[0].strip().isdigit()]

cfg = configparser.ConfigParser(); cfg.read("/etc/text-pair/global_settings.ini"); D = cfg["DATABASE"]
cn = psycopg2.connect(user=D["database_user"], password=D["database_password"], database=D["database_name"])
cur = cn.cursor()

HEAD = re.compile(rb"<head[^>]*>(.*?)</head>", re.S)
MARK = re.compile(rb"(Remarques?\s+de\s+[^<.]{0,40}|Observations?\s+de\s+[^<.]{0,40}|Notes?\s+du\s+[Tt]raducteur|REMARQUES?\b[^<]{0,40}|OBSERVATIONS?\b[^<]{0,40}|NOTES?\s+DU\s+TRADUCTEUR|<note\b)", re.S)
cache = {}
def clean(b): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", b.decode("utf-8", "replace")))).strip()
def index(path):
    if path not in cache:
        try:
            b = open(path, "rb").read()
            cache[path] = ([(m.start(), clean(m.group(1))) for m in HEAD.finditer(b)],
                           [(m.start(), clean(m.group(1)) or "<note>") for m in MARK.finditer(b)])
        except Exception as e:
            print(f"# cannot read {path}: {e}", file=sys.stderr); cache[path] = None
    return cache[path]

print("group\trowid\tside\tauthor\ttitle\tfile\tstart\tend\tlast_head\thead_offset\tlast_marker\tmarker_offset\tbytes_since_marker")
for g in groups:
    cur.execute("""SELECT rowid, source_author, source_title, source_filename, source_start_byte, source_end_byte,
                          target_author, target_title, target_filename, target_start_byte, target_end_byte
                   FROM combined_align WHERE group_id = %s ORDER BY rowid""", (g,))
    rows = cur.fetchall()
    if not rows: print(f"{g}\t\t\t(group not live)"); continue
    for rid, sa, st, sf, ss, se, ta, tt, tf, ts, te in rows:
        for side, au, title, fn, s, e in (("S", sa, st, sf, ss, se), ("T", ta, tt, tf, ts, te)):
            hit = any(m in (title or "").lower() or m in (fn or "").lower() for m in matches)
            base = f"{g}\t{rid}\t{side}\t{(au or '')[:40]}\t{(title or '')[:50]}\t{(fn or '').rsplit('/',1)[-1]}\t{s}\t{e}"
            if not hit: print(base + "\t(not matched)\t\t\t\t"); continue
            ix = index(fn) if fn else None
            if not ix: print(base + "\t(file unreadable)\t\t\t\t"); continue
            heads, marks = ix
            h = [x for x in heads if x[0] <= (s or 0)]; mk = [x for x in marks if x[0] <= (s or 0)]
            lh = h[-1][1][:70] if h else ""; ho = h[-1][0] if h else ""
            lm, lo = (mk[-1][1][:60], mk[-1][0]) if mk else ("", "")
            since = (s - lo) if mk else ""
            print(f"{base}\t{lh}\t{ho}\t{lm}\t{lo}\t{since}")
