#!/usr/bin/env python3
"""
agent/partB_joins_21oct.py -- 21 Oct 2026. Part B phase 2, last step: joins between groups that are NOT natives of
the phase-2 plan (phase-1 groups that carry one passage under two wordings, Glenn 21 Oct 12:41; a few
"wrong-way" sources; the restored convocation letter). Dry run by default; --commit.

IN  agent/partB/joins_nonnative.tsv    from  into  why        (from = a group id, or rowid:N for one row)
Every row of `from` (or the one row) takes group_id = into, in ONE transaction; COUNT(*) asserted unchanged.
Records: split_manifest.tsv (natural key, old/new group, op move) and, for whole-group joins,
merged_clusters_manifest.tsv (old -> new), so carry_forward_tombstones.py can carry any claim on `from`.
Run AFTER partB_apply_21oct.py --phase regroup on plan2 (ids named here are post-phase-2 live ids).
  python3 -u agent/partB_joins_21oct.py [--commit]
"""
import argparse, configparser, csv, os, sys, time
import psycopg2
from psycopg2.extras import execute_values
ap = argparse.ArgumentParser()
ap.add_argument("--inp", default="agent/partB/joins_nonnative.tsv")
ap.add_argument("--table", default="combined_align")
ap.add_argument("--manifest", default="split_manifest.tsv")
ap.add_argument("--clusters-manifest", default="merged_clusters_manifest.tsv")
ap.add_argument("--commit", action="store_true")
a = ap.parse_args()
cfg = configparser.ConfigParser(); cfg.read("/etc/text-pair/global_settings.ini"); D = cfg["DATABASE"]
cn = psycopg2.connect(user=D["database_user"], password=D["database_password"], database=D["database_name"])
cur = cn.cursor(); cur.execute("SET statement_timeout = 0")
J = [r for r in csv.reader(open(a.inp, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE) if r and not r[0].startswith("#")]
moves = []; whole = []; bad = 0
print("=" * 78); print("PART B JOINS" + ("" if a.commit else " (dry run)")); print("=" * 78)
for r in J:
    f, into, why = r[0].strip(), int(r[1]), (r[2] if len(r) > 2 else "")
    cur.execute(f"SELECT count(*) FROM {a.table} WHERE group_id = %s", (into,)); n_into = cur.fetchone()[0]
    if f.startswith("rowid:"):
        rid = int(f[6:])
        cur.execute(f"""SELECT rowid, group_id, source_filename, source_start_byte, target_filename, target_start_byte
                        FROM {a.table} WHERE rowid = %s""", (rid,)); rows = cur.fetchall()
    else:
        cur.execute(f"""SELECT rowid, group_id, source_filename, source_start_byte, target_filename, target_start_byte
                        FROM {a.table} WHERE group_id = %s""", (int(f),)); rows = cur.fetchall()
    ok = bool(rows) and n_into > 0
    print(f"  {f:>16} -> {into:<14} rows {len(rows):>4}  into has {n_into:>5}  {'OK' if ok else '!! SKIPPED (not live)'}  {why[:60]}")
    if not ok: bad += 1; continue
    rows = [x for x in rows if x[1] != into]
    moves += [(x, into, why) for x in rows]
    if not f.startswith("rowid:"): whole.append((int(f), into, len(rows), why))
print(f"\n  rows to move {len(moves):,}; whole-group joins {len(whole)}; skipped {bad}")
if not a.commit: print("  Dry run. Nothing was changed."); sys.exit(0)
cur.execute(f"SELECT count(*) FROM {a.table}"); before = cur.fetchone()[0]
cur.execute("CREATE TEMP TABLE _j (rowid bigint PRIMARY KEY, g bigint, old bigint) ON COMMIT DROP")
execute_values(cur, "INSERT INTO _j VALUES %s", [(x[0], g, x[1]) for x, g, _ in moves])
cur.execute(f"UPDATE {a.table} t SET group_id = j.g FROM _j j WHERE t.rowid = j.rowid AND t.group_id = j.old")
n = cur.rowcount
cur.execute(f"SELECT count(*) FROM {a.table}"); after = cur.fetchone()[0]
if n != len(moves) or after != before:
    cn.rollback(); sys.exit(f"ROLLED BACK: updated {n} of {len(moves)}; count {before} -> {after}")
new = not os.path.exists(a.manifest)
with open(a.manifest, "a", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, delimiter="\t")
    if new: w.writerow(["source_filename", "source_start_byte", "target_filename", "target_start_byte", "old_group_id", "new_group_id", "op", "note"])
    for x, g, why in moves: w.writerow([x[2], x[3], x[4], x[5], x[1], g, "move", f"Part B join 21 Oct: {why}"])
cn.commit()
with open(a.clusters_manifest, "a", encoding="utf-8") as fh:
    for f, g, k, why in whole: fh.write(f"{f}\t{g}\t{k}\tpartB_joins_21oct.py\t{time.strftime('%Y-%m-%d')}\t\t{why}\n")
print(f"  COMMITTED: {n:,} rows; count {before:,} -> {after:,} UNCHANGED; {len(whole)} succession lines appended.")
