#!/usr/bin/env python3
"""
fix_document_year.py
Correct `source_year` / `target_year` for one document, BY BYTE BAND.
Dry run by default; --commit required. Nothing is ever deleted.

WHY BANDS RATHER THAN A DOCUMENT-WIDE YEAR
-------------------------------------------
28 Aug 2026. `bpt6k4235443s.tei` carries 1770 on all 312 of its rows. The BnF
record dates it [1770-1784]: the ingest took the FIRST year of a bracketed
range and applied it to a volume that binds several works together. Taking
the LAST year instead repeats the fault with the sign flipped -- Fabre's own
Essais of 1770 would then be dated after two decades of work it genuinely
precedes -- and taking a midpoint asserts a publication year true of nothing.

`probe_document_layout.py` showed where the pieces divide: bytes 2,988-314,263
align backward to Mauriceau 1694, Boerhaave 1743, Cartheuser 1755, Bordeu
1764-67, and touch no magnetism at all; from 325,723 to the end every partner
belongs to the 1779-85 magnetism controversy. So the band is the unit, and
each band gets the year that is TRUE of it rather than the year that makes
the page sort correctly.

Gallica books in this corpus carry no structural tagging (Glenn, 28 Aug), so
a byte offset is the only handle there is. The boundary here was CHOSEN at
320,000 within the measured gap 314,263..325,723, not found in the markup,
and that choice is stamped into the manifest rather than left implicit.

BOTH SIDES, SEVEN TABLES
------------------------
A document's year is wrong wherever the document appears. Rows where it is
the SOURCE are banded by `source_start_byte` and update `source_year`; rows
where it is the TARGET are banded by `target_start_byte` and update
`target_year`. Every registered set-aside table is included through
corpus_source -- a row moved to noise carries the same wrong year, and
leaving it behind would mean a later reversal restores bad data.

`combined_align_groups` is DERIVED and is not touched here. Run
`rebuild_derived_tables.py --commit` afterwards, in the standing order.

PROTECTED ROWS ARE REPORTED, NOT REFUSED
-----------------------------------------
`setaside_groups.py` refuses on protected rows because MOVING an affirmed row
withdraws it from view. Correcting the year of an affirmed row does the
opposite: the affirmation stands and the metadata beneath it stops lying. So
the count is printed prominently in both modes and the run proceeds. If that
is the wrong call for some future document, refuse in the caller rather than
weakening this note.

RECONCILIATION IS ENFORCED, NOT PRINTED
----------------------------------------
Standing rule 4: a no-op reports success. Under --commit this recomputes the
matching count immediately before each UPDATE and compares it against the
UPDATE's own rowcount, in the same transaction. Any disagreement rolls the
whole run back and names the band. A dry run's prediction is not trusted to
survive to commit time; it is recomputed.

REVERSAL
--------
Every change is appended to a manifest (table, side, filename, band, old year,
new year, rows). Reversal is mechanical: run again with the bands' years
swapped. Rows whose year already equals the band's target are counted and
skipped, so a second run is a no-op rather than a double application.

Usage:
    python3 fix_document_year.py --filename '%bpt6k4235443s%' \\
        --band 0:320000:1770 --band 320000:999999999:1784

    python3 fix_document_year.py --filename '%bpt6k4235443s%' \\
        --band 0:320000:1770 --band 320000:999999999:1784 --commit
"""

import argparse, configparser, csv, os, sys, time
import psycopg2
import corpus_source as CS

ap = argparse.ArgumentParser()
ap.add_argument("--filename", required=True,
                help="source/target filename. ILIKE if it contains '%%', "
                     "otherwise exact equality. Must resolve to ONE document.")
ap.add_argument("--band", action="append", default=[], metavar="LO:HI:YEAR",
                help="half-open byte range [LO,HI) gets YEAR. Repeatable. "
                     "Bands may not overlap; rows outside every band are "
                     "left alone and REPORTED, never silently skipped.")
ap.add_argument("--manifest", default="document_year_changes.tsv")
ap.add_argument("--note", default="",
                help="why this run was made, stamped into the manifest.")
ap.add_argument("--protected", default="protected_rows")
ap.add_argument("--commit", action="store_true")
CS.add_arguments(ap)
args = ap.parse_args()

