#!/usr/bin/env python3
"""
agent/phaseP/dump_native_pairs.py -- 22 Oct 2026. READ-ONLY. For reading the native candidates before any join.
IN  agent/phaseP/native_candidates_<tag>.tsv (find_native_P.py)
OUT agent/phaseP/native_pairs_<tag>.txt : per held group, ALL its rows, then for each candidate group the rows that
    share a witness byte-span with the held group (marked *) and, if the candidate is larger, the next rows up to
    --ctx in front-first order, with S/T passages (--chars).
  python3 -u agent/phaseP/dump_native_pairs.py --tag t01
"""
import argparse, configparser, csv, sys
from collections import defaultdict
import psycopg2
csv.field_size_limit(sys.maxsize)
ap = argparse.ArgumentParser()
ap.add_argument("--tag", default="t01"); ap.add_argument("--chars", type=int, default=300); ap.add_argument("--ctx", type=int, default=4)
a = ap.parse_args()
cfg = configparser.ConfigParser(); cfg.read("/etc/text-pair/global_settings.ini"); D = cfg["DATABASE"]
cn = psycopg2.connect(user=D["database_user"], password=D["database_password"], database=D["database_name"])
cur = cn.cursor(); cur.execute("SET statement_timeout = 0")
C = defaultdict(list); AU = {}
for r in csv.DictReader(open(f"agent/phaseP/native_candidates_{a.tag}.tsv", encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
    AU[r["held_group"]] = r["author"]
    if r["cand_group"]: C[r["held_group"]].append(r["cand_group"])
Q = f"""SELECT rowid, source_year, source_author, left(source_title,55), target_year, target_author, left(target_title,55),
        left(regexp_replace(source_passage,'\\s+',' ','g'),{a.chars}), left(regexp_replace(target_passage,'\\s+',' ','g'),{a.chars}),
        source_filename, source_start_byte, source_end_byte, target_filename, target_start_byte, target_end_byte
        FROM combined_align WHERE group_id = %s ORDER BY source_year, rowid"""
def rows(g): cur.execute(Q, (int(g),)); return cur.fetchall()
def fmt(r, mark=" "):
    return (f" {mark} row {r[0]} | S {r[1]} {(r[2] or '')[:30]} | {r[3]} || T {r[4]} {(r[5] or '')[:30]} | {r[6]}\n"
            f"      S: {r[7]}\n      T: {r[8]}\n")
out = open(f"agent/phaseP/native_pairs_{a.tag}.txt", "w", encoding="utf-8"); n = 0
for h in AU:
    if not C[h]: continue
    H = rows(h); spans = set()
    for r in H: spans |= {(r[9], r[10], r[11]), (r[12], r[13], r[14])}
    out.write(f"\n==================== HELD {h}  ({len(H)} rows)  claimed: {AU[h]} ====================\n")
    for r in H: out.write(fmt(r))
    for c in C[h]:
        R = rows(c)
        def shares(r): return any(f == r[9] and s < r[11] and e > r[10] or f == r[12] and s < r[14] and e > r[13] for f, s, e in spans)
        sh = [r for r in R if shares(r)]; rest = [r for r in R if r not in sh][:a.ctx]
        out.write(f"\n  ---------- CANDIDATE {c}  ({len(R)} rows; {len(sh)} share a witness span with HELD, marked *) ----------\n")
        for r in sh: out.write(fmt(r, "*"))
        if rest: out.write(f"   (first {len(rest)} other rows of {c}:)\n")
        for r in rest: out.write(fmt(r))
        n += 1
out.close()
print(f"{len(AU)} held groups, {n} candidate pairs -> agent/phaseP/native_pairs_{a.tag}.txt")
