#!/usr/bin/env python3
"""
rebuild_derived_tables.py
Rebuilds <table>_groups and <table>_ordered from the alignment table, with
indexes and ANALYZE. Idempotent, and safe to run at any time.

WHY THIS EXISTS SEPARATELY
--------------------------
Every mutating script in this project ends with the same sequence: mutate,
DROP the two derived tables, CREATE TABLE AS, add the primary keys, build
the indexes, ANALYZE. That sequence is the longest part of every run -- on
combined_align it is a 2.1M-row scan plus two GIN trigram builds -- and it
is the part most likely to be interrupted.

The failure that motivates this: a script whose DELETE has committed but
whose rebuild was killed leaves the alignment table correct and the derived
tables missing or half-built. Rerunning the original script does not help,
because it loads from <table>_groups, which is exactly what is missing. The
recovery is not a rerun, it is a rebuild.

So the rebuild lives here too, and can be pointed at any table.

THE TIE-BREAK WAS DOCUMENTED AS ADOPTED AND WAS NEVER HERE — 23 Aug 2026
-------------------------------------------------------------------------
`add_attributed_surname.py` (21 Aug) added and populated
`attributed_surname` for one purpose, stated in its own docstring:

    "rebuild_derived_tables.py chooses each group's representative row by
    earliest source_year, and until 21 Aug 2026 it broke ties with `rowid` --
    insertion order, which means nothing. Where a work and the polemic
    attacking it were printed in the SAME year, that coin-flip decided the
    byline, and it kept landing on the polemic... The tie-break now prefers a
    row whose `source_author` matches an attribution recorded against that
    group."

`record_native_override.py` records the same thing as settled: "THE ACTUAL
REMEDY, adopted 21 Aug: the tie-break in rebuild_derived_tables.py now
prefers a source_author matching an attribution on the group."

It was never in this file. The ORDER BY read `source_year ASC NULLS LAST,
rowid` until today, so the column was added, populated, and read by nothing —
and the three cases those docstrings name were still wrong on the page two
days later:

    10600028907   Beaumont's *Mandement ... portant condamnation d'un livre
                  qui a pour titre: Emile* (1762) bylined over Rousseau's own
                  Profession de foi — the censure credited with the words it
                  censures.
    1200064257    Bethisy's *Lettre* on the *Discours sur l'inegalite* (1755)
                  ahead of Rousseau's *Discours* (1755).
    10900028712   the *Dissertation sur les tragedies de Phedre et Hippolyte*
                  (1677) ahead of Racine's *Phedre* (1677).

This is `shipped-means-the-server-file-says-so` for the third time. A fix
described in two docstrings is not a fix; only the file is.

THE CLAUSE CANNOT PROMOTE A ROW THAT IS NOT THERE. It reorders rows WITHIN a
group. Where the attributed author has no row in the group at all — the
native sits in a different group and no run ever paired them — this changes
nothing, and the remedy is a merge or an override rather than a tie-break.
The dry run reports both counts so the difference is visible before the
rebuild rather than inferred from the page afterwards.

NOTE: `merge_from_sets.py` rebuilds the same table from its own copy of this
ORDER BY and carries the same omission. Fixing it there too is outstanding.

WHAT IT GUARANTEES
------------------
  - the representative-row rule: earliest source_year, NULLS LAST, then a row
    whose source_author carries the group's attributed surname, then (at a
    year-99 tie) a modern_phi*.tei row, then rowid.
    The surname clause is skipped with a loud message where the column does
    not exist, so this still runs against a provenance table predating
    add_attributed_surname.py
  - the standard index set, or -- if the tables already exist and carry
    indexes -- exactly the indexes that were there, captured and replayed
  - ANALYZE on all three tables, which is NOT optional: DROP + CREATE TABLE
    AS leaves the rebuilt table with no planner statistics at all, and
    without them Postgres cannot estimate pg_trgm selectivity and falls back
    to sequential scans computing similarity() over every row. That is what
    made every seed in the first overlap sweep time out.

The alignment table itself is never touched. This only rebuilds what is
derived from it, so running it when nothing is wrong is harmless.

Usage:
    python3 rebuild_derived_tables.py --table combined_align            # dry run
    python3 rebuild_derived_tables.py --table combined_align --commit
"""

import sys, configparser
import psycopg2
import representative as REP