if not args.band:
    sys.exit("REFUSING: no --band given. A document-wide year is the fault "
             "this script exists to avoid; state the bands explicitly.")

bands = []
for b in args.band:
    try:
        lo, hi, yr = b.split(":")
        lo, hi, yr = int(lo), int(hi), int(yr)
    except ValueError:
        sys.exit(f"REFUSING: --band {b!r} is not LO:HI:YEAR with integers.")
    if hi <= lo:
        sys.exit(f"REFUSING: --band {b!r} has HI <= LO.")
    bands.append((lo, hi, yr))
bands.sort()
for (l1, h1, _), (l2, h2, _) in zip(bands, bands[1:]):
    if l2 < h1:
        sys.exit(f"REFUSING: bands [{l1},{h1}) and [{l2},{h2}) overlap. "
                 "An overlapping band makes the applied year depend on "
                 "evaluation order, which is not a decision anyone made.")

cfg = configparser.ConfigParser()
cfg.read("/etc/text-pair/global_settings.ini")
conn = psycopg2.connect(user=cfg["DATABASE"]["database_user"],
                        password=cfg["DATABASE"]["database_password"],
                        database=cfg["DATABASE"]["database_name"])
cur = conn.cursor()
cur.execute("SET statement_timeout = 0")

src = CS.CorpusSource(cur, args)
print(src.describe())
print()
MODE = "COMMIT" if args.commit else "DRY RUN"
print(f"*** {MODE} ***")
print()

OP = "ILIKE" if "%" in args.filename else "="

# ---- the document must be exactly one ------------------------------------
names = set()
for t in src.tables:
    for side in ("source", "target"):
        cur.execute(f"SELECT DISTINCT {side}_filename FROM {t} "
                    f"WHERE {side}_filename {OP} %s", (args.filename,))
        names.update(r[0] for r in cur.fetchall())
if not names:
    sys.exit(f"No rows with a filename {OP} {args.filename!r} in "
             + " + ".join(src.tables) + ".")
if len(names) > 1:
    print("REFUSING: the pattern matches more than one document —")
    for n in sorted(names):
        print(f"    {n}")
    sys.exit("\nNarrow --filename to exactly one. A band cut for one "
             "document is not a fact about another.")
FN = names.pop()
print(f"DOCUMENT  {FN}")
print(f"BANDS     " + ", ".join(f"[{l:,},{h:,}) -> {y}" for l, h, y in bands))
print(f"          boundary CHOSEN, not found in markup — gallica_mono has no "
      "structural tagging")
print()

# ---- protected rows, reported ---------------------------------------------
cur.execute("SELECT to_regclass(%s)", (args.protected,))
if cur.fetchone()[0] is not None:
    cur.execute(f"SELECT COUNT(*) FROM {args.protected} "
                f"WHERE source_filename = %s OR target_filename = %s",
                (FN, FN))
    np = cur.fetchone()[0]
    if np:
        print(f"PROTECTED ROWS: {np:,} affirmed row(s) touch this document. "
              "They are NOT")
        print("  refused — correcting a year does not withdraw an "
              "affirmation, it stops")
        print("  the metadata under it from lying. Read this line before "
              "committing.")
        print()

# ---- plan ------------------------------------------------------------------
plan = []          # (table, side, lo, hi, year, n_to_change, n_already)
outside = []       # (table, side, n)
for t in src.tables:
    for side in ("source", "target"):
        byte = f"{side}_start_byte"
        yc = f"{side}_year"
        cur.execute(f"SELECT COUNT(*) FROM {t} WHERE {side}_filename {OP} %s",
                    (args.filename,))
        total = cur.fetchone()[0]
        if not total:
            continue
        cur.execute(f"SELECT {yc}, COUNT(*) FROM {t} "
                    f"WHERE {side}_filename {OP} %s GROUP BY 1 ORDER BY 2 DESC",
                    (args.filename,))
        dist = cur.fetchall()
        print(f"{t}.{side}: {total:,} row(s); current {yc} = "
              + ", ".join(f"{y} ({c:,})" for y, c in dist))
        covered = 0
        for lo, hi, yr in bands:
            cur.execute(
                f"SELECT COUNT(*) FILTER (WHERE {yc} IS DISTINCT FROM %s), "
                f"       COUNT(*) FROM {t} "
                f"WHERE {side}_filename {OP} %s "
                f"  AND {byte} >= %s AND {byte} < %s",
                (yr, args.filename, lo, hi))
            n_change, n_band = cur.fetchone()
            covered += n_band
            if n_band:
                plan.append((t, side, lo, hi, yr, n_change, n_band - n_change))
                print(f"    [{lo:,},{hi:,}) -> {yr}: {n_band:,} row(s), "
                      f"{n_change:,} to change, {n_band - n_change:,} already "
                      f"{yr}")
        if covered != total:
            outside.append((t, side, total - covered))
            print(f"    *** {total - covered:,} row(s) fall OUTSIDE every "
                  "band and will be left unchanged ***")
