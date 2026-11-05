#!/usr/bin/env python3
"""
carry_forward_tombstones.py
Follow a provenance claim whose group was merged away to whatever is LIVE now,
and record that in `resolved_by`. Dry run unless --commit.

GLENN'S RULING, 22 September 2026
---------------------------------
Tombstones are CARRIED FORWARD. And, in his words on the same day:

    "for native_unaligned native_absent and native_unsearched — carrying
     forward does not mean resolving"

**SO THIS SCRIPT NEVER TOUCHES `native_status`.** It changes where a claim can
be FOUND, never what the claim ASSERTS. A carried-forward `native_absent` row
ends up saying: the witnesses now live under canonical X, and the source is
still not in the corpus. Rewriting its status to `resolved` would destroy the
only thing it was ever there to say.

POINTING, NOT MOVING — AND WHY
-------------------------------
Carry-forward is implemented as setting `resolved_by`, not as rewriting
`group_id` onto the canonical. Several claims may legitimately point at one
canonical; only one row can SIT on it. Moving would manufacture collisions
that pointing does not create, and a collision here is a decision about which
claim a group asserts, which is a reading rather than an update.

THE TWO POPULATIONS, AND WHY THEY ARE ONE JOB
----------------------------------------------
    DEAD GROUP      the claim's own group_id no longer exists   (823 on 22 Sep)
    STALE POINTER   `resolved_by` was live when written and has since been
                    merged away by a later round

The second is not a backlog, it is the MECHANISM: every campaign that merges a
canonical stales every pointer at it. A tool that handled only today's 823
would need rewriting after band B. Both are the same walk.

THE WALK
---------
`merged_clusters_manifest.tsv` is append-only: old_group_id, new_group_id,
then five descriptive columns. A chain arises when a canonical is itself
retired later — A -> B, then B -> C. The walk follows until it reaches a live
group, and it carries a depth cap and a cycle guard because an append-only
file written by many rounds is not guaranteed acyclic and a loop would hang
silently rather than fail loudly.

FATES, ALL COUNTED
-------------------
    CARRIED         reached a live successor
    NO SUCCESSOR    dead, and absent from the manifest entirely. Its rows were
                    SET ASIDE rather than merged, so they kept their group_id
                    and only the proposer ever saw a group. Nothing to point at
    DEAD END        the chain terminates on a dead id that has no further
                    manifest entry
    CYCLE           the walk revisited an id. Reported, never followed
    REFUSED         `out_of_scope` — carrying it forward would assert a descent
                    for a source that is out of scope by ruling
    ALREADY         `resolved_by` is set and still live. Left alone

They must sum to the rows considered or the script refuses to commit.

USAGE
    python3 carry_forward_tombstones.py
    python3 carry_forward_tombstones.py --report carry_22sep.txt --commit
    python3 carry_forward_tombstones.py --only-stale        # just the pointers
"""

import argparse
import configparser
import sys
from collections import Counter

import psycopg2
from psycopg2.extras import execute_values

ap = argparse.ArgumentParser()
ap.add_argument("--manifest", default="merged_clusters_manifest.tsv")
ap.add_argument("--prov", default="combined_align_groups_provenance")
ap.add_argument("--groups", default="combined_align_groups")
ap.add_argument("--column", default="resolved_by")
ap.add_argument("--max-depth", type=int, default=25,
                help="chain length beyond which the walk gives up and reports "
                     "rather than looping.")
ap.add_argument("--only-dead", action="store_true",
                help="only claims whose OWN group is dead.")
ap.add_argument("--only-stale", action="store_true",
                help="only claims whose resolved_by has since died.")
ap.add_argument("--never", default="out_of_scope",
                help="comma-separated native_status values that are REFUSED. "
                     "Emptying this is a ruling, not a convenience.")
ap.add_argument("--show", type=int, default=15, help="0 = all.")
ap.add_argument("--report", default="")
ap.add_argument("--commit", action="store_true")
args = ap.parse_args()

if args.only_dead and args.only_stale:
    sys.exit("\n  REFUSING: --only-dead and --only-stale exclude each other.\n")

NEVER = {s.strip() for s in args.never.split(",") if s.strip()}
OUT = []


def p(*a):
    line = " ".join(str(x) for x in a)
    print(line)
    OUT.append(line)


