#!/usr/bin/env python3
"""
agent/phaseP/find_native_P.py -- 22 Oct 2026. READ-ONLY. For each claim held as "native_absent but the author has rows
in the corpus" (agent/phaseP/claims_P_report.tsv), look for the NATIVE's own group: another live group that shares a
witness document with the held group AT THE SAME PLACE (byte spans overlap on the same file, either side), and that
holds at least one row whose author carries the claimed author's surname key.

OUT agent/phaseP/native_candidates_P.tsv
  held_group  author  cand_group  cand_rows  shared_spans  author_rows_in_cand  cand_front  sample_cand_passage
Several candidates per held group are possible (a native split in several groups); none = the native's passage is
not reached by any witness of the held group (then it is a genuine absent-from-this-passage case, or needs reading).
  python3 -u agent/phaseP/find_native_P.py
"""
import configparser, csv, os, sys, unicodedata
from collections import defaultdict
import psycopg2
sys.path.insert(0, os.getcwd())
from surname_key import surname
csv.field_size_limit(sys.maxsize)
TAG = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "P"
cfg = configparser.ConfigParser(); cfg.read("/etc/text-pair/global_settings.ini"); D = cfg["DATABASE"]
cn = psycopg2.connect(user=D["database_user"], password=D["database_password"], database=D["database_name"])
cur = cn.cursor(); cur.execute("SET statement_timeout = 0")
def fold(s): return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").lower()
held = [r for r in csv.DictReader(open(f"agent/phaseP/claims_{TAG}_report.tsv", encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE)
        if r["decision"] == "HOLD" and r["detail"].startswith("native_absent but")]
out = []
for h in held:
    g = int(h["group"]); key = fold(surname(h["author"]))
    cur.execute("""SELECT source_filename, source_start_byte, source_end_byte, target_filename, target_start_byte, target_end_byte
                   FROM combined_align WHERE group_id = %s""", (g,))
    spans = []
    for sf, ss, se, tf, ts, te in cur.fetchall():
        spans += [(sf, ss, se), (tf, ts, te)]
    hits = defaultdict(int)
    for f, s, e in set(spans):
        cur.execute("""SELECT group_id FROM combined_align WHERE group_id <> %s AND
                         ((source_filename = %s AND source_start_byte < %s AND source_end_byte > %s) OR
                          (target_filename = %s AND target_start_byte < %s AND target_end_byte > %s))""",
                    (g, f, e, s, f, e, s))
        for (c,) in cur.fetchall(): hits[c] += 1
    found = 0
    for c, n in sorted(hits.items(), key=lambda x: -x[1]):
        cur.execute("""SELECT count(*), count(*) FILTER (WHERE lower(source_author) LIKE %s OR lower(target_author) LIKE %s),
                              (array_agg(source_author || ' ' || source_year ORDER BY source_year, rowid))[1],
                              (array_agg(left(regexp_replace(source_passage,'\\s+',' ','g'),140) ORDER BY source_year, rowid))[1]
                       FROM combined_align WHERE group_id = %s""", (f"%{key}%", f"%{key}%", c))
        nr, na, front, samp = cur.fetchone()
        if na:
            out.append((g, h["author"][:40], c, nr, n, na, (front or "")[:50], (samp or "").replace("\t", " ")))
            found += 1
    if not found: out.append((g, h["author"][:40], "", 0, 0, 0, "NO CANDIDATE", ""))
    print(f"  {g:>12}  {h['author'][:35]:35}  candidates {found}", flush=True)
with open(f"agent/phaseP/native_candidates_{TAG}.tsv", "w", encoding="utf-8") as fh:
    fh.write("held_group\tauthor\tcand_group\tcand_rows\tshared_spans\tauthor_rows_in_cand\tcand_front\tsample_cand_passage\n")
    for o in out: fh.write("\t".join(str(x) for x in o) + "\n")
print(f"-> agent/phaseP/native_candidates_{TAG}.tsv")
