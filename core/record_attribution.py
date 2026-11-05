#!/usr/bin/env python3
"""
record_attribution.py
Write ONE scholarly attribution into the provenance table. Dry run by default;
--commit required.

WHY THIS EXISTS
---------------
23 Aug 2026. Group 1200092131 displays Rossant's *Réfutation du nouvel ouvrage
de Jean-Jacques Rousseau intitulé Émile*, and the passage is Émile itself --
the Profession de foi du vicaire savoyard, "Et qui a fait ces Livres ? Des
hommes." `inspect_groups.py --works-only` shows fourteen works in the group
and every one of them is an *Examen*, a *Réfutation*, a *Réponse* or *Les
Plagiats de M. J. J. R.*: the passage circulates entirely through Rousseau's
opponents and Rousseau is on neither side of any row.

There was no way to record that. Every existing provenance writer either
edits a row that already exists (`record_native_override.py`,
`retire_provenance_override.py`) or is a hard-coded batch from one round
(`record_top3_provenance.py`, `add_horace_aristote_provenance.py`). A single
new attribution, found by reading the page, had no tool at all -- which is why
`new_sources.txt` accumulates them as prose.

WHAT AN ATTRIBUTION IS NOT
--------------------------
It is not an override. `record_native_override.py` asserts that the native IS
in the corpus and the representative-row rule cannot front it; it refuses
unless the attributed author's surname appears on some row of a candidate
group. Where the native is ABSENT, that assertion would be false. The two
tools answer different questions and the statuses say so:

    native_unsearched   nobody has looked for the native yet
    native_unaligned    the work is in the corpus; THIS passage is not aligned
    native_absent       a BIBLIOGRAPHIC fact -- the work is not in ModERN or
                        Gallica, so no passage of it can be. A reviewer's
                        declaration; no script may produce it and this one
                        will not either without --status given explicitly
    native_override     the native is present and the date order defeats it
                        -- use record_native_override.py, not this

Glenn, 19 Aug: "there is no reason to ever run native_absent on the corpus, it
is not there, it will never be there... only the references can do this." An
attribution recorded here against an absent native is precisely a
reference_passages case, and saying so is the point of recording it.

WITHDRAWING A STATUS — `--status none`, added 23 Aug 2026
---------------------------------------------------------
There was no way to say "this attribution stands and its native question is
open again". Every value in the vocabulary is a claim, and the honest move
when a claim has been withdrawn is to hold no claim — which the table already
expresses, since a CHECK constraint passes on NULL and eight rows carry it.
`split_group_loci.py` writes exactly that for an inherited attribution and
glosses it "attributed, not yet adjudicated".

It was wanted within hours of this tool being written. Three groups were given
`native_unaligned` on 23 Aug on the strength of `probe_native_orientation.py`
reporting Rousseau absent — absent FROM THOSE GROUPS. The probe is
group-scoped and `native_unaligned` is a claim about the whole corpus, and
Glenn withdrew the premise the same evening: "the rousseau shouldn't be
'unaligned', it's definitely in the database, we saw it today". Reverting them
to `native_unsearched` would be false in the other direction, the search
having been run and having found a great deal. NULL is what is actually the
case.

`--status none` clears the status and keeps the attribution. It requires
--update like any other replacement, so a status never vanishes without the
evidence recording that it did.

WHOSE REASON IS IT — `--reason-by`, added the same day for a worse cause
------------------------------------------------------------------------
`evidence` hard-coded `Glenn: "{reason}"`, so every attribution this tool
wrote put its --reason in Glenn's mouth whatever the actual source. That is
harmless while the tool transcribes his rulings out of new_sources.txt and
stops being harmless the moment it records anything else — a correction the
assistant made, an inference drawn from a run, a note from a third reader. An
audit trail that misattributes its own authority is worse than one that is
merely thin, and a provenance row saying something slightly other than what
was meant has already cost this project two days.

--reason-by defaults to Glenn, so transcribing his rulings is unchanged.

TWO GUARDS, BOTH LEARNED THE HARD WAY
--------------------------------------
**The works are printed before anything is written.** Round 19's rule, after
this assistant identified detached loci of Racine's *Esther* as *Athalie* from
the text alone: never rule on a passage without the works. An attribution is a
ruling.

**The author string is checked against the corpus.** Malherbe carried
`native_damaged` for two days because the provenance row said
`François de Malherbe` where the corpus says `François de Malherbe
(1555-1628)`, so author-keyed search could not see him and the native looked
absent. A string that matches nothing is reported loudly; it may still be
right (the work genuinely is not in the corpus, which is the whole point of
`native_absent`), but it must be a decision rather than a typo.

Usage:
    python3 record_attribution.py --group 1200092131 \\
        --author "Jean-Jacques Rousseau (1712-1778)" \\
        --title "Emile, ou, De l'éducation" --year 1762 \\
        --division "LIVRE 4" \\
        --status native_unaligned \\
        --reason "the Profession de foi du vicaire savoyard, quoted by its refuters"
"""