# --------------------------------------------------------- the manifest ----
# Split on tab and take the first two fields only. old_author and old_title are
# free text written raw by merge_from_sets.py, so a tab inside a title would
# shift every later column — it cannot shift the first two.
succ = {}
n_man = n_man_bad = 0
try:
    fh = open(args.manifest, encoding="utf-8")
except FileNotFoundError:
    sys.exit(f"\n  REFUSING: {args.manifest} not found. Without it there is no "
             f"succession to follow, and a run that carried nothing forward "
             f"would report success.\n")
for i, line in enumerate(fh):
    if i == 0 and line.startswith("old_group_id"):
        continue
    f = line.rstrip("\n").split("\t")
    if len(f) < 2 or not f[0].strip().isdigit() or not f[1].strip().isdigit():
        n_man_bad += 1
        continue
    old, new = int(f[0]), int(f[1])
    n_man += 1
    # An id is retired ONCE. If the file disagrees with itself, the LAST entry
    # wins, because the file is chronological and a later round is later truth.
    succ[old] = new
fh.close()

# ------------------------------------------------------------- the corpus --
cfg = configparser.ConfigParser()
cfg.read("/etc/text-pair/global_settings.ini")
conn = psycopg2.connect(user=cfg["DATABASE"]["database_user"],
                        password=cfg["DATABASE"]["database_password"],
                        database=cfg["DATABASE"]["database_name"])
cur = conn.cursor()

cur.execute("""SELECT data_type FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s""",
            (args.prov, args.column))
_c = cur.fetchone()
if not _c:
    sys.exit(f"\n  REFUSING: {args.prov}.{args.column} does not exist. Run "
             f"backfill_resolved_by.py first — this script MAINTAINS that "
             f"column and does not create it.\n")
if _c[0] != "bigint":
    sys.exit(f"\n  REFUSING: {args.prov}.{args.column} is {_c[0]!r}, not "
             f"bigint. Group ids exceed int4.\n")

cur.execute(f"SELECT group_id FROM {args.groups}")
live = {g for (g,) in cur}

cur.execute(f"SELECT group_id, native_status, {args.column} FROM {args.prov}")
prov = cur.fetchall()


def walk(gid):
    """Follow gid through the manifest to a live group.
    Returns (verdict, value) where verdict is one of
    CARRIED / NO_SUCCESSOR / DEAD_END / CYCLE."""
    if gid not in succ:
        return "NO_SUCCESSOR", None
    seen = {gid}
    cur_id = gid
    for _ in range(args.max_depth):
        nxt = succ.get(cur_id)
        if nxt is None:
            return "DEAD_END", cur_id
        if nxt in seen:
            return "CYCLE", nxt
        seen.add(nxt)
        if nxt in live:
            return "CARRIED", nxt
        cur_id = nxt
    return "DEAD_END", cur_id


carried, refused, already, problems = [], [], [], []
considered = 0
skip_notinscope = 0
fate_n = Counter()

for gid, status, rb in prov:
    gid_dead = gid not in live
    rb_stale = rb is not None and rb not in live
    if not (gid_dead or rb_stale):
        skip_notinscope += 1
        continue
    if args.only_dead and not gid_dead:
        skip_notinscope += 1
        continue
    if args.only_stale and not rb_stale:
        skip_notinscope += 1
        continue
    considered += 1

    if status in NEVER:
        refused.append((gid, status, rb))
        fate_n["REFUSED"] += 1
        continue
    if rb is not None and rb in live:
        already.append((gid, status, rb))
        fate_n["ALREADY"] += 1
        continue

    # Walk from whichever id is the better starting point: a stale pointer is
    # already one step along the chain, so start there rather than from the
    # claim's own group, which may be several rounds older.
    start = rb if rb_stale else gid
    verdict, value = walk(start)
    fate_n[verdict] += 1
    if verdict == "CARRIED":
        carried.append((gid, status, rb, value))
    else:
        problems.append((gid, status, rb, verdict, value))

seen_total = (len(carried) + len(refused) + len(already) + len(problems))