def arg(flag, default, cast=str):
    if flag in sys.argv:
        try:
            return cast(sys.argv[sys.argv.index(flag) + 1])
        except (IndexError, ValueError):
            sys.exit(f"ERROR: {flag} needs a {cast.__name__} argument.")
    return default


TABLE = arg("--table", "combined_align")
GROUPS_TABLE = f"{TABLE}_groups"
ORDERED_TABLE = f"{TABLE}_ordered"
COMMIT = "--commit" in sys.argv

STANDARD_INDEXES = [
    f"CREATE INDEX source_author_{GROUPS_TABLE}_idx ON {GROUPS_TABLE} USING hash (source_author)",
    f"CREATE INDEX source_author_{GROUPS_TABLE}_trigrams_idx ON {GROUPS_TABLE} USING gin (source_author gin_trgm_ops)",
    f"CREATE INDEX source_passage_{GROUPS_TABLE}_trigrams_idx ON {GROUPS_TABLE} USING gin (source_passage gin_trgm_ops)",
    f"CREATE INDEX source_title_{GROUPS_TABLE}_idx ON {GROUPS_TABLE} USING hash (source_title)",
    f"CREATE INDEX source_title_{GROUPS_TABLE}_trigrams_idx ON {GROUPS_TABLE} USING gin (source_title gin_trgm_ops)",
    f"CREATE INDEX source_year_{GROUPS_TABLE}_idx ON {GROUPS_TABLE} USING btree (source_year)",
    f"CREATE INDEX count_{GROUPS_TABLE}_idx ON {GROUPS_TABLE} USING btree (count)",
    f"CREATE INDEX group_id_{GROUPS_TABLE}_idx ON {GROUPS_TABLE} USING hash (group_id)",
    f"CREATE INDEX {ORDERED_TABLE}_source_year_target_year_rowid_idx ON {ORDERED_TABLE} USING btree (source_year_target_year)",
]

cfg = configparser.ConfigParser()
cfg.read("/etc/text-pair/global_settings.ini")
conn = psycopg2.connect(user=cfg["DATABASE"]["database_user"],
                        password=cfg["DATABASE"]["database_password"],
                        database=cfg["DATABASE"]["database_name"])
cur = conn.cursor()
for s in ("SET statement_timeout = 0", "SET maintenance_work_mem = '8GB'",
          "SET work_mem = '1GB'", "SET max_parallel_maintenance_workers = 4"):
    cur.execute(s)
conn.commit()

cur.execute("SELECT to_regclass(%s)", (TABLE,))
if cur.fetchone()[0] is None:
    sys.exit(f"ERROR: {TABLE} does not exist. Nothing to rebuild from.")

cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
align_rows = cur.fetchone()[0]
cur.execute(f"SELECT COUNT(DISTINCT group_id) FROM {TABLE} WHERE group_id IS NOT NULL")
align_groups = cur.fetchone()[0]

print(f"{TABLE}: {align_rows:,} rows, {align_groups:,} distinct group_ids")

state = {}
for t in (GROUPS_TABLE, ORDERED_TABLE):
    cur.execute("SELECT to_regclass(%s)", (t,))
    exists = cur.fetchone()[0] is not None
    n = None
    if exists:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        n = cur.fetchone()[0]
    state[t] = (exists, n)
    print(f"{t}: {'present, ' + format(n, ',') + ' rows' if exists else 'MISSING'}")

# Diagnose the interrupted-rebuild case explicitly, since that is what this
# script is usually being run to fix.
g_exists, g_n = state[GROUPS_TABLE]
o_exists, o_n = state[ORDERED_TABLE]
if not g_exists or not o_exists:
    print("\n  => A derived table is MISSING. This is the signature of a rebuild")
    print("     interrupted after its DELETE or UPDATE committed. The alignment")
    print("     table above is authoritative; rebuilding restores consistency.")
elif g_n != align_groups or o_n != align_rows:
    print(f"\n  => STALE. {GROUPS_TABLE} holds {g_n:,} rows against {align_groups:,}")
    print(f"     distinct group_ids, and {ORDERED_TABLE} holds {o_n:,} against")
    print(f"     {align_rows:,} alignment rows. Rebuilding will reconcile them.")
else:
    print("\n  => Consistent with the alignment table. A rebuild is harmless but")
    print("     is not needed.")

