#!/usr/bin/env python3
"""
agent/reading_ledger.py -- 21 Oct 2026. The reading ledger: which rows a reader (Claude or an agent) has READ IN FULL,
when, in which campaign, with what verdict. Coverage becomes a query instead of a guess.

TABLE rows_read (rowid, group_id, campaign, read_date, reader, verdict, note), PRIMARY KEY (rowid, campaign).
It is NOT a derived table: rebuild_derived_tables.py never touches it. A row read in two campaigns has two lines.
Only rows whose own text was shown to a reader go in -- never a group judged on samples or a front.

  python3 agent/reading_ledger.py --init                                   create the table (idempotent)
  python3 agent/reading_ledger.py --add FILE --campaign NAME [--date YYYY-MM-DD] [--reader agent]
        [--rowid-col rowid] [--group-col from_group] [--verdict-col action] [--commit]
        FILE: TSV with a header; one line per row read. Dry run by default.
  python3 agent/reading_ledger.py --report                                 coverage of the LIVE table by group-size band

Backfill of 21 Oct (Part B, every row shown):
  python3 agent/reading_ledger.py --add agent/partB/plan_rows.tsv  --campaign partB_phase1 --date 2026-10-21 --commit
  python3 agent/reading_ledger.py --add agent/partB/plan2_rows.tsv --campaign partB_phase2 --date 2026-10-21 --commit
"""
import argparse, configparser, csv, sys
import psycopg2
from psycopg2.extras import execute_values
csv.field_size_limit(sys.maxsize)
ap = argparse.ArgumentParser()
ap.add_argument("--init", action="store_true")
ap.add_argument("--add")
ap.add_argument("--campaign")
ap.add_argument("--date", default=None)
ap.add_argument("--reader", default="agent")
ap.add_argument("--rowid-col", default="rowid")
ap.add_argument("--group-col", default="from_group")
ap.add_argument("--verdict-col", default="action")
ap.add_argument("--note-col", default=None)
ap.add_argument("--report", action="store_true")
ap.add_argument("--table", default="combined_align")
ap.add_argument("--commit", action="store_true")
a = ap.parse_args()
cfg = configparser.ConfigParser(); cfg.read("/etc/text-pair/global_settings.ini"); D = cfg["DATABASE"]
cn = psycopg2.connect(user=D["database_user"], password=D["database_password"], database=D["database_name"])
cur = cn.cursor(); cur.execute("SET statement_timeout = 0")

DDL = """CREATE TABLE IF NOT EXISTS rows_read (
  rowid bigint NOT NULL, group_id bigint, campaign text NOT NULL, read_date date NOT NULL DEFAULT current_date,
  reader text, verdict text, note text, PRIMARY KEY (rowid, campaign));
CREATE INDEX IF NOT EXISTS rows_read_rowid ON rows_read (rowid);"""

if a.init:
    cur.execute(DDL); cn.commit(); print("rows_read ready."); sys.exit(0)

if a.add:
    if not a.campaign: sys.exit("--campaign is required with --add")
    cur.execute("SELECT to_regclass('rows_read')")
    if cur.fetchone()[0] is None: sys.exit("rows_read does not exist: run --init first")
    rd = csv.DictReader(open(a.add, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE)
    for c in (a.rowid_col,):
        if c not in rd.fieldnames: sys.exit(f"column {c!r} not in {a.add}: {rd.fieldnames}")
    seen = {}; bad = 0
    for r in rd:
        v = (r.get(a.rowid_col) or "").strip()
        if not v.isdigit(): bad += 1; continue
        g = (r.get(a.group_col) or "").strip() if a.group_col else ""
        seen[int(v)] = (int(g) if g.isdigit() else None, (r.get(a.verdict_col) or "").strip() or None,
                        (r.get(a.note_col) or "").strip()[:500] if a.note_col else None)
    cur.execute("SELECT count(*) FROM rows_read WHERE campaign = %s", (a.campaign,)); already = cur.fetchone()[0]
    print("=" * 78); print(f"READING LEDGER -- add {a.add}" + ("" if a.commit else " (dry run)")); print("=" * 78)
    print(f"  campaign {a.campaign}   date {a.date or 'today'}   reader {a.reader}")
    print(f"  rows in file {len(seen):,}   unparseable lines {bad}   already in ledger for this campaign {already:,}")
    from collections import Counter
    print("  verdicts:", dict(Counter(x[1] for x in seen.values()).most_common(12)))
    if not a.commit: print("  Dry run. Nothing written."); sys.exit(0)
    cur.execute("SELECT count(*) FROM rows_read"); before = cur.fetchone()[0]
    rows = [(rid, g, a.campaign, a.date, a.reader, v, n) for rid, (g, v, n) in seen.items()]
    execute_values(cur, """INSERT INTO rows_read (rowid, group_id, campaign, read_date, reader, verdict, note)
                           VALUES %s ON CONFLICT (rowid, campaign) DO NOTHING""",
                   [(r[0], r[1], r[2], r[3] or None, r[4], r[5], r[6]) for r in rows],
                   template="(%s,%s,%s,COALESCE(%s::date,current_date),%s,%s,%s)", page_size=5000)
    cur.execute("SELECT count(*) FROM rows_read"); n = cur.fetchone()[0] - before
    cn.commit(); print(f"  COMMITTED: {n:,} new line(s)."); sys.exit(0)

if a.report:
    cur.execute("SELECT to_regclass('rows_read')")
    if cur.fetchone()[0] is None: sys.exit("rows_read does not exist: run --init first")
    cur.execute(f"""
      WITH g AS (SELECT group_id, count(*) n FROM {a.table} GROUP BY 1),
           r AS (SELECT DISTINCT rowid FROM rows_read)
      SELECT CASE WHEN g.n=1 THEN '1' WHEN g.n<5 THEN '2-4' WHEN g.n<10 THEN '5-9' WHEN g.n<30 THEN '10-29'
                  WHEN g.n<50 THEN '30-49' ELSE '50+' END band, min(g.n) k,
             count(*) rows_live, count(r.rowid) rows_read,
             count(DISTINCT t.group_id) groups_live,
             count(DISTINCT t.group_id) FILTER (WHERE r.rowid IS NOT NULL) groups_touched
      FROM {a.table} t JOIN g USING (group_id) LEFT JOIN r ON r.rowid = t.rowid
      GROUP BY 1 ORDER BY 2""")
    R = cur.fetchall()
    print("=" * 78); print("READING COVERAGE OF THE LIVE TABLE"); print("=" * 78)
    print(f"  {'band':>6} {'rows live':>11} {'rows read':>11} {'%':>6} {'groups live':>12} {'touched':>9}")
    T = [0, 0]
    for band, _, rl, rr, gl, gt in R:
        T[0] += rl; T[1] += rr
        print(f"  {band:>6} {rl:>11,} {rr:>11,} {100*rr/rl:>5.1f}% {gl:>12,} {gt:>9,}")
    print(f"  {'all':>6} {T[0]:>11,} {T[1]:>11,} {100*T[1]/T[0]:>5.1f}%")
    cur.execute("SELECT campaign, count(*), min(read_date), max(read_date) FROM rows_read GROUP BY 1 ORDER BY 3, 1")
    print("\n  campaigns:")
    for c, n, d0, d1 in cur.fetchall(): print(f"    {c:<32} {n:>9,}  {d0}" + (f" .. {d1}" if d1 != d0 else ""))
    sys.exit(0)
ap.print_help()
