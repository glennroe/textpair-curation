#!/usr/bin/env python3
"""
check_native_candidate.py
Does a located native edition actually contain the passage? STRICTLY READ-ONLY.

WHY THIS EXISTS
---------------
`native_status` distinguishes two states that are easy to conflate:

    native_other_verse   a native edition of the WORK is located; this PASSAGE
                         is not yet matched to it
    merged               the native was found FOR THIS PASSAGE; the override
                         is retired

The difference is a targeted anchor search, and skipping it is how Malherbe
`300013186` came to carry `native_damaged` for two days. On 16 Aug the native
of the work was located -- group 10600001858, four rows, *Les poesies de Mr de
Malherbe*, 1628, undamaged -- and the damage turned out to be in the search
rather than the text. But "the work is present" is not "this line is present",
and promoting the row straight to `merged` would assert the second on evidence
for the first. That is the original error inverted: a status claiming more than
was checked.

So this compares the passage against every row of the candidate group and
prints the containment scores, and the status follows from what it finds:

    a high score          the passage IS in the native  -> merge, then `merged`
    no row above ~0.4     the work is there, the line is not (or is damaged
                          beyond whole-passage similarity) -> native_other_verse

CORRECTION, 28 Aug 2026 -- READ THIS BEFORE THE THRESHOLD ABOVE.
The "~0.4" floor was calibrated on Malherbe and on Latin, and it does not
transfer to short French verse, where the containment FLOOR between unrelated
passages is already 0.5 and set containment reaches 0.92 on pairs sharing no
phrase whatever. Worse, containment is |A n B| / |A|, so a short OCR-wrecked
passage -- ellipses, a running head, broken words -- reduces to ordinary
French tokens that are contained in any longer French passage, and scores
1.00. That happened on 10900214530 vs 10900081681: wcont 1.00, setcont 1.00,
JACCARD 0.08, two passages with nothing in common, and this script recommended
a merge and a permanent `merged` status on it.

So the ranking is now by JACCARD, which is |A n B| / |A u B| and cannot be
inflated by a short degenerate side; the top pairings are printed WITH THEIR
TEXT so the numbers can be read rather than trusted; and the verdict REFUSES
when the best jaccard in the whole matrix falls below --min-jaccard (0.15 by
default), naming the OCR-fragment case rather than reporting a confident
score. Containment is still shown, because a real match usually has both.

ROWS, NOT THE REPRESENTATIVE. The candidate's rows are read from combined_align
directly. combined_align_groups holds one row per group and would show a single
arbitrary witness -- the blindness this project spent August removing, and it
would be a poor way to answer a question about whether four specific rows
contain a line.

THE CORPUS IS THREE TABLES. Rows set aside on 15 and 18 Aug are included, so a
native that has been moved out is still found rather than silently reported
absent.

Usage:
    python3 check_native_candidate.py --group 300013186 --candidate 10600001858
"""

import argparse, configparser, sys
import psycopg2
from containment import score_pair, fold
import locus_test as LT

ap = argparse.ArgumentParser()
ap.add_argument("--group", type=int, required=True,
                help="the group carrying the provenance override")
ap.add_argument("--candidate", type=int, required=True,
                help="the located native group")
ap.add_argument("--min-jaccard", dest="min", type=float, default=0.15,
                help="refuse a verdict when the best jaccard in the matrix "
                     "falls below this. Containment alone cannot tell a "
                     "shared line from shared French; see the OCR-FRAGMENT "
                     "note in the verdict.")
ap.add_argument("--top", type=int, default=6,
                help="pairings to print, ranked by jaccard, with their text.")
ap.add_argument("--table", default="combined_align")
ap.add_argument("--setaside", nargs="*",
                default=["combined_align_translations",
                         "combined_align_labelled_noise"])
args = ap.parse_args()

cfg = configparser.ConfigParser()
cfg.read("/etc/text-pair/global_settings.ini")
conn = psycopg2.connect(user=cfg["DATABASE"]["database_user"],
                        password=cfg["DATABASE"]["database_password"],
                        database=cfg["DATABASE"]["database_name"])
cur = conn.cursor()
cur.execute("SET statement_timeout = 0")

COLS = ("group_id, source_author, source_title, source_year, "
        "source_passage, target_author, target_title, target_year, "
        "target_passage")
parts = [f"SELECT {COLS} FROM {args.table}"]
for t in args.setaside:
    cur.execute("SELECT to_regclass(%s)", (t,))
    if cur.fetchone()[0] is not None:
        parts.append(f"SELECT {COLS} FROM {t}")
    else:
        print(f"  note: {t} does not exist, skipped", file=sys.stderr)
