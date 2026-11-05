#!/usr/bin/env python3
"""
agent/dump_phaseP.py -- 22 Oct 2026. READ-ONLY. Complete reading, Phase P (groups of 2-9 live rows).

1. Lists every live group of --min..--max rows that still has at least one row NOT in rows_read (the ledger),
   with its front row (earliest source_year, then lowest rowid) and that row's source file and byte.
   Sorted by (front file, front byte): fragments of one work land next to each other, so a reader can see
   two groups carrying one passage and fold them.
   OUT agent/phaseP/groups_P.tsv   seq group n unread front_file front_byte front_year

2. Cuts the sorted list into batches of about --rows rows (a group is never split) and dumps the rows of the
   batches asked for, passages --chars long.
   --pilot K --seed S : K batches starting at random points of the list (each batch contiguous)
   --batches a-b      : batches a..b of the full cut (later runs)
   OUT agent/phaseP/dump_<tag>.tsv  batch seq group_id rowid sy sa st ty ta tt sp tp

  python3 -u agent/dump_phaseP.py --pilot 10 --seed 22 --tag pilot
"""
import argparse, configparser, csv, os, random, sys, time
import psycopg2
csv.field_size_limit(sys.maxsize)
ap = argparse.ArgumentParser()
ap.add_argument("--min", type=int, default=2)
ap.add_argument("--max", type=int, default=9)
ap.add_argument("--rows", type=int, default=400)
ap.add_argument("--chars", type=int, default=400)
ap.add_argument("--pilot", type=int, default=0)
ap.add_argument("--seed", type=int, default=22)
ap.add_argument("--batches", default="")
ap.add_argument("--tag", default="pilot")
ap.add_argument("--table", default="combined_align")
a = ap.parse_args()
t0 = time.time()
os.makedirs("agent/phaseP", exist_ok=True)
cfg = configparser.ConfigParser(); cfg.read("/etc/text-pair/global_settings.ini"); D = cfg["DATABASE"]
cn = psycopg2.connect(user=D["database_user"], password=D["database_password"], database=D["database_name"])
cur = cn.cursor(); cur.execute("SET statement_timeout = 0")

cur.execute(f"""
  WITH g AS (SELECT group_id, count(*) n FROM {a.table} GROUP BY 1 HAVING count(*) BETWEEN %s AND %s),
       u AS (SELECT t.group_id, count(*) FILTER (WHERE r.rowid IS NULL) unread
             FROM {a.table} t JOIN g USING (group_id)
             LEFT JOIN (SELECT DISTINCT rowid FROM rows_read) r ON r.rowid = t.rowid GROUP BY 1),
       f AS (SELECT DISTINCT ON (t.group_id) t.group_id, t.source_filename, t.source_start_byte, t.source_year
             FROM {a.table} t JOIN g USING (group_id) ORDER BY t.group_id, t.source_year, t.rowid)
  SELECT g.group_id, g.n, u.unread, f.source_filename, f.source_start_byte, f.source_year
  FROM g JOIN u USING (group_id) JOIN f USING (group_id) WHERE u.unread > 0
  ORDER BY f.source_filename, f.source_start_byte, g.group_id""", (a.min, a.max))
G = cur.fetchall()
with open("agent/phaseP/groups_P.tsv", "w", encoding="utf-8") as fh:
    fh.write("seq\tgroup\tn\tunread\tfront_file\tfront_byte\tfront_year\n")
    for i, r in enumerate(G): fh.write(f"{i}\t" + "\t".join(str(x) for x in r) + "\n")
tot = sum(r[1] for r in G)
print(f"[{time.time()-t0:4.0f}s] groups of {a.min}-{a.max} rows with unread rows: {len(G):,} ({tot:,} rows) -> agent/phaseP/groups_P.tsv", flush=True)

# cut into batches
cuts = []; cur_b = []; nr = 0
for i, r in enumerate(G):
    if cur_b and nr + r[1] > a.rows: cuts.append(cur_b); cur_b = []; nr = 0
    cur_b.append(i); nr += r[1]
if cur_b: cuts.append(cur_b)
print(f"  full cut: {len(cuts):,} batches of about {a.rows} rows", flush=True)
if a.pilot:
    random.seed(a.seed); pick = sorted(random.sample(range(len(cuts)), a.pilot))
elif a.batches:
    lo, hi = (int(x) for x in a.batches.split("-")); pick = list(range(lo, hi + 1))
else:
    print("  no --pilot / --batches: list only."); sys.exit(0)
want = {}
for b in pick:
    for i in cuts[b]: want[G[i][0]] = (b, i)
cl = lambda v: str(v).replace("\t", " ").replace("\n", " ")
q = f"""SELECT group_id, rowid, source_year, source_author, left(source_title,60), target_year, target_author,
        left(target_title,60), left(regexp_replace(source_passage,'\\s+',' ','g'),{a.chars}),
        left(regexp_replace(target_passage,'\\s+',' ','g'),{a.chars})
        FROM {a.table} WHERE group_id = ANY(%s) ORDER BY group_id, source_year, rowid"""
out = f"agent/phaseP/dump_{a.tag}.tsv"; n = 0
rows = []
ids = list(want)
for i in range(0, len(ids), 2000):
    cur.execute(q, (ids[i:i+2000],)); rows += cur.fetchall()
rows.sort(key=lambda r: (want[r[0]][1], r[2] if r[2] is not None else 0, r[1]))
with open(out, "w", encoding="utf-8") as fh:
    fh.write("batch\tseq\tgroup_id\trowid\tsy\tsa\tst\tty\tta\ttt\tsp\ttp\n")
    for r in rows:
        b, s = want[r[0]]; fh.write(f"{b}\t{s}\t" + "\t".join(cl(v) for v in r) + "\n"); n += 1
print(f"[{time.time()-t0:4.0f}s] batches {pick}: {len(want):,} groups, {n:,} rows -> {out}", flush=True)