import argparse, configparser, csv, os, re, sys, time
import psycopg2
import corpus_source as CS

ap = argparse.ArgumentParser()
ap.add_argument("--group", type=int, required=True)
ap.add_argument("--author", required=True,
                help="the corpus's OWN authority string, life-dates included "
                     "-- 'Jean-Jacques Rousseau (1712-1778)', not 'Rousseau'. "
                     "Author-keyed search matches on this and a short form "
                     "silently finds nothing.")
ap.add_argument("--title", required=True)
ap.add_argument("--year", type=int, default=None,
                help="the work's date. For a classical text at the PHI "
                     "sentinel this is 99; see native-is-not-year-99. "
                     "Required, except with --status native_proverbial, "
                     "where a proverb has no date and the year is NULL.")
ap.add_argument("--division", default="",
                help="chapter, book, act -- 'LIVRE 4', 'Acte IV, Scène VI'. "
                     "Recorded where the table has a column for it, otherwise "
                     "folded into the note.")
ap.add_argument("--status", default=None,
                help="see the docstring. On a NEW row it defaults to "
                     "native_unsearched, which claims the least. With --update "
                     "and no --status the EXISTING status is KEPT -- until 23 "
                     "Sep 2026 it silently reverted to native_unsearched, which "
                     "destroyed an override twice in one evening. The literal "
                     "'none' CLEARS the status to NULL -- attributed, not "
                     "adjudicated -- for a claim withdrawn rather than replaced.")
ap.add_argument("--reason", required=True,
                help="how the attribution was made. Goes into `evidence`, "
                     "which is the audit trail a later reader inherits.")
ap.add_argument("--reason-by", default="Glenn",
                help="who the --reason belongs to. Written into `evidence` "
                     "beside the quotation. Defaults to Glenn because that is "
                     "what this tool is normally for; name the actual source "
                     "for anything else, so the trail does not credit a "
                     "ruling to someone who did not make it.")
ap.add_argument("--note", default="")
ap.add_argument("--update", action="store_true",
                help="replace an attribution already on this group. Refused "
                     "without it, because silently overwriting somebody's "
                     "ruling is how a judgement disappears.")
ap.add_argument("--retired-ok", action="store_true",
                help="record against a group that has NO ROWS in any table. "
                     "Refused by default, because a live group is what an "
                     "attribution is normally about and an unknown id is more "
                     "often a typo than a judgement. The legitimate case is a "
                     "RETIRED id whose attribution the page still inherits "
                     "forward and DISPLAYS: correcting a wrong claim there is "
                     "not re-keying it — the row keeps its own id and stays a "
                     "historical record, it simply stops asserting something "
                     "false. Precedent: 11200308601, 7 Sep 2026, whose "
                     "inherited attribution was corrected in place. Passing "
                     "this is a claim you are making, so it is stamped into "
                     "`evidence` rather than passing silently.")
ap.add_argument("--force-author", action="store_true",
                help="record even though the author string appears nowhere in "
                     "the corpus. Legitimate when the work genuinely is not "
                     "held -- which is what native_absent means -- and a typo "
                     "otherwise, so it is a claim you make rather than a "
                     "default.")
ap.add_argument("--prov", default="combined_align_groups_provenance")
ap.add_argument("--table", default="combined_align")
ap.add_argument("--tsv", default="sourced_attributions.tsv")
ap.add_argument("--commit", action="store_true")
args = ap.parse_args()
# 29 Sep 2026: a proverb with a written tradition (the Golden Rule) has no
# work date; native_proverbial alone records attributed_year NULL.
if args.year is None and args.status != "native_proverbial":
    sys.exit("  --year is required (only --status native_proverbial may omit it).")

