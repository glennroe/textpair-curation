#!/usr/bin/env python3
"""
agent/partB_apply_21oct.py -- 21 Oct 2026. Applies PART B (the full-row reading of the tangled components:
232 batches, 80,670 rows, every row read) from the row-level plan compiled offline (agent/partB/compile.py):
  agent/partB/plan_rows.tsv   rowid from_group comp action dest batch why
     KEEP     stays where it is
     MOVE     group_id := dest (an existing group: a native, or a group that keeps rows)
     NEW      rows with the same comp:label become ONE new group
     NOISE    -> combined_align_editorial_noise        (setaside_rowids.py)
     EDITION  -> combined_align_translations           (Glenn 10 Oct: Latin with an edition of its author at one end)
     LATIN    -> combined_align_translations           (Glenn 7 Oct: classical v classical, translations, commentators)
Natives are NOT touched here: their REVERSE / NATIVENOISE lines (plan_natives.tsv) are phase 2, after a full read.

Dry run by default; --commit per phase. Phases, in this order:
  check      read-only: live state v plan, protected rows, provenance claims, fronts that change, expected counts
  setaside   NOISE / EDITION / LATIN via agent/setaside_rowids.py (--allow-whole --skip-protected)
  regroup    NEW then MOVE in ONE transaction; COUNT(*) asserted unchanged; split_manifest.tsv records every row
Then: rebuild_derived_tables.py --commit; carry_forward_tombstones.py --only-dead; map_martial_to_corpus.py --commit --reuse-mk.

HOLDS (left as they are, listed in agent/partB/apply_holds.tsv):
  * a row no longer live, or live in another group than the plan's from_group (it moved since the dump)
  * a MOVE whose dest group is not live
  * (only with --hold-claimed) a group with a provenance claim that would retire
CLAIMS ON RETIRING GROUPS (Glenn 22 Sep: tombstones are CARRIED FORWARD; carry_forward_tombstones.py walks
merged_clusters_manifest.tsv). On --commit, each retiring group gets a manifest line old -> the group that receives
most of its rows, but a CLAIMED group gets one only when the claim AGREES with that successor (same author key, or
the successor is unclaimed and the claim is not out_of_scope). Otherwise no line: the claim stays a tombstone on its
dead id rather than being pointed at a different passage. Listed in agent/partB/claims_successors.tsv.
  python3 -u agent/partB_apply_21oct.py --phase check
  python3 -u agent/partB_apply_21oct.py --phase setaside [--commit]
  python3 -u agent/partB_apply_21oct.py --phase regroup [--commit]
"""
import argparse, configparser, csv, os, subprocess, sys, time
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import psycopg2
from psycopg2.extras import execute_values
import corpus_source as CS, protection as PR
ap = argparse.ArgumentParser()
ap.add_argument("--phase", required=True, choices=["check", "setaside", "regroup"])
ap.add_argument("--plan", default="agent/partB/plan_rows.tsv")
ap.add_argument("--table", default="combined_align")
ap.add_argument("--prov", default="combined_align_groups_provenance")
ap.add_argument("--manifest", default="split_manifest.tsv")
ap.add_argument("--holds", default="agent/partB/apply_holds.tsv")
ap.add_argument("--fronts", default="agent/partB/front_changes.tsv")
ap.add_argument("--hold-claimed", action="store_true")
ap.add_argument("--clusters-manifest", default="merged_clusters_manifest.tsv")
ap.add_argument("--release-protected", default="", help="FILE of rowids: protected rows released by Glenn's ruling (read in Part B)")
ap.add_argument("--commit", action="store_true")
a = ap.parse_args()
t0 = time.time()
def log(*x): print(f"[{time.time()-t0:5.0f}s]", *x, flush=True)
cfg = configparser.ConfigParser(); cfg.read("/etc/text-pair/global_settings.ini"); D = cfg["DATABASE"]
cn = psycopg2.connect(user=D["database_user"], password=D["database_password"], database=D["database_name"])
cur = cn.cursor(); cur.execute("SET statement_timeout = 0")