# ---------------------------------------------------------------------------
# THE SURNAME TIE-BREAK. See the docstring: this was documented as adopted on
# 21 Aug and was not in the file.
#
# One row per group is guaranteed by aggregating the provenance table rather
# than joining it directly. Nothing enforces one provenance row per group_id,
# and a duplicate would multiply the rows DISTINCT ON is choosing between --
# which would not change the winner, but would make the plan quietly quadratic
# on any group that had one.
#
# position(... in ...) rather than ILIKE: an authority id such as
# `author_03346` is a legitimate attributed_surname, and `_` is a single-
# character wildcard in LIKE. A literal substring test has no such trapdoor.
# ---------------------------------------------------------------------------
PROV_TABLE = f"{GROUPS_TABLE}_provenance"
cur.execute("SELECT to_regclass(%s)", (PROV_TABLE,))
HAVE_PROV = cur.fetchone()[0] is not None
HAVE_SURNAME = False
if HAVE_PROV:
    cur.execute("""SELECT 1 FROM information_schema.columns
                    WHERE table_name = %s AND column_name = 'attributed_surname'""",
                (PROV_TABLE.split(".")[-1],))
    HAVE_SURNAME = cur.fetchone() is not None

# THE CLAUSE NOW COMES FROM representative.py, 24 Aug 2026.
#
# It was defined here and nowhere else, which is why merge_from_sets.py and
# campaign_find_natives.py went on choosing representatives by a rule two
# steps behind — and why the campaign classified two Rousseau/Rossant year
# ties as DATE DEFEATS IT, nearly earning two permanent overrides for a fault
# a tie-break resolves. One definition, three importers.
if HAVE_SURNAME:
    SURN_JOIN = REP.join_sql(PROV_TABLE)
    SURN_ORDER = REP.order_sql()
else:
    SURN_JOIN = SURN_ORDER = ""
    print(f"""
  *** NO attributed_surname ON {PROV_TABLE} ***
      The representative tie-break falls back to rowid, which is insertion
      order and means nothing. Where a work and the polemic attacking it were
      printed in the same year, the byline is then a coin flip and it keeps
      landing on the polemic. Run add_attributed_surname.py --commit first.""")

# WHAT THE CLAUSE WOULD ACTUALLY CHANGE, reported BEFORE the rebuild. A count
# printed after the fact is not a check; and the clause reorders rows WITHIN a
# group, so a group whose attributed author has no row in it is untouched and
# should not be expected to move.
if HAVE_SURNAME:
    cur.execute(f"""
        WITH p AS (SELECT group_id, MIN(attributed_surname) AS surn
                     FROM {PROV_TABLE}
                    WHERE attributed_surname IS NOT NULL
                      AND attributed_surname <> ''
                    GROUP BY group_id),
             hit AS (
               SELECT p.group_id,
                      BOOL_OR(c.source_author IS NOT NULL
                              AND position(lower(p.surn)
                                           in lower(c.source_author)) > 0) AS present
                 FROM p JOIN {TABLE} c ON c.group_id = p.group_id
                GROUP BY p.group_id)
        SELECT COUNT(*), COUNT(*) FILTER (WHERE present) FROM hit""")
    n_attr, n_present = cur.fetchone()
    print(f"""
  SURNAME TIE-BREAK
      groups carrying an attributed_surname          {n_attr:>8,}
      ... of which some row's source_author matches  {n_present:>8,}   <- can move
      ... of which NO row carries that author        {n_attr - n_present:>8,}   <- cannot

  The second number is the reach of this rebuild. For the third, the
  attributed author has no row in the group at all: the native sits in
  another group and no run ever paired them, so no ordering rule can front
  it. Those need a merge or an override, not a tie-break.""")

# THE YEAR-99 TIE, 29 Sep 2026 (Glenn, ruling 2 of the pilot decisions).
# A bilingual edition's Latin band is dated 99 like the PHI text itself, so
# at a year-99 tie the edition could front the group on rowid alone and the
# page named an edition where the work belonged (Horace, Sermones I.1.68,
# 1500179712, fronted by Batteux's 1750 bilingual Poesies). Measured before
# the change: 13,577 groups front at 99, 12,846 of them hold a PHI row, and
# in 376 the PHI row lost the tie. At a year-99 tie a modern_phi*.tei row now
# comes first. It sorts false-first, so it touches nothing but year-99 ties,
# and it follows the surname clause, which never separates two rows of one
# author. merge_from_sets.py carries its own copy of this ORDER BY (merges
# are frozen; fix it there before they reopen).
PHI_TIE = ("(c.source_year = 99 AND c.source_filename NOT LIKE '%%modern_phi%%') "
           "ASC NULLS LAST").replace("%%", "%")