cfg = configparser.ConfigParser()
cfg.read("/etc/text-pair/global_settings.ini")
conn = psycopg2.connect(user=cfg["DATABASE"]["database_user"],
                        password=cfg["DATABASE"]["database_password"],
                        database=cfg["DATABASE"]["database_name"])
cur = conn.cursor()
cur.execute("SET statement_timeout = 0")

cur.execute("SELECT to_regclass(%s)", (args.prov,))
if cur.fetchone()[0] is None:
    sys.exit(f"{args.prov} does not exist. create_provenance_table.py builds it.")

cur.execute("""SELECT column_name FROM information_schema.columns
                WHERE table_name = %s""", (args.prov.split(".")[-1],))
pcols = {r[0] for r in cur.fetchall()}

# THE VOCABULARY IS A CHECK CONSTRAINT, AND IT HAS DRIFTED BEFORE.
# 172 live rows carried statuses the constraint forbade, invisibly, until
# set_status_vocabulary.py caught it. Read the constraint rather than a list
# in this file, so the two cannot disagree.
cur.execute("""SELECT pg_get_constraintdef(oid) FROM pg_constraint
                WHERE conname = 'prov_native_status_vocab'
                  AND conrelid = %s::regclass""", (args.prov,))
row = cur.fetchone()
vocab = set(re.findall(r"'([a-z_]+)'", row[0])) if row else set()

# CLEARING is not a vocabulary value, so it is resolved before the check.
# NULL passes any CHECK constraint by definition; the guard below is that it
# can only ever be written over an EXISTING row, since clearing a status that
# was never set is not an operation anyone means to perform.
STATUS_GIVEN = args.status is not None
if not STATUS_GIVEN:
    args.status = "native_unsearched"   # provisional; kept status decided below
CLEAR = args.status.strip().lower() == "none"
STATUS = None if CLEAR else args.status
if not CLEAR and vocab and args.status not in vocab:
    sys.exit(f"""
REFUSING: '{args.status}' is not in the prov_native_status_vocab constraint.

Allowed: {', '.join(sorted(vocab))}

If a new value is wanted, add it in set_status_vocabulary.py and commit that
first -- the constraint is the definition, not this script.""")
if args.status == "native_override":
    sys.exit("""
REFUSING: native_override asserts the native IS in the corpus and the
earliest-year rule cannot front it. That is record_native_override.py's
claim to make, and it verifies the native's presence before making it. This
script records an attribution, which is a different and weaker statement.""")

# ---------------------------------------------------------------------------
# Does a row already exist?
# ---------------------------------------------------------------------------
cur.execute(f"""SELECT attributed_author, attributed_title, attributed_year,
                       native_status, evidence
                  FROM {args.prov} WHERE group_id = %s""", (args.group,))
existing = cur.fetchone()

# --update WITHOUT --status KEEPS THE STATUS — 23 Sep 2026. It used to revert
# the row to native_unsearched, silently; see first-printing-or-quotation.
if existing and not STATUS_GIVEN:
    STATUS = existing[3]
    args.status = STATUS if STATUS is not None else "NULL (kept)"
    CLEAR = False      # keeping a NULL is not withdrawing a status
    print(f"  --status not given: KEEPING the existing status {STATUS!r}.")

# A PINNED surname key is authoritative (surname_key.py). Say so; the
# database trigger installed by pin_surnames.py refuses the overwrite anyway.
import surname_key as _SK
_PINNED = args.group in _SK.pinned_groups(cur, args.prov)
if _PINNED:
    print("  attributed_surname is PINNED on this group and will not change.")

# ---------------------------------------------------------------------------
# THE WORKS. Round 19's rule: never rule on a passage without them.
# ---------------------------------------------------------------------------
src = CS.CorpusSource(cur, table=args.table, warn=lambda m: None)
works, n_rows = {}, 0
for t in src.tables:
    cur.execute(f"""SELECT source_author, source_title, target_author,
                           target_title, COUNT(*)
                      FROM {t} WHERE group_id = %s
                     GROUP BY 1,2,3,4""", (args.group,))
    for sa, st, ta, tt, n in cur.fetchall():
        n_rows += n
        for a, ti_ in ((sa, st), (ta, tt)):
            k = f"{(a or '—')[:32]} · {(ti_ or '—')[:44]}"
            works[k] = works.get(k, 0) + n