plan = list(csv.DictReader(open(a.plan, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
for p in plan: p["rowid"] = int(p["rowid"]); p["from_group"] = int(p["from_group"])
ids = [p["rowid"] for p in plan]
log(f"plan {len(plan):,} rows: " + ", ".join(f"{k} {v:,}" for k, v in Counter(p['action'] for p in plan).most_common()))

# ---------------- live state ----------------
cur.execute(f"""SELECT rowid, group_id, source_year, source_filename, source_start_byte, target_filename, target_start_byte
                FROM {a.table} WHERE rowid = ANY(%s)""", (ids,))
live = {r[0]: r for r in cur.fetchall()}
prot = PR.Protection(cur)
cur.execute(f"SELECT c.rowid FROM {a.table} c WHERE c.rowid = ANY(%s) AND {prot.is_protected('c')}", (ids,))
protected = {r[0] for r in cur.fetchall()}
released = set()
if a.release_protected:
    import re
    released = protected & {int(x) for x in re.findall(r"^\s*(\d+)", open(a.release_protected).read(), re.M)}
    protected -= released
holds = []
ok = []
for p in plan:
    L = live.get(p["rowid"])
    if L is None: holds.append((p["rowid"], p["from_group"], p["action"], p["dest"], "not live")); continue
    if L[1] != p["from_group"]: holds.append((p["rowid"], p["from_group"], p["action"], p["dest"], f"now in group {L[1]}")); continue
    ok.append(p)
SET = {"NOISE", "EDITION", "LATIN"}
leaving = [p for p in ok if p["action"] in SET and p["rowid"] not in protected]
stay_prot = [p for p in ok if p["action"] in SET and p["rowid"] in protected]

# groups and their live sizes
groups = {p["from_group"] for p in ok} | {int(p["dest"]) for p in ok if p["action"] == "MOVE"}
cur.execute(f"SELECT group_id, count(*) FROM {a.table} WHERE group_id = ANY(%s) GROUP BY 1", (list(groups),))
size = dict(cur.fetchall())
out = Counter((p["from_group"]) for p in ok if p["action"] != "KEEP" and not (p["action"] in SET and p["rowid"] in protected))
retiring = {g for g, n in out.items() if n == size.get(g, 0)}
cur.execute(f"SELECT DISTINCT group_id FROM {a.prov} WHERE group_id = ANY(%s)", (list(groups),))
claimed = {r[0] for r in cur.fetchall()}
claimed_retiring = retiring & claimed
held_groups = claimed_retiring if a.hold_claimed else set()
moves = []
for p in ok:
    if p["action"] not in ("MOVE", "NEW"): continue
    if p["from_group"] in held_groups:
        holds.append((p["rowid"], p["from_group"], p["action"], p["dest"], "group has a provenance claim and would retire")); continue
    if p["action"] == "MOVE" and not size.get(int(p["dest"])):
        holds.append((p["rowid"], p["from_group"], p["action"], p["dest"], "dest not live")); continue
    moves.append(p)

with open(a.holds, "w", encoding="utf-8") as fh:
    fh.write("rowid\tfrom_group\taction\tdest\treason\n")
    for h in holds: fh.write("\t".join(map(str, h)) + "\n")
    for p in stay_prot: fh.write(f"{p['rowid']}\t{p['from_group']}\t{p['action']}\t\tprotected: stays live\n")

# fronts: earliest source_year then rowid, per MOVE dest, before/after
dests = {int(p["dest"]) for p in moves if p["action"] == "MOVE"}
cur.execute(f"""SELECT DISTINCT ON (group_id) group_id, source_year, rowid, left(coalesce(source_author,''),40),
                       left(coalesce(source_title,''),50)
                FROM {a.table} WHERE group_id = ANY(%s) ORDER BY group_id, source_year NULLS LAST, rowid""", (list(dests),))
fr = {r[0]: r[1:] for r in cur.fetchall()}
inc = defaultdict(list)
for p in moves:
    if p["action"] == "MOVE": inc[int(p["dest"])].append(p["rowid"])
chg = []
for d, rs in inc.items():
    best = min(((live[r][2] or 9999), r) for r in rs)
    f0 = fr.get(d)
    if f0 and best < ((f0[0] or 9999), f0[1]): chg.append((d, f0[0], f0[2], f0[3], best[0], best[1], len(rs)))
if chg:
    cur.execute(f"""SELECT rowid, left(coalesce(source_author,''),40), left(coalesce(source_title,''),50)
                    FROM {a.table} WHERE rowid = ANY(%s)""", ([c[5] for c in chg],))
    nm = {r[0]: r[1:] for r in cur.fetchall()}
with open(a.fronts, "w", encoding="utf-8") as fh:
    fh.write("dest\tyear_before\tauthor_before\ttitle_before\tyear_after\tauthor_after\ttitle_after\trows_in\n")
    for c in sorted(chg):
        fh.write(f"{c[0]}\t{c[1]}\t{c[2]}\t{c[3]}\t{c[4]}\t{nm[c[5]][0]}\t{nm[c[5]][1]}\t{c[6]}\n")

cur.execute(f"SELECT count(*) FROM {a.table}"); total = cur.fetchone()[0]
cur.execute(f"SELECT count(DISTINCT group_id) FROM {a.table}"); ngroups = cur.fetchone()[0]
print("=" * 78); print("PART B APPLY -- " + a.phase.upper() + ("" if a.commit else " (dry run)")); print("=" * 78)
print(f"  live table {total:,} rows / {ngroups:,} groups")
print(f"  plan rows live in their group {len(ok):,} of {len(plan):,}; held {len(holds):,} (see {a.holds})")
print(f"  set aside: {len(leaving):,} rows  ({', '.join(f'{k} {v:,}' for k, v in Counter(p['action'] for p in leaving).items())}); "
      f"protected and kept live {len(stay_prot):,}; protected released by ruling {len(released):,}")
print(f"  regroup: MOVE {sum(1 for p in moves if p['action']=='MOVE'):,} rows into {len(dests):,} groups; "
      f"NEW {sum(1 for p in moves if p['action']=='NEW'):,} rows into {len({p['dest'] for p in moves if p['action']=='NEW'}):,} new groups")
print(f"  groups retiring {len(retiring):,}; with a provenance claim {len(claimed_retiring):,}"
      + (" (HELD)" if claimed_retiring and a.hold_claimed else " (carried forward where the claim agrees with the successor)"))

# successors of retiring groups, and whether a claim may follow
import re as _re, unicodedata as _ud
STOP = {"les","des","jean","pierre","jacques","francois","louis","charles","claude","marie","joseph","antoine","nicolas","baptiste"}
def akey(x):
    x = "".join(c for c in _ud.normalize("NFD", x or "") if _ud.category(c) != "Mn").lower()
    return set(_re.findall(r"[a-z]{3,}", _re.sub(r"\(.*", "", x))) - STOP
recv = defaultdict(Counter)
for p in moves: recv[p["from_group"]][p["dest"] if p["action"] == "MOVE" else "NEW:" + p["dest"]] += 1
succ = {g: recv[g].most_common(1)[0][0] for g in retiring if recv.get(g)}
cur.execute("SELECT group_id, coalesce(native_status,''), coalesce(attributed_author,'') FROM " + a.prov +
            " WHERE group_id = ANY(%s)", (list(claimed_retiring | {int(d) for d in succ.values() if not str(d).startswith("NEW:")}),))
pc = defaultdict(list)
for g, st, au in cur.fetchall(): pc[g].append((st, au))
def follows(g, d):
    mine = pc.get(g)
    if not mine: return True, "no claim"
    if str(d).startswith("NEW:"): return False, "claim; successor is a new group"
    theirs = pc.get(int(d))
    oos = any(s == "out_of_scope" for s, _ in mine)
    if not theirs: return (not oos), ("successor unclaimed" if not oos else "out_of_scope claim, successor unclaimed")
    if oos != any(s == "out_of_scope" for s, _ in theirs): return False, "scope clash"
    if any((akey(x) & akey(y)) or (not x and not y) or x == y for _, x in mine for _, y in theirs): return True, "same author"
    return False, "authors differ"
SUC = {}
with open("agent/partB/claims_successors.tsv", "w", encoding="utf-8") as fh:
    fh.write("group\tclaim\tsuccessor\tfollows\twhy\n")
    for g, d in sorted(succ.items()):
        ok_, why = follows(g, d); SUC[g] = (d, ok_)
        if g in claimed_retiring:
            fh.write(f"{g}\t{'|'.join(f'{s}:{x}' for s, x in pc.get(g, []))}\t{d}\t{ok_}\t{why}\n")
nc = Counter(SUC[g][1] for g in claimed_retiring if g in SUC)
print(f"  claimed retiring groups: successor line written {nc[True]:,}; left as tombstone {nc[False] + len(claimed_retiring - set(SUC)):,} "
      f"(see agent/partB/claims_successors.tsv)")
print(f"  MOVE dests whose front document changes {len(chg):,} (see {a.fronts})")
print(f"  expected after set-aside: {total-len(leaving):,} rows")

def rowfile(name, rows):
    p = f"agent/partB/_{name}_rowids.tsv"
    with open(p, "w") as fh:
        fh.write("rowid\n"); fh.write("".join(f"{r}\n" for r in rows))
    return p
REASON = {"NOISE": "Part B 21 Oct 2026, full-row reading of the tangled components: not literary reuse (laws, decrees, "
                   "addresses voted by a body, titles, catalogues, prize questions, formulas, liturgy, convergence, fragments)",
          "EDITION": "Part B 21 Oct 2026, read: Latin passage with an edition/translation of its classical author at one end, "
                     "redundant with the PHI native (Glenn 10 Oct)",
          "LATIN": "Part B 21 Oct 2026, read: classical v classical Latin, a translation of it, or an ancient commentator (Glenn 7 Oct)"}
DEST = {"NOISE": "combined_align_editorial_noise", "EDITION": "combined_align_translations", "LATIN": "combined_align_translations"}

if a.phase == "setaside":
    bad = 0
    for k in ("NOISE", "EDITION", "LATIN"):
        rs = [p["rowid"] for p in ok if p["action"] == k]
        if not rs: continue
        print(f"\n##### {k}: {len(rs):,} rows -> {DEST[k]}", flush=True)
        cmd = ["python3", "-u", "agent/setaside_rowids.py", "--rowids-file", rowfile(k.lower(), rs), "--dest", DEST[k],
               "--allow-whole", "--skip-protected", f"agent/partB/_{k.lower()}_protected.tsv"]
        if a.release_protected: cmd += ["--release-protected", a.release_protected]
        if a.commit: cmd += ["--reason", REASON[k], "--reason-by", "Glenn (rulings), Part B readers", "--commit"]
        rc = subprocess.run(cmd).returncode
        if rc: bad += 1; print(f"  !! exit {rc}")
    print(f"\nsetaside: {bad} problem(s). {'COMMITTED' if a.commit else 'Dry run'}."); sys.exit(1 if bad else 0)

if a.phase == "regroup":
    # NEW: reuse a contributing group's id when that group gives ALL its live rows to this label (and keeps none)
    newkeys = defaultdict(list)
    for p in moves:
        if p["action"] == "NEW": newkeys[p["dest"]].append(p)
    gives = defaultdict(Counter)   # group -> Counter(destination key) over every live row still in it after set-aside
    for p in ok:
        if p["action"] in SET and p["rowid"] not in protected: continue
        gives[p["from_group"]][(p["action"], p["dest"]) if p["action"] in ("NEW", "MOVE") else ("KEEP", "")] += 1
    gone = Counter(p["from_group"] for p in ok if p["action"] in SET and p["rowid"] not in protected)
    nxt = CS.next_free_group_id(cur, a.table); newid = {}
    used = set()
    for k, ps in sorted(newkeys.items()):
        cand = sorted(g for g in {p["from_group"] for p in ps}
                      if set(gives[g]) == {("NEW", k)} and sum(gives[g].values()) + gone[g] == size.get(g, 0) and g not in used)
        if cand: newid[k] = cand[0]; used.add(cand[0])
        else: newid[k] = nxt; nxt += 1
    upd = [(p["rowid"], newid[p["dest"]] if p["action"] == "NEW" else int(p["dest"]), p["from_group"], p) for p in moves]
    upd = [u for u in upd if u[1] != u[2]]
    print(f"\n  NEW groups: {len(newid):,} ({len(used):,} reuse a contributing group's id)")
    print(f"  rows to regroup {len(upd):,}")
    if not a.commit:
        print("\n  Dry run. Nothing was changed."); sys.exit(0)
    cur.execute(f"SELECT count(*) FROM {a.table}"); before = cur.fetchone()[0]
    cur.execute("CREATE TEMP TABLE _rg (rowid bigint PRIMARY KEY, g bigint, old bigint) ON COMMIT DROP")
    execute_values(cur, "INSERT INTO _rg VALUES %s", [(u[0], u[1], u[2]) for u in upd], page_size=5000)
    cur.execute(f"UPDATE {a.table} t SET group_id = r.g FROM _rg r WHERE t.rowid = r.rowid AND t.group_id = r.old")
    n = cur.rowcount
    cur.execute(f"SELECT count(*) FROM {a.table}"); after = cur.fetchone()[0]
    if n != len(upd) or after != before:
        cn.rollback(); sys.exit(f"ROLLED BACK: updated {n:,} of {len(upd):,}; row count {before:,} -> {after:,}.")
    new = not os.path.exists(a.manifest)
    with open(a.manifest, "a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        if new: w.writerow(["source_filename", "source_start_byte", "target_filename", "target_start_byte",
                            "old_group_id", "new_group_id", "op", "note"])
        for rid, g, old, p in upd:
            L = live[rid]
            w.writerow([L[3], L[4], L[5], L[6], old, g, "move" if p["action"] == "MOVE" else "detach",
                        f"Part B 21 Oct: {p['action']} {p['dest']} (batch {p['batch']}) {p['why']}"])
    cn.commit()
    with open(a.clusters_manifest, "a", encoding="utf-8") as fh:
        nm = 0
        for g, (d, ok_) in sorted(SUC.items()):
            if not ok_ or g in held_groups: continue
            new_g = newid[d[4:]] if str(d).startswith("NEW:") else int(d)
            if new_g == g: continue
            fh.write(f"{g}\t{new_g}\t{sum(recv[g].values())}\tpartB_apply_21oct.py\t{time.strftime('%Y-%m-%d')}\t\tPart B full-row reading\n"); nm += 1
    print(f"  {a.clusters_manifest}: {nm:,} succession lines appended")
    print(f"\n  COMMITTED: {n:,} rows regrouped; row count {before:,} -> {after:,} UNCHANGED.")
    print("  NOW: python3 -u rebuild_derived_tables.py --commit, then carry_forward_tombstones.py --only-dead, then the remap.")