p("=" * 78)
p("CARRYING PROVENANCE CLAIMS FORWARD — POINTING, NEVER RESOLVING")
p("=" * 78)
p(f"""
  manifest                {args.manifest}
    succession(s) read    {n_man:,}
    unparseable line(s)   {n_man_bad:,}

  provenance              {args.prov}
    row(s) total          {len(prov):,}
    out of scope for this pass          {skip_notinscope:,}
    CONSIDERED            {considered:,}

  live group(s)           {len(live):,}
  refused status(es)      {', '.join(sorted(NEVER)) or '(none)'}

  FATES
    CARRIED               {fate_n['CARRIED']:,}
    ALREADY live          {fate_n['ALREADY']:,}
    REFUSED (by status)   {fate_n['REFUSED']:,}
    NO SUCCESSOR          {fate_n['NO_SUCCESSOR']:,}   set aside, never merged
    DEAD END              {fate_n['DEAD_END']:,}   chain ends on a dead id
    CYCLE                 {fate_n['CYCLE']:,}   reported, never followed
    ---------------------------------------
    reconciles            {seen_total:,} of {considered:,}

  native_status is NOT written by this script. A carried-forward claim keeps
  what it asserts and gains only a pointer to where its subject now lives.
""")

if seen_total != considered:
    cur.close()
    conn.close()
    sys.exit("\n  REFUSING: the fates do not reconcile.\n  Standing rule 4.\n")

by_status = Counter(s for _, s, _, _ in carried)
if by_status:
    p("-" * 78)
    p("  CARRIED, by status — none of these statuses changes")
    for s, n in by_status.most_common():
        p(f"      {str(s):<20} {n:>6,}")


def show(label, items, fmt):
    if not items:
        return
    p("-" * 78)
    n = len(items) if args.show == 0 else min(args.show, len(items))
    p(f"  {label} — showing {n:,} of {len(items):,}")
    for it in items[:n]:
        p("      " + fmt(it))


show("PROBLEMS — not carried", problems,
     lambda t: f"{t[0]:>12}  [{t[1]}]  rb={t[2]}  {t[3]}"
               + (f" at {t[4]}" if t[4] is not None else ""))
show("REFUSED by status", refused,
     lambda t: f"{t[0]:>12}  [{t[1]}]  rb={t[2]}")
show("CARRIED", carried,
     lambda t: f"{t[0]:>12}  [{t[1]}]  rb {t[2]} -> {t[3]}")

if not args.commit:
    p("""
  DRY RUN. Nothing was written.

  Re-run with --commit. PROBLEMS and REFUSED are never written: a chain that
  dead-ends or cycles is a question about descent, and a refused status is a
  ruling.
""")
else:
    cur.execute(f"SELECT count(*) FROM {args.prov} "
                f"WHERE {args.column} IS NOT NULL")
    before_set = cur.fetchone()[0]
    if carried:
        execute_values(
            cur,
            f"UPDATE {args.prov} AS t SET {args.column} = v.rb "
            f"FROM (VALUES %s) AS v(gid, rb) WHERE t.group_id = v.gid",
            [(g, new) for g, _, _, new in carried])
    conn.commit()
    cur.execute(f"SELECT count(*) FROM {args.prov} "
                f"WHERE {args.column} IS NOT NULL")
    now_set = cur.fetchone()[0]

    # COUNT THE COLUMN, NOT THE DRIVER. cur.rowcount after execute_values
    # reports only the last batch — it pages at 100. Measured 22 Sep: a
    # 6,725-row write returned 25.
    #
    # The delta is NOT the carried count here, because a STALE POINTER row
    # already had a non-null value and is being overwritten rather than filled.
    # So the honest check is the newly-non-null count plus the overwrites.
    newly_null_filled = sum(1 for _, _, rb, _ in carried if rb is None)
    expected_delta = newly_null_filled
    delta = now_set - before_set
    p(f"""
  COMMITTED.
      {args.column} set before   {before_set:,}
      {args.column} set after    {now_set:,}
      delta                   {delta:,}   (expected {expected_delta:,})
      carried in total        {len(carried):,}
        of which filled a NULL   {newly_null_filled:,}
        of which REPOINTED a stale value   {len(carried) - newly_null_filled:,}

  The delta counts only rows that went from NULL to a value. A repointed row
  was already non-null, so it cannot move the count — which is why the delta
  is checked against the NULL-filling subset and not against the total.
""")
    if delta != expected_delta:
        p("  *** MISMATCH: delta != expected. STOP AND READ. ***")

if args.report:
    with open(args.report, "w", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")
    print(f"\nwrote {args.report}")

cur.close()
conn.close()