SHOWN_STATUS = ("NULL — status CLEARED (attributed, not adjudicated)"
                if CLEAR else args.status)
print("=" * 78)
print("WITHDRAWING A NATIVE_STATUS" if CLEAR else "RECORDING AN ATTRIBUTION")
print("=" * 78)
print(f"""
  group             {args.group}   [{n_rows:,} row(s), {len(works)} work(s)]
  attributing to    {args.author}
                    {args.title} ({args.year})""" +
      (f"\n                    {args.division}" if args.division else "") + f"""
  native_status     {SHOWN_STATUS}
""")
if not n_rows and not args.retired_ok:
    sys.exit(f"""  Refusing: group {args.group} has no rows in any table.
  Check the id -- a merge may have retired it.

  If it IS retired and the page still inherits this attribution forward to a
  live canonical, correcting it there is legitimate: pass --retired-ok, which
  stamps that claim into the evidence.""")
if not n_rows:
    print("""  *** --retired-ok: this group has NO ROWS. Recorded as a
      correction to an attribution the page inherits forward, not as a claim
      about a live group. The row keeps its own id.
""")

print(f"  THE WORKS IN THIS GROUP ({min(len(works), 20)} of {len(works)})")
print("  " + "-" * 74)
for k, n in sorted(works.items(), key=lambda kv: -kv[1])[:20]:
    print(f"      {n:>5}  {k}")
if len(works) > 20:
    print(f"      ... {len(works) - 20} more")
print("""
  Read these before committing. If the attributed work is among them, the
  native is IN the group and this may be an override case rather than an
  attribution -- probe_native_orientation.py answers which. If it is absent,
  the passage reaches the corpus only through the works above, and that is
  what the status should say.""")

# ---------------------------------------------------------------------------
# Is the author string one the corpus uses?
# ---------------------------------------------------------------------------
# surname() is the shared key from surname_key.py since 23 Sep 2026 --
# one definition for every writer of attributed_surname. See that
# module for why the local copies were removed.
from surname_key import surname


exact = variants = 0
surn = surname(args.author)
for t in src.tables:
    cur.execute(f"""SELECT COUNT(*) FROM {t}
                     WHERE source_author = %s OR target_author = %s""",
                (args.author, args.author))
    exact += cur.fetchone()[0]
    if surn:
        cur.execute(f"""SELECT COUNT(*) FROM {t}
                         WHERE source_author ILIKE %s OR target_author ILIKE %s""",
                    (f"%{surn}%", f"%{surn}%"))
        variants += cur.fetchone()[0]

print(f"""
  THE AUTHOR STRING
      exact matches in the corpus        {exact:>9,}
      any row whose author contains '{surn}'  {variants:>9,}
""")
if exact == 0:
    cur.execute(f"""SELECT DISTINCT source_author FROM {args.table}
                     WHERE source_author ILIKE %s LIMIT 8""", (f"%{surn}%",))
    near = [r[0] for r in cur.fetchall()]
    print(f"""      *** The corpus uses this string on NO row. ***

      Malherbe carried native_damaged for two days on exactly this: the
      provenance said 'François de Malherbe' where the corpus says
      'François de Malherbe (1555-1628)', so author-keyed search could not
      see him and the native looked absent.""")
    if near:
        print("\n      Strings the corpus DOES use containing that surname:")
        for s in near:
            print(f"          {s}")
    print("""
      If the work genuinely is not in the corpus, that is native_absent and
      the mismatch is expected -- rerun with --force-author. Otherwise fix
      the string.""")
    if not args.force_author:
        sys.exit("\n  Refusing without --force-author.")

if existing:
    e_au, e_ti, e_yr, e_st, e_ev = existing
    print(f"""
  *** A PROVENANCE ROW ALREADY EXISTS ON THIS GROUP ***
      {e_au} — {e_ti} ({e_yr})
      native_status  {e_st}
      evidence       {str(e_ev)[:160]}
""")
    if not args.update:
        sys.exit("""  Refusing. Pass --update to replace it, having read the
  above -- a ruling that vanishes without trace is worse than a stale one.""")