print("\n  year-99 tie-break: a modern_phi*.tei row fronts a year-99 tie "
      "(29 Sep 2026)")

saved = []
for t in (GROUPS_TABLE, ORDERED_TABLE):
    if not state[t][0]:
        continue
    cur.execute("""
        SELECT i.indexdef FROM pg_indexes i
        JOIN pg_class c ON c.relname = i.indexname
        JOIN pg_index x ON x.indexrelid = c.oid
        WHERE i.tablename = %s AND NOT x.indisprimary
    """, (t,))
    saved.extend(r[0] for r in cur.fetchall())
print(f"\n{len(saved)} existing index(es) captured for replay"
      + ("" if saved else " -- will fall back to the standard set"))

if not COMMIT:
    print("\nDry run. Rerun with --commit to rebuild.")
    cur.close(); conn.close()
    sys.exit(0)

print(f"\nRebuilding {GROUPS_TABLE} ...", flush=True)
cur.execute(f"DROP TABLE IF EXISTS {GROUPS_TABLE} CASCADE")
cur.execute(f"""
    CREATE TABLE {GROUPS_TABLE} AS
    SELECT m.*, counts.cnt AS count
    FROM (
        SELECT DISTINCT ON (c.group_id) c.*
        FROM {TABLE} c{SURN_JOIN}
        WHERE c.group_id IS NOT NULL
        ORDER BY c.group_id, c.source_year ASC NULLS LAST{SURN_ORDER},
                 {PHI_TIE}, c.rowid
    ) m
    JOIN (
        SELECT group_id, COUNT(*) AS cnt FROM {TABLE}
        WHERE group_id IS NOT NULL GROUP BY group_id
    ) counts ON m.group_id = counts.group_id
""")
cur.execute(f"ALTER TABLE {GROUPS_TABLE} DROP COLUMN rowid")
cur.execute(f"ALTER TABLE {GROUPS_TABLE} ADD PRIMARY KEY (group_id)")
conn.commit()
cur.execute(f"SELECT COUNT(*) FROM {GROUPS_TABLE}")
print(f"  {cur.fetchone()[0]:,} groups.", flush=True)

print(f"\nRebuilding {ORDERED_TABLE} ...", flush=True)
cur.execute(f"DROP TABLE IF EXISTS {ORDERED_TABLE} CASCADE")
cur.execute(f"""
    CREATE TABLE {ORDERED_TABLE} AS
    SELECT ROW_NUMBER() OVER (ORDER BY source_year, target_year, source_start_byte)
               AS rowid_ordered,
           rowid AS source_year_target_year
    FROM {TABLE}
""")
cur.execute(f"ALTER TABLE {ORDERED_TABLE} ADD PRIMARY KEY (rowid_ordered)")
conn.commit()
cur.execute(f"SELECT COUNT(*) FROM {ORDERED_TABLE}")
print(f"  {cur.fetchone()[0]:,} rows.", flush=True)

todo = saved or STANDARD_INDEXES
print(f"\nBuilding {len(todo)} index(es) ...", flush=True)
for idx in todo:
    try:
        cur.execute(idx)
        conn.commit()
        print(f"  OK: {idx.split('INDEX ')[1].split(' ON')[0]}", flush=True)
    except psycopg2.Error as e:
        conn.rollback()
        print(f"  FAILED: {str(e).strip().splitlines()[0]}", flush=True)

print("\nANALYZE ...", flush=True)
for t in (GROUPS_TABLE, TABLE, ORDERED_TABLE):
    cur.execute(f"ANALYZE {t}")
    conn.commit()
    print(f"  OK: {t}", flush=True)

cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
r = cur.fetchone()[0]
cur.execute(f"SELECT COUNT(*) FROM {GROUPS_TABLE}")
g = cur.fetchone()[0]
cur.execute(f"SELECT COUNT(*) FROM {ORDERED_TABLE}")
o = cur.fetchone()[0]
print(f"\nVERIFICATION\n  {TABLE:<28} {r:>12,} rows")
print(f"  {GROUPS_TABLE:<28} {g:>12,} groups")
print(f"  {ORDERED_TABLE:<28} {o:>12,} rows")
print(f"  ordered matches align: {'OK' if o == r else '*** MISMATCH ***'}")

cur.close(); conn.close()
print("\nDone.")