CORPUS = "(" + " UNION ALL ".join(parts) + ") z"


def rows_of(gid):
    cur.execute(f"SELECT {COLS} FROM {CORPUS} WHERE group_id = %s", (gid,))
    return cur.fetchall()


# FOLD BEFORE SCORING. score_pair documents itself as taking "two folded
# strings" and this script passed raw passages, which UNDER-scores real
# matches: Bibliotheque/Bibliotheque 0.86 raw against 1.00 folded,
# revetir/revestir 0.83 against 0.96. fold() normalises case, accents,
# ligatures, i/j and u/v -- early-modern orthography and OCR damage, which are
# exactly what separates a native from its witnesses. Raw scoring therefore
# produced silent FALSE NEGATIVES in the one place this script looks.
A = rows_of(args.group)
B = rows_of(args.candidate)
print("=" * 78)
print(f"DOES {args.candidate} CONTAIN THE PASSAGE OF {args.group}?")
print("=" * 78)
print(f"\n  {args.group:<14} {len(A):>4} row(s)")
print(f"  {args.candidate:<14} {len(B):>4} row(s)")
if not A or not B:
    sys.exit("\n  One of the groups has no rows. Check the ids, and check "
             "whether either has been merged away or set aside.")

for lbl, rs in ((str(args.group), A), (str(args.candidate), B)):
    print(f"\n  --- {lbl} ---")
    for r in rs[:6]:
        print(f"      ({r[3]}) {str(r[1])[:38]} | {str(r[2])[:44]}")
        print(f"        {' '.join(str(r[4] or '').split())[:150]!r}")

# Every side of A against every side of B: the passage may sit on either.
print("\n" + "=" * 78)
print("CONTAINMENT, EVERY PASSAGE OF ONE AGAINST EVERY PASSAGE OF THE OTHER")
print("=" * 78)
print(f"\n      {'wcont':>7} {'setcont':>8} {'jaccard':>8}  {'dir':<6} pairing")
# RANKED BY JACCARD, NOT CONTAINMENT — 28 Aug 2026. See the header note.
scored = []
for ia, ra in enumerate(A):
    for sa_i, sa in ((4, ra[4]), (8, ra[8])):
        if not sa:
            continue
        for ib, rb in enumerate(B):
            for sb_i, sb in ((4, rb[4]), (8, rb[8])):
                if not sb:
                    continue
                try:
                    w, sc, j, d = score_pair(fold(sa), fold(sb),
                                             skip_degenerate=True)
                except Exception as e:
                    print(f"      score_pair failed: {e}", file=sys.stderr)
                    continue
                side_a = "src" if sa_i == 4 else "tgt"
                side_b = "src" if sb_i == 4 else "tgt"
                # THE SHARED RUN, added 28 Aug 2026 — see the verdict note.
                # LT.longest_run returns 0 the moment no 4-gram is shared, so
                # this is cheap on the pairings that do not match.
                run = LT.longest_run(fold(sa).split(), fold(sb).split())
                scored.append((w, sc, j, d, ia, side_a, ib, side_b, sa, sb,
                               run))
                if w >= 0.30:
                    print(f"      {w:>7.2f} {sc:>8.2f} {j:>8.2f}  {str(d)[:6]:<6} "
                          f"A[{ia}].{side_a} vs B[{ib}].{side_b}")

by_cont = max(scored, key=lambda r: r[0]) if scored else None
best = max(scored, key=lambda r: r[2]) if scored else None

if scored:
    print("\n" + "=" * 78)
    print(f"TOP {args.top} PAIRINGS BY JACCARD — read these, not the maximum "
          "containment")
    print("=" * 78)
    for r in sorted(scored, key=lambda x: -x[2])[:args.top]:
        w, sc, j, d, ia, sa_side, ib, sb_side, sa, sb, run = r
        print(f"\n  jaccard {j:.2f}   wcont {w:.2f}   setcont {sc:.2f}   "
              f"run {run:<3} A[{ia}].{sa_side} vs B[{ib}].{sb_side}")
        print(f"      A: {' '.join(str(sa).split())[:160]!r}")
        print(f"      B: {' '.join(str(sb).split())[:160]!r}")
    if by_cont is not None and by_cont[2] < args.min and by_cont is not best:
        print(f"\n  (maximum-containment pairing was A[{by_cont[4]}]."
              f"{by_cont[5]} vs B[{by_cont[6]}].{by_cont[7]} at wcont "
              f"{by_cont[0]:.2f} / jaccard {by_cont[2]:.2f} — NOT used.)")