elif CLEAR:
    sys.exit(f"""
  Refusing: --status none CLEARS a status, and group {args.group} has no
  provenance row to clear. A new attribution states what is known about the
  native; write it with a status that says so, or with the default
  native_unsearched if nobody has looked.""")

stamp = time.strftime("%Y-%m-%d")
div = f" ({args.division})" if args.division else ""
head = (f"{stamp}: native_status WITHDRAWN to NULL; attribution unchanged."
        if CLEAR else f"{stamp}: attribution recorded.")
RETIRED_NOTE = (" Recorded with --retired-ok: this group has no rows in any "
                "table, so the attribution is corrected where the page "
                "INHERITS it forward rather than asserted about a live group."
                if not n_rows else "")
evidence = (f"{head} {args.author} — {args.title}"
            f"{div}, {args.year if args.year is not None else 'undated (proverbial)'}. {args.reason_by}: \"{args.reason}\" "
            f"Group holds {n_rows} row(s) across {len(works)} work(s); "
            f"author string matches {exact:,} row(s) exactly."
            f"{RETIRED_NOTE} {args.note}").strip()
if CLEAR and existing:
    evidence = (f"{evidence} The withdrawn status was "
                f"{existing[3]!r}; NULL here means attributed but NOT "
                f"adjudicated, not that the question was never asked.")
if existing and existing[4]:
    evidence = f"{evidence}\n[superseded] {existing[4]}"

print("  evidence to be written:\n")
for line in evidence.splitlines():
    print(f"      {line}")

if not args.commit:
    print("""

  Dry run. Nothing written. Rerun with --commit.
""")
    sys.exit(0)

# Populate only columns the table actually has, so a schema that has gained or
# lost a division column does not need this script edited.
cols = {"group_id": args.group, "attributed_author": args.author,
        "attributed_title": args.title, "attributed_year": args.year,
        "native_status": STATUS, "evidence": evidence}
# THE COLUMN THE TIE-BREAK READS. rebuild_derived_tables.py chooses a group's
# representative row by earliest source_year and then, since 23 Aug, by
# whether a row's source_author carries the group's `attributed_surname`.
# This tool never populated it, so every attribution it wrote was invisible
# to that rule and could not move a byline however certain it was.
if "attributed_surname" in pcols and not _PINNED:
    cols["attributed_surname"] = surn or None
note = args.note
if args.division:
    if "attributed_division" in pcols:
        cols["attributed_division"] = args.division
    elif "division" in pcols:
        cols["division"] = args.division
    else:
        note = f"{args.division}. {note}".strip()
if note and "note" in pcols:
    cols["note"] = note
cols = {k: v for k, v in cols.items() if k in pcols or k == "group_id"}

if existing:
    sets = ", ".join(f"{k} = %s" for k in cols if k != "group_id")
    cur.execute(f"UPDATE {args.prov} SET {sets} WHERE group_id = %s",
                [v for k, v in cols.items() if k != "group_id"] + [args.group])
    print(f"\n  updated {cur.rowcount} provenance row(s)")
else:
    cur.execute(f"""INSERT INTO {args.prov} ({', '.join(cols)})
                    VALUES ({', '.join(['%s'] * len(cols))})""",
                list(cols.values()))
    print(f"\n  inserted {cur.rowcount} provenance row(s)")
conn.commit()

header = ["group_id", "status", "resolved_by", "attributed_author",
          "attributed_title", "attributed_year", "note", "passage_excerpt",
          "review_file"]
new = not os.path.exists(args.tsv)
with open(args.tsv, "a", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, delimiter="\t")
    if new:
        w.writerow(header)
    w.writerow([args.group, ("" if STATUS is None else STATUS), "", args.author,
                args.title, args.year, evidence.splitlines()[0], "",
                "record_attribution.py"])
print(f"  appended 1 line to {args.tsv}")

cur.execute(f"""SELECT native_status, COUNT(*) FROM {args.prov}
                 GROUP BY 1 ORDER BY 2 DESC""")
print("\n  native_status distribution now:")
for st, c in cur.fetchall():
    print(f"      {str(st):<22} {c:>4}")
print("""
  Rebuild the page so the attribution reaches a reader:

      python3 build_top_passages_page.py --out /path/to/site
""")
cur.close(); conn.close()
