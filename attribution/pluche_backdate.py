#!/usr/bin/env python3
"""
agent/phaseP/pluche_backdate.py -- 4 Nov 2026. Writes agent/phaseP/claims_t17p.tsv (claims_P format). Read-only on the DB.

Glenn 4 Nov: the Goldsmith Pluche files are the Estienne reissue (t.1 1754, t.2-3 1752, t.4-8 1755); first printings
t.1 1732, t.2 1735, t.3 1735, t.4 1739, t.5 1746, t.6 1746, t.7 1746, t.8 1750. Blanket rule (approved 4 Nov):
for every live group holding a row of Pluche tome N whose earliest OTHER witness (rows not Pluche-v-Pluche) is
  >= first printing of tome N  and  < the reissue year  -> claim Pluche, tome N, first-printing year, resolved
     (claims_P records the front override: Pluche's row is dated later than the earlier quoter);
  <  first printing of tome N                          -> no claim (Pluche quotes an earlier text), listed;
  already claimed in provenance                        -> skipped, listed.
Run from cleaned/:  python3 -u agent/phaseP/pluche_backdate.py   then   python3 -u agent/phaseP/claims_P.py --tag t17p
"""
import configparser, re
import psycopg2
FIRST = {1: 1732, 2: 1735, 3: 1735, 4: 1739, 5: 1746, 6: 1746, 7: 1746, 8: 1750}
cfg = configparser.ConfigParser(); cfg.read("/etc/text-pair/global_settings.ini"); D = cfg["DATABASE"]
cn = psycopg2.connect(user=D["database_user"], password=D["database_password"], database=D["database_name"]); cur = cn.cursor()
cur.execute("""SELECT group_id, rowid, source_title, source_filename, source_year, target_title, target_filename, target_year
               FROM combined_align WHERE group_id IN (SELECT DISTINCT group_id FROM combined_align
               WHERE source_filename LIKE '%%modern_goldsmith_190100661%%' OR target_filename LIKE '%%modern_goldsmith_190100661%%'
                  OR source_filename LIKE '%%modern_goldsmith_190100660%%' OR target_filename LIKE '%%modern_goldsmith_190100660%%')""")
def tome(fn):
    m = re.search(r"modern_goldsmith_19010066[01]001(0\d)\.tei", fn or "")
    return int(m.group(1)) if m else None
G = {}
for g, rid, st, sf, sy, tt, tf, ty in cur.fetchall():
    ts, tt_ = tome(sf), tome(tf)
    d = G.setdefault(g, {"tomes": set(), "years": [], "reissue": []})
    for t, fn in ((ts, sf), (tt_, tf)):
        if t: d["tomes"].add(t)
    if ts and tt_: continue                      # Pluche v Pluche
    if ts: d["years"].append(ty)
    elif tt_: d["years"].append(sy)
cur.execute("SELECT group_id FROM combined_align_groups_provenance"); claimed = {r[0] for r in cur.fetchall()}
REISSUE = {1: 1754, 2: 1752, 3: 1752, 4: 1755, 5: 1755, 6: 1755, 7: 1755, 8: 1755}
out, rep = [], []
for g, d in sorted(G.items()):
    if not d["tomes"] or not d["years"]: rep.append((g, "SKIP", "no other witness")); continue
    t = min(d["tomes"], key=lambda x: FIRST[x]); fp = FIRST[t]; om = min(y for y in d["years"] if y)
    if g in claimed: rep.append((g, "SKIP", f"already claimed (t.{t}, other {om})")); continue
    if om >= REISSUE[t]: rep.append((g, "SKIP", f"front already Pluche or later (t.{t}, other {om})")); continue
    if om < fp: rep.append((g, "NO CLAIM", f"earliest other witness {om} precedes t.{t} ({fp}): Pluche quotes")); continue
    out.append((str(g), "Antoine Pluche (1688-1761)", f"Le spectacle de la nature, t. {t}", str(fp), "resolved", "",
                f"Glenn 4 Nov (t17): Pluche back-dating rule; t.{t} first printed {fp}, corpus file is the Estienne reissue {REISSUE[t]}; earliest other witness {om}", ""))
    rep.append((g, "CLAIM", f"t.{t} {fp}, other {om}"))
with open("agent/phaseP/claims_t17p.tsv", "w", encoding="utf-8") as fh:
    fh.write("group\tauthor\ttitle\tyear\tstatus\tlatin\treason\tkey\n")
    for r in out: fh.write("\t".join(r) + "\n")
with open("agent/phaseP/pluche_backdate_report.tsv", "w", encoding="utf-8") as fh:
    for r in rep: fh.write("\t".join(str(x) for x in r) + "\n")
from collections import Counter
print("groups", len(G), dict(Counter(r[1] for r in rep)), "-> agent/phaseP/claims_t17p.tsv; report agent/phaseP/pluche_backdate_report.tsv")
for r in rep:
    if r[1] == "NO CLAIM": print("  ", r)