print()

to_change = sum(p[5] for p in plan)
already = sum(p[6] for p in plan)
print(f"TOTAL: {to_change:,} row(s) to change, {already:,} already correct, "
      f"{sum(n for _t, _s, n in outside):,} outside all bands.")
if outside:
    print("  Rows outside every band are not an error — they are simply not "
          "covered by")
    print("  a decision. Widen the bands if they should be.")
print()

if not args.commit:
    print("Dry run. Nothing was written. Re-run with --commit.")
    print()
    print("Then, in this order:")
    print("    python3 rebuild_derived_tables.py --commit")
    print("    python3 build_top_passages_page.py")
    print("    hard reload the page")
    conn.close()
    sys.exit(0)

if not to_change:
    print("Nothing to change. No transaction opened.")
    conn.close()
    sys.exit(0)

# ---- commit, with the count recomputed inside the transaction -------------
stamp = time.strftime("%Y-%m-%d %H:%M:%S")
rows_written = []
try:
    for t, side, lo, hi, yr, _pred, _ok in plan:
        byte = f"{side}_start_byte"
        yc = f"{side}_year"
        cur.execute(
            f"SELECT COUNT(*) FROM {t} WHERE {side}_filename {OP} %s "
            f"  AND {byte} >= %s AND {byte} < %s "
            f"  AND {yc} IS DISTINCT FROM %s",
            (args.filename, lo, hi, yr))
        expect = cur.fetchone()[0]
        cur.execute(
            f"SELECT DISTINCT {yc} FROM {t} WHERE {side}_filename {OP} %s "
            f"  AND {byte} >= %s AND {byte} < %s "
            f"  AND {yc} IS DISTINCT FROM %s",
            (args.filename, lo, hi, yr))
        olds = ",".join(str(r[0]) for r in cur.fetchall())
        cur.execute(
            f"UPDATE {t} SET {yc} = %s WHERE {side}_filename {OP} %s "
            f"  AND {byte} >= %s AND {byte} < %s "
            f"  AND {yc} IS DISTINCT FROM %s",
            (yr, args.filename, lo, hi, yr))
        got = cur.rowcount
        if got != expect:
            raise RuntimeError(
                f"RECONCILIATION FAILED on {t}.{side} [{lo},{hi}): counted "
                f"{expect} row(s) to change, UPDATE reported {got}. "
                "Rolling the entire run back.")
        print(f"  {t}.{side} [{lo:,},{hi:,}) -> {yr}: {got:,} row(s) "
              f"(was {olds or '—'})")
        rows_written.append((stamp, t, side, FN, lo, hi, olds, yr, got,
                             args.note))
    conn.commit()
except Exception as e:
    conn.rollback()
    sys.exit(f"\nROLLED BACK. Nothing was written.\n{e}")

new = not os.path.exists(args.manifest)
with open(args.manifest, "a", newline="") as fh:
    w = csv.writer(fh, delimiter="\t")
    if new:
        w.writerow(["recorded_at", "table", "side", "filename", "band_lo",
                    "band_hi", "old_years", "new_year", "rows", "note"])
    w.writerows(rows_written)

print()
print(f"COMMITTED. {sum(r[8] for r in rows_written):,} row(s) changed; "
      f"appended to {args.manifest}.")
print("To reverse, run again with the bands' years swapped.")
print()
print("NOW, in this order — a stale page file cost half an hour on the 27th:")
print("    python3 rebuild_derived_tables.py --commit")
print("    python3 build_top_passages_page.py")
print("    hard reload the page")
print()
print("Titles were NOT touched: the tail rows still carry the composite "
      "catalogue string.")
print("Fix those with record_attribution.py --update if wanted.")
conn.close()