print("\n" + "=" * 78)
print("VERDICT")
print("=" * 78)
if best is None:
    print("\n  Nothing scored. Both groups have rows but no passage pair "
          "could be compared.")
else:
    w, sc, j, d, ia, sa_side, ib, sb_side, sa, sb, run = best
    max_run = max(r[10] for r in scored)
    print(f"""
  best pairing   A[{ia}].{sa_side} against B[{ib}].{sb_side}   (highest JACCARD)
  weighted containment {w:.2f}   set containment {sc:.2f}   jaccard {j:.2f}
  longest shared run {run} word(s); longest anywhere in the matrix {max_run}

      A: {' '.join(str(sa).split())[:150]!r}
      B: {' '.join(str(sb).split())[:150]!r}
""")
    if max_run == 0:
        print(f"""  NO VERDICT — NO SHARED WORD RUN ANYWHERE IN THE MATRIX.

  Not one pairing shares even four consecutive words, whatever the containment
  says. This refusal is the whole of 28 Aug 2026 in one line.

  THE CASE THAT ADDED IT. Virgil seed 10900083047 against candidate
  300002548: best jaccard 0.19, weighted containment 0.67, and this script
  recommended a merge and a permanent 'merged' status. The seed is a French
  *Voyage de France, d'Espagne, de Portugal* (1770) quoting Virgil's EPITAPH
  in an account of his tomb; the candidate is a tag-group for *monstrum
  horrendum, informe, ingens, cui lumen ademptum*, Aeneid III.658. Two
  different Virgil quotations in two different French discussions OF Virgil.
  The containment came from shared literary-commentary vocabulary -- *les
  Romains*, *les Ecrivains du bon temps* -- which is a shared SUBJECT, not a
  shared text.

  WHY A RUN AND NOT A HIGHER JACCARD FLOOR. The --min-jaccard floor added
  earlier the same day was 0.15, chosen out of the air, and this pair cleared
  it by four hundredths. A floor on a set-overlap measure cannot express
  "these passages have no wording in common"; contiguity can. Seven merge sets
  triaged that afternoon separated real candidates from noise on exactly this,
  with nothing in between -- 167-185 words against 4-5 on Diderot, 179 against
  0 on Malherbe.

  Read the ranked table above and rule by eye, or widen the comparison.""")
    elif j < args.min:
        print(f"""  NO VERDICT. The best jaccard in the whole matrix is {j:.2f}, below the
  --min-jaccard floor of {args.min:.2f}, so nothing here is evidence of a shared
  line whatever the containment says.

  THE OCR-FRAGMENT CASE, and why this refuses rather than reporting a score.
  Containment is |A n B| / |A|. A short passage wrecked by OCR -- ellipses,
  a running head, broken words -- keeps only ordinary French tokens, and
  ordinary French is contained in ANY longer French passage. On 28 Aug 2026
  this script returned wcont 1.00, setcont 1.00 and jaccard 0.08 for
  10900214530 against 10900081681, on a pair sharing no phrase at all, and
  recommended a merge and a permanent 'merged' status on that basis. It
  ranked by containment and never read the jaccard column beside it --
  standing rule 9, in the script rather than in the reader.

  Read the ranked table above and rule by eye, or widen the comparison.""")
    elif w >= 0.60:
        print(f"""  The passage IS in the native. The override should be retired: merge
  {args.group} into {args.candidate}, set native_status = 'merged', and log
  the resolution to sourced_attributions.tsv with resolved_by =
  {args.candidate}. That is the project's stated preference -- a native
  in-corpus edition beats a provenance annotation whenever one exists.""")
    elif w >= 0.30:
        print("""  Suggestive and not conclusive. Read the two passages above before
  ruling. A partial score on an OCR-damaged line is exactly the case the
  anchor search exists for, and it is also exactly what a similarity sweep
  gets wrong in both directions.""")
    else:
        print(f"""  The work is present; this passage is not, at least not to whole-passage
  similarity. That is `native_other_verse` -- a located edition with an
  unmatched line -- and NOT `merged`, which would assert a resolution nobody
  has made. Next action is a targeted anchor search on the line against
  {args.candidate}'s rows.

  It is emphatically not `native_damaged` either: that status says the text is
  beyond reach, and an undamaged 1628 edition sitting in the corpus is the
  counter-example.""")
cur.close(); conn.close()
