#!/usr/bin/env python3
"""
rewrite_author_variants.py -- item 5: rewrite variant author strings to one canonical string
per person (Glenn, 19 Oct 2026: "I'm happy to rewrite the strings at this point", superseding
the 8 Sep authority-map ruling). MUTATING with --commit; dry run by default.

INPUT  --map TSV with columns variant, canonical (agent/author_variants_map.tsv, built from
       author_variants_census.py's proposals AFTER they were read line by line: only lines read
       SAME are in it). A variant appearing twice, or a canonical that is itself a variant,
       is refused.
TABLES the corpus tables corpus_source.CorpusSource gives (combined_align + the set-aside
       tables), both source_author and target_author -- as fix_document_author.py.
NOT TOUCHED: attributed_author on the provenance table (a judgement about a group, not a
       catalogue fact -- fix_document_author.py's rule); titles; derived tables (rebuild).

RECORD before any UPDATE, in the same transaction: every (table, side, rowid, old string) that
will change is copied to author_variant_backup_19oct, so the rewrite is exactly reversible.
RECONCILIATION: per table and side, rows selected == UPDATE rowcount, or the whole run rolls back.

  python3 -u agent/rewrite_author_variants.py --map agent/author_variants_map.tsv
  python3 -u agent/rewrite_author_variants.py --map agent/author_variants_map.tsv --commit
Then rebuild_derived_tables.py --commit, then the remap.
"""
import argparse, configparser, csv, os, sys
sys.path.insert(0, os.getcwd())
import psycopg2
from psycopg2.extras import execute_values
import corpus_source as CS
csv.field_size_limit(sys.maxsize)
ap = argparse.ArgumentParser()
ap.add_argument("--map", required=True)
ap.add_argument("--backup", default="author_variant_backup_19oct")
ap.add_argument("--commit", action="store_true")
CS.add_arguments(ap)
a = ap.parse_args()
M = {}
for r in csv.DictReader(open(a.map, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
    v, c = r["variant"], r["canonical"]
    if not v.strip() or not c.strip() or v == c: continue
    if v in M and M[v] != c: sys.exit(f"REFUSING: variant {v!r} mapped to two canonicals.")
    M[v] = c
bad = [c for c in set(M.values()) if c in M]
if bad: sys.exit(f"REFUSING: canonical(s) that are themselves variants: {bad[:5]}")
print(f"map: {len(M):,} variants -> {len(set(M.values())):,} canonical strings")
cfg = configparser.ConfigParser(); cfg.read("/etc/text-pair/global_settings.ini"); D = cfg["DATABASE"]
cn = psycopg2.connect(user=D["database_user"], password=D["database_password"], database=D["database_name"])
cur = cn.cursor(); cur.execute("SET statement_timeout = 0")
src = CS.CorpusSource(cur, a)
print(src.describe())
cur.execute("CREATE TEMP TABLE avmap (variant text PRIMARY KEY, canonical text)")
execute_values(cur, "INSERT INTO avmap VALUES %s", list(M.items()))
plan = []
for t in src.tables:
    cur.execute("SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = 'rowid'", (t,))
    has_rowid = cur.fetchone() is not None
    for side in ("source", "target"):
        col = f"{side}_author"
        cur.execute(f"SELECT count(*) FROM {t} x JOIN avmap m ON x.{col} = m.variant")
        n = cur.fetchone()[0]
        plan.append((t, side, n, has_rowid)); print(f"  {t}.{side}: {n:,} row(s) to rewrite" + ("" if has_rowid else "  (no rowid column: not backed up)"))
tot = sum(p[2] for p in plan)
print(f"\n  TOTAL {tot:,} row-sides")
if any(n and not hr for _, _, n, hr in plan):
    sys.exit("REFUSING: a table without rowid has rows to change; it cannot be backed up exactly.")
if not a.commit:
    cn.rollback(); print("\n  Dry run. Nothing written. Rerun with --commit."); sys.exit(0)
try:
    cur.execute(f"""CREATE TABLE IF NOT EXISTS {a.backup}
                    (tbl text, side text, rowid bigint, old_author text, new_author text)""")
    for t, side, n, _ in plan:
        if not n: continue
        col = f"{side}_author"
        cur.execute(f"""INSERT INTO {a.backup} SELECT %s, %s, x.rowid, x.{col}, m.canonical
                        FROM {t} x JOIN avmap m ON x.{col} = m.variant""", (t, side))
        if cur.rowcount != n: raise RuntimeError(f"{t}.{side}: backed up {cur.rowcount} != planned {n}")
        cur.execute(f"UPDATE {t} x SET {col} = m.canonical FROM avmap m WHERE x.{col} = m.variant")
        if cur.rowcount != n: raise RuntimeError(f"{t}.{side}: updated {cur.rowcount} != planned {n}")
        print(f"  {t}.{side}: {n:,} rewritten")
    cn.commit()
except Exception as e:
    cn.rollback(); sys.exit(f"ROLLED BACK, nothing written: {e}")
print(f"\n  COMMITTED: {tot:,} row-sides rewritten; old strings in {a.backup}. Now rebuild, then the remap.")
