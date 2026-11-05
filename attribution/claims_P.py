#!/usr/bin/env python3
"""
agent/phaseP/claims_P.py -- 22 Oct 2026. Claims from the Phase P readers' `source` lines (agent/phaseP/claims_P.tsv:
group author title year status latin reason), after the regroup is applied and the tables rebuilt.

DRY RUN (default) -- a report, nothing written (agent/phaseP/claims_P_report.tsv):
  * group not live, or already claimed -> SKIP (listed; an existing claim needs --update by hand)
  * latin = a PHI author key  -> the author string is the PHI form already used in provenance at year 99
            (most frequent attributed_author with year 99 containing the key); none found -> HOLD
    latin = VULGATE           -> the corpus's Vulgate authority (author string from provenance, year 1450)
  * other authors: the string is checked against the corpus (source_author, exact).
      status resolved: the author must be on a row of the group; if not exact, the corpus form found ON the group's
              rows with the same surname is used; none -> HOLD. Then the FRONT is simulated: the group's earliest
              source year v the author's earliest row in the group:
                same year -> the claim alone makes the author front (surname tie-break)      [ATTR]
                later     -> an earlier-dated row fronts: claim + record_native_override        [ATTR+OVR]
      native_first_printing / native_absent: exact corpus string, or a unique corpus string with that surname
              (switched); otherwise the reader's string is kept with --force-author ONLY if no corpus string
              shares the surname (a new person); several candidates -> HOLD.
--commit: record_attribution.py per line (and record_native_override.py where [ATTR+OVR]).
key "!+" (23 Oct): as "!" and also record the front override.
key "!" (22 Oct, t02): write the author string as given (a new person sharing a surname with a corpus author).
Run from the TextPAIR root:  python3 -u agent/phaseP/claims_P.py --tag t01 [--commit]
"""
import configparser, csv, os, subprocess, sys, unicodedata
import psycopg2
sys.path.insert(0, os.getcwd())
from surname_key import surname
COMMIT = "--commit" in sys.argv
TAG = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "P"
csv.field_size_limit(sys.maxsize)
J = list(csv.DictReader(open(f"agent/phaseP/claims_{TAG}.tsv", encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
cfg = configparser.ConfigParser(); cfg.read("/etc/text-pair/global_settings.ini"); D = cfg["DATABASE"]
cn = psycopg2.connect(user=D["database_user"], password=D["database_password"], database=D["database_name"])
cur = cn.cursor(); cur.execute("SET statement_timeout = 0")
def fold(s): return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").lower()

cur.execute("SELECT group_id FROM combined_align_groups_provenance"); claimed = {r[0] for r in cur.fetchall()}
cur.execute("SELECT attributed_author, count(*) FROM combined_align_groups_provenance WHERE attributed_year = 99 GROUP BY 1")
phi = cur.fetchall()
cur.execute("SELECT attributed_author, attributed_year, count(*) FROM combined_align_groups_provenance WHERE attributed_author ILIKE '%%vulgat%%' OR attributed_author = 'author_03346' GROUP BY 1,2 ORDER BY 3 DESC")
vulg = cur.fetchall()
cur.execute("SELECT DISTINCT source_author FROM combined_align UNION SELECT DISTINCT target_author FROM combined_align")
corpus_auth = [r[0] for r in cur.fetchall() if r[0]]
by_sur = {}
for a in corpus_auth: by_sur.setdefault(fold(surname(a)), set()).add(a)

import re as _re
def pick(a):
    """exact corpus string; else the unique corpus string containing the reader's name (dates stripped), narrowed by the
    reader's birth year if given; returns (string, None) or (None, candidates)"""
    if a in corpus_auth: return a, None
    base = fold(_re.sub(r"\s*\(.*$", "", a)).strip(); yr = _re.search(r"\((\d{4})", a)
    c = [x for x in corpus_auth if base and base in fold(x)]
    if yr: c = [x for x in c if yr.group(1) in x] or c
    if len(c) == 1: return c[0], None
    last = fold(base.split()[-1]) if base else ""
    loose = sorted({x for x in corpus_auth if last and _re.search(r"\b" + _re.escape(last) + r"\b", fold(x))})
    return None, (c or loose)
cur.execute("SELECT attributed_author, count(*) FROM combined_align_groups_provenance WHERE (attributed_author ILIKE 'la sainte bible%%' OR attributed_author = 'author_03337') AND attributed_year = 1450 GROUP BY 1 ORDER BY 2 DESC")
bible = cur.fetchall()
NOHOLD = {a for a in corpus_auth if fold(a).startswith("la sainte bible")}  # the Bible authority: absent passages are claimed, not searched
rep = []; jobs = []
for j in J:
    g = int(j["group"]); a, t, y, st, lat = j["author"], j["title"], j["year"], j["status"], j["latin"]
    cur.execute("SELECT rowid, source_year, source_author, target_year, target_author FROM combined_align WHERE group_id = %s", (g,))
    R = cur.fetchall()
    if not R: rep.append((g, "SKIP", "group not live", a)); continue
    if g in claimed: rep.append((g, "SKIP", "already claimed (decide by hand, --update)", a)); continue
    force = False; ovr = False
    if lat == "VULGATE":
        if not vulg: rep.append((g, "HOLD", "no Vulgate authority string in provenance", a)); continue
        a, y = vulg[0][0], str(vulg[0][1] or 1450)
    elif lat:
        c = sorted([(n, s) for s, n in phi if fold(lat) in fold(s)], reverse=True)
        if not c: rep.append((g, "HOLD", f"no PHI string at year 99 for {lat}", a)); continue
        a, y = c[0][1], "99"
    else:
        if a not in corpus_auth and not fold(a).startswith("la sainte bible"):
            p, _ = pick(a)              # a reader's short or truncated form ("Jean Racine (1639") -> the one corpus string
            if p: a = p
        sur = fold(surname(a))
        key = (j.get("key") or "").strip()
        if fold(a).startswith("la sainte bible"):
            if not bible: rep.append((g, "HOLD", "no La Sainte Bible authority string in provenance", a)); continue
            a = bible[0][0]; NOHOLD.add(a); force = a not in corpus_auth
        elif key in ("!", "!+"):
            # 22 Oct (t02): a NEW person whose surname another corpus author shares (Jean Passerat v. Claude-François
            # Passerat; Pierre Le Tourneur's own preface): the reader's string is written as given, with --force-author;
            # no on-rows check and no override (any status)
            force = a not in corpus_auth
            ovr = key == "!+"   # 23 Oct: "!+" also records the front override (the source is in the group under no/another author, an earlier row fronts)
        elif st == "resolved" and key == "*":
            # the front document IS the source but is catalogued under another name (Dacier's remarks under Horace):
            # the claim only changes the displayed author; no on-rows check, no override
            p, cand = pick(a)
            if p: a = p
            elif cand: rep.append((g, "HOLD", f"commentator: corpus strings share the name, choose one: {cand[:4]}", a)); continue
            else: force = True
        elif st == "resolved":
            on_rows = {x for r in R for x in (r[2], r[4]) if x and (fold(key) in fold(x) if key else fold(surname(x)) == sur)}
            if a not in on_rows:
                if len(on_rows) == 1: a = on_rows.pop()
                else:
                    rows_auth = sorted({x for r in R for x in (r[2], r[4]) if x})
                    rep.append((g, "HOLD", f"resolved but author not on the group's rows exactly once: {sorted(on_rows)[:3]}; rows carry {rows_auth[:5]}", a)); continue
            ey = min(r[1] for r in R if r[1] is not None)
            # the front is chosen among SOURCE rows only: an author whose document sits only on the target side
            # cannot win a same-year tie, so that case needs an override too (pilot, 22 Oct: Richer, La Touche, Thomas)
            ay = min([r[1] for r in R if r[2] == a and r[1] is not None] or [9999])
            ovr = ay > ey
        else:
            if a not in corpus_auth:
                p, cand = pick(a)
                if p: a = p
                elif not cand and not by_sur.get(sur): force = True     # a person the corpus does not hold
                else: rep.append((g, "HOLD", f"corpus strings share the name, choose one: {(cand or sorted(by_sur.get(sur, [])))[:4]}", a)); continue
            if st == "native_absent" and a in corpus_auth and a not in NOHOLD:
                # the author HAS documents in the corpus: the native may sit in another group (fold, not claim)
                cur.execute("""SELECT count(*), string_agg(DISTINCT left(source_title,50), ' ; ') FROM combined_align
                               WHERE source_author = %s""", (a,))
                n, tt = cur.fetchone()
                rep.append((g, "HOLD", f"native_absent but the author has {n:,} source rows in the corpus ({(tt or '')[:120]}): find the native's group first", a)); continue
    rep.append((g, "ATTR+OVR" if ovr else "ATTR", f"{st} | {y} | {t[:60]}" + (" | force-author" if force else ""), a))
    jobs.append((g, a, t, y, st, j["reason"], force, ovr))

with open(f"agent/phaseP/claims_{TAG}_report.tsv", "w", encoding="utf-8") as fh:
    fh.write("group\tdecision\tdetail\tauthor\n")
    for r in rep: fh.write("\t".join(str(x) for x in r) + "\n")
from collections import Counter
print("=" * 78); print("PHASE P CLAIMS" + ("" if COMMIT else " (dry run)")); print("=" * 78)
print("  lines", len(J), dict(Counter(r[1] for r in rep)))
for r in rep:
    if r[1] in ("HOLD", "SKIP") or "force" in r[2]: print(f"  {r[1]:8} {r[0]:>12}  {r[3][:45]:45}  {r[2][:90]}")
print(f"  report: agent/phaseP/claims_{TAG}_report.tsv")
if not COMMIT: print("  Dry run. Nothing written."); sys.exit(0)
ok = 0
for g, a, t, y, st, why, force, ovr in jobs:
    cmd = ["python3", "record_attribution.py", "--group", str(g), "--author", a, "--title", t, "--year", y,
           "--status", st, "--reason", why, "--commit"] + (["--force-author"] if force else [])
    r1 = subprocess.run(cmd, capture_output=True, text=True)
    if r1.returncode: print(f"  !! attribution failed {g}: {r1.stdout[-300:]}{r1.stderr[-300:]}"); continue
    if ovr:
        r2 = subprocess.run(["python3", "record_native_override.py", "--group", str(g), "--candidates", str(g),
                             "--ruling-date", "22 Oct 2026", "--reason", f"Phase P {TAG}: {a} is in the group; an earlier-dated row (quoter or reprint) fronts", "--commit"],
                            capture_output=True, text=True)
        if r2.returncode: print(f"  !! override failed {g}: {r2.stdout[-300:]}{r2.stderr[-300:]}"); continue
    ok += 1
print(f"  COMMITTED {ok} of {len(jobs)}")
