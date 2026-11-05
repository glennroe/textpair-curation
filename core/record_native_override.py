#!/usr/bin/env python3
"""
record_native_override.py
Write a PERMANENT override to the database: the native is confirmed present,
and no merge will ever make the representative-row rule show it. Dry run by
default.

WHY THIS IS NOT retire_provenance_override.py
-----------------------------------------------
That script asserts the native was found FOR THIS PASSAGE **and the group
merged into one holding it** -- native_status becomes 'resolved' because a
merge fixed what the page displays. This script is for the other outcome:
the native is just as confirmed, and merging would not help, because the
earliest-year representative-row rule would still promote a different,
earlier-dated witness ahead of it even inside the merged group. Two overrides
were read this way on 19 Aug 2026 (campaign_natives2.txt, "WOULD NOT FIX --
the native is here and the DATE ORDER defeats it"):

    900041946   Boileau's Satires (1701) is the right native, but Pradon's
                Le triomphe de Pradon (1684) came in from Gallica and
                predates it -- the corpus holds a late printing of the
                source and an early printing of someone quoting it, and
                date order inverts authorship. Glenn, 19 Aug: "the Satires
                are the right native, they're just dated later than
                Pradon."

    10600028907  Emile -- SECOND CORRECTION, 23 Aug 2026. This entry read
                "a YEAR TIE broken by insertion order, not a date order
                inversion. Do not use this script for it," on the strength
                of the tie-break remedy described below. Both halves failed.

                The remedy was never in rebuild_derived_tables.py at all --
                the ORDER BY read `source_year ASC NULLS LAST, rowid` until
                23 Aug, so `attributed_surname` was added, populated and
                read by nothing for two days. And once it WAS restored, this
                group did not move, because the clause reorders rows WITHIN
                a group and Rousseau has no row in this one: the measured
                split was 39 groups whose attribution matches some row
                against 64 where it matches none, and this is one of the 64.

                So it is not a tie. It is a structural absence -- the native
                sits in 10600026336, where Rousseau's Emile is the source at
                1762 and aligns to Beaumont's Mandement, a witness this
                group also carries, at containment 1.00 and jaccard 0.93.
                Glenn, 23 Aug, on seeing the page unchanged for the third
                time: "Just override that."

                A merge onto 10600026336 would also fix it and is deferred
                to the reference_passages work, which has to rule on where
                the Profession de foi locus ends. Retire this override
                through retire_provenance_override.py if that merge runs.

                CORRECTION, 21 Aug 2026. This entry previously read "This
                one WAS fixed: the tying rival lost the tie on Glenn's
                explicit ruling ... so it goes through
                retire_provenance_override.py --status resolved instead,
                once merged." Every part of that was wrong, and it was
                written here as settled fact from a round summary rather
                than from the database.

                trace_group.py 10600028907, run the same day: 58 rows,
                received 0 groups by merge, became nothing, native_status
                still 'native_unsearched'. Nothing was ever done to it. The
                page was at that moment attributing Rousseau's Profession
                de foi to "Beaumont, Christophe de — Mandement ... portant
                condamnation d'un livre qui a pour titre: Emile" (1762) --
                the Archbishop's censure of Emile credited with Emile's own
                words.

                Nor could a merge ever have fixed it. The representative
                rule ordered by source_year then rowid, and merging does
                not change any row's rowid; merging a work with the
                pamphlet attacking it in the same year guarantees a
                coin-flip on the byline rather than resolving one.

                THE ACTUAL REMEDY, adopted 21 Aug: the tie-break in
                rebuild_derived_tables.py now prefers a source_author
                matching an attribution on the group, via the
                attributed_surname column that add_attributed_surname.py
                populates. That repairs every same-year tie at once,
                including ones not yet found, and leaves this script's
                territory -- a native genuinely dated LATER than its
                quoter -- untouched, because such a native loses on year
                before any tie-break is reached.

                This is what `declarations-need-a-recorded-reversal` is
                about, and the reversal is recorded here rather than only
                in prose elsewhere.

**Merging is still permitted where it consolidates a locus's witnesses** --
the override carries the attribution either way, per the review file -- but
it resolves nothing on its own and must not be recorded as though it had.
Run this whether or not a consolidating merge happens; native_status does
not depend on it.

WHY A NEW VOCABULARY VALUE RATHER THAN 'out_of_scope'
--------------------------------------------------------
'out_of_scope' means the attribution is correct and kept but outside what
the project describes -- a scope judgement. This is not that: the passage is
squarely in scope and squarely matched, at containment as high as 1.00. The
failure is structural, in the representative-row rule, not editorial. Glenn's
call, 21 Aug 2026: a new value, 'native_override'. Add it to the CHECK
constraint FIRST:

    python3 set_status_vocabulary.py --commit

or this script's UPDATE fails against the old constraint with a clear
IntegrityError naming it.

TWO FAULTS, ONE STATUS — 21 Aug 2026
-------------------------------------
`native_override` covers both of the conditions under which the
representative-row rule cannot be made to show a correct attribution. They
look identical on the page and they are not the same thing, so the script
works out which one it is and words `evidence` accordingly rather than
asserting one of them in every case.

  DATE INVERSION  the native's surviving edition postdates a witness quoting
                  it. It loses on source_year before any tie-break is
                  reached, and no tie-break rule can reach a row that has
                  already lost on year. Permanent in the strong sense.
                  Boileau's Satires (1701) behind Pradon (1684); J.-B.
                  Rousseau's Odes (1723) behind a Mercure galant of 1711.

  TIE             the native is present as a source at the SAME year and
                  lost the tie-break, which is `rowid` -- insertion order,
                  which means nothing. No MERGE repairs it, since merging
                  changes no row's rowid, but a tie-break that consulted the
                  attribution would. So the override records a RULING that
                  the rule cannot currently make, rather than an unrepairable
                  defect, and the evidence says so.

Measured by probe_native_orientation.py, 21 Aug: 1200064257 (Rousseau's
Discours, 1755, behind Bethisy's Lettre answering it), 10900028712 (Racine's
Phedre, 1677, behind the anonymous Dissertation on it) and 11200004591
(Virgil behind the Histoire auguste, both at the sentinel 99) are all ties,
with the native present on the source side in 23, 30 and 5 rows respectively.

A provenance-aware tie-break was built and then withdrawn the same day:
against 200 hand-made attributions with three conflicts, a schema dependency
inside the rebuild-recovery script was not a proportionate remedy. Glenn's
call, 21 Aug: "happy for me to adjudicate these and future native_override
calls." If the tie population ever grows enough to change that arithmetic,
the mechanism is described in this file's git history and the argument
against it was about proportion, not correctness.

THE CANDIDATE CHECK, ADDED 21 Aug 2026
---------------------------------------
The evidence this script writes asserts that the native is present at the
groups named in --candidates. Until now nothing tested that: the only
preflight was COUNT(*) > 0, which every live group passes. It now also asks
whether the attributed author's surname appears as an author on any row of
each candidate group, refuses when no candidate can show it, and records in
`evidence` HOW the presence was established -- a matched author string, or an
explicit --skip-native-check. A permanent ruling should not rest on a check
nobody ran.

The candidate lines also print a real representative row now. They used to
print MIN(source_year), MIN(source_author) and MIN(source_title) side by side,
which is a composite of up to three different rows and reads exactly like one
row. On the 343-row Rousseau group it printed a title from a periodical that
was not the representative at all.

ORDER
-----
    python3 set_status_vocabulary.py --commit                # once
    python3 record_native_override.py --group 900041946 \\
        --candidates 10300019810,10300019809,10000001138,10300019811 \\
        --reason "the Satires are the right native, they're just dated later than Pradon, who came in from Gallica" \\
        --commit

Usage:
    python3 record_native_override.py --group 900041946 \\
        --candidates 10300019810,10300019809,10000001138,10300019811 \\
        --reason "..."
"""

import argparse, configparser, csv, os, re, sys, time
import psycopg2

ap = argparse.ArgumentParser()
ap.add_argument("--group", type=int, required=True)
ap.add_argument("--candidates", required=True,
                help="comma-separated group_ids in combined_align that carry "
                     "the confirmed native passage -- for the record, not "
                     "for merging. From the campaign review file that "
                     "settled this.")
ap.add_argument("--reason", required=True,
                help="Glenn's ruling, quoted, explaining why no merge can "
                     "fix the representative-row display.")
ap.add_argument("--ruling-date", default="",
                help="when the ruling above was made, e.g. '19 Aug 2026'. "
                     "NOT the same as the recording date, which is stamped "
                     "automatically. Leave blank rather than guess.")
ap.add_argument("--prov", default="combined_align_groups_provenance")
ap.add_argument("--table", default="combined_align")
ap.add_argument("--groups-table", default="",
                help="defaults to <table>_groups. Read to find the row the "
                     "page actually displays, so the recorded reason names "
                     "the right fault -- a TIE and a DATE INVERSION look "
                     "identical on the page and are not the same thing.")
ap.add_argument("--tsv", default="sourced_attributions.tsv")
ap.add_argument("--note", default="")
ap.add_argument("--skip-native-check", action="store_true",
                help="record the override even though the attributed author's "
                     "surname appears on no row of any candidate group. The "
                     "check is a crude substring test and a mononym, a title "
                     "or a Latin form can defeat it legitimately. Overriding "
                     "it is a claim you are making, so it is stamped into "
                     "`evidence` rather than passing silently.")
ap.add_argument("--commit", action="store_true")
args = ap.parse_args()

cfg = configparser.ConfigParser()
cfg.read("/etc/text-pair/global_settings.ini")
conn = psycopg2.connect(user=cfg["DATABASE"]["database_user"],
                        password=cfg["DATABASE"]["database_password"],
                        database=cfg["DATABASE"]["database_name"])
cur = conn.cursor()
cur.execute("SET statement_timeout = 0")

cur.execute("""SELECT pg_get_constraintdef(oid) FROM pg_constraint
                WHERE conname = 'prov_native_status_vocab'
                  AND conrelid = %s::regclass""", (args.prov,))
row = cur.fetchone()
if row is None or "native_override" not in row[0]:
    sys.exit(f"""
REFUSING: the prov_native_status_vocab CHECK constraint does not yet allow
'native_override'{"" if row is None else f" ({row[0]})"}.

    python3 set_status_vocabulary.py --commit

Run that first, then rerun this.""")

cur.execute(f"""SELECT group_id, attributed_author, attributed_title,
                       attributed_year, note, native_status, evidence
                  FROM {args.prov} WHERE group_id = %s""", (args.group,))
row = cur.fetchone()
if not row:
    sys.exit(f"No provenance row for group_id {args.group} in {args.prov}.")
gid, au, ti, yr, note, status, evidence = row

# WHAT A CANDIDATE LINE REPORTS, AND WHY IT CHANGED, 21 Aug 2026
# ---------------------------------------------------------------
# This block used to read MIN(source_year), MIN(source_author) and
# MIN(source_title) as three independent aggregates and print them on one
# line. That line is not a row. MIN on a text column is alphabetical, so the
# three fields could come from three different rows, and on the 343-row
# Rousseau group they did: it printed "1711, — Bibliothèque raisonnée des
# ouvrages des..." while the group's actual representative was the Mercure
# galant issue. A composite of that kind reads exactly like a record and is
# not one.
#
# It now reports a REAL representative row -- the earliest source_year, ties
# broken by rowid, which is the rule the derived groups table is built on --
# and, more to the point, it CHECKS THE CLAIM. The evidence text this script
# writes asserts the native is present at these groups. Nothing verified that;
# the only test was COUNT(*) > 0, which any group passes. `holds_native` now
# asks whether the attributed author's surname appears on either side of any
# row in the candidate group, and the preflight refuses when none of them can
# show it.
def _surname(author):
    """The family name. Parenthesised dates are stripped first; a comma is
    read as the inverted form ('Bayle, Pierre') and the name before it wins,
    because taking the last token unconditionally returns the forename and
    the presence check below would then refuse a perfectly good override."""
    if not author:
        return ""
    s = re.sub(r"\([^)]*\)", "", str(author)).strip()
    if "," in s:
        s = s.split(",", 1)[0].strip()
    parts = s.split()
    return parts[-1] if parts else ""


cur.execute("""SELECT column_name FROM information_schema.columns
                WHERE table_name = %s
                  AND column_name IN ('target_author', 'rowid')""",
            (args.table.split(".")[-1],))
_tcols = {r[0] for r in cur.fetchall()}
_ORDER = ("source_year ASC NULLS LAST, rowid" if "rowid" in _tcols
          else "source_year ASC NULLS LAST")
_surn = _surname(au)

cand_ids = [int(x) for x in args.candidates.split(",") if x.strip()]
cand_info = []
for cid in cand_ids:
    cur.execute(f"SELECT COUNT(*) FROM {args.table} WHERE group_id = %s",
                (cid,))
    n = cur.fetchone()[0]
    y = a = t = None
    if n:
        cur.execute(f"""SELECT source_year, source_author, source_title
                          FROM {args.table} WHERE group_id = %s
                         ORDER BY {_ORDER} LIMIT 1""", (cid,))
        y, a, t = cur.fetchone()
    holds = False
    if n and _surn:
        _where = "source_author ILIKE %s"
        _params = [cid, f"%{_surn}%"]
        if "target_author" in _tcols:
            _where = f"({_where} OR target_author ILIKE %s)"
            _params.append(f"%{_surn}%")
        cur.execute(f"""SELECT EXISTS (SELECT 1 FROM {args.table}
                         WHERE group_id = %s AND {_where})""", _params)
        holds = cur.fetchone()[0]
    cand_info.append((cid, n, y, a, t, holds))

print("=" * 78)
print("RECORDING A PERMANENT NATIVE OVERRIDE")
print("=" * 78)
print(f"""
  provenance row      {gid}
    attributed        {au} — {ti} ({yr})
    native_status     {status!r}  ->  'native_override'
    note              {str(note)[:100]!r}
    evidence          {str(evidence)[:100]!r}

  confirmed native passage present at:
    (representative row = earliest source_year; "holds" = the attributed
     author's surname appears on some row of that group)""")
for cid, n, y, a, t, holds in cand_info:
    if not n:
        print(f"      group {cid}: *** 0 rows in {args.table} -- check the id ***")
        continue
    mark = "holds" if holds else "*** surname NOT found in this group ***"
    print(f"      group {cid}: {n:,} row(s)  [{mark}]")
    print(f"          representative: {y}, {str(a)[:34]} — {str(t)[:44]}")
if any(n == 0 for _, n, _, _, _, _ in cand_info):
    sys.exit("\n  Refusing: at least one candidate group has no rows. "
             "Fix --candidates.")
_native_shown = bool(_surn) and any(h for *_, h in cand_info)
if _surn and not _native_shown and not args.skip_native_check:
    sys.exit(f"""
  Refusing: '{_surn}' does not appear as an author on ANY row of ANY
  candidate group. The evidence this script writes asserts the native is
  present at those groups, and nothing here can show it.

  Either the --candidates ids are wrong, or the native sits under a different
  author string (an authority id, a variant spelling, an OCR form), or the
  attribution itself needs checking. Confirm with check_native_candidate.py
  before recording a permanent override on it.

  If the surname test is simply too crude for this case -- a mononym, a title,
  a Latin form -- rerun with --skip-native-check and say so in --note.""")

# WHICH FAULT IS THIS, ACTUALLY? — added 21 Aug 2026
# ---------------------------------------------------
# Two conditions produce an identical page: a DATE INVERSION, where the
# native's surviving edition postdates a witness quoting it, and a TIE, where
# the native is present at the SAME year and lost the tie-break to `rowid`,
# which is insertion order and means nothing.
#
# The distinction matters to the audit trail, not to the remedy. The evidence
# text used to assert an "earlier-dated witness" and that "the override stands
# permanently" in every case. For a tie both clauses are false: the rival is
# not earlier-dated, and the rule COULD show the native under a tie-break that
# consulted the attribution -- it simply does not today. Recording a wrong
# reason is the failure this project keeps paying for, so the reason is now
# derived rather than assumed.
#
# Measured by probe_native_orientation.py on 21 Aug: of the four cases looked
# at, three were ties (1200064257 Rousseau/Bethisy 1755, 10900028712
# Racine/the Dissertation 1677, 11200004591 Virgil/Histoire auguste at the
# sentinel 99) and one -- Emile, 10600028907 -- was neither, the native being
# absent from the group entirely and correctly carrying native_unsearched.
GROUPS = args.groups_table or f"{args.table}_groups"
_rep_year = _nat_year = None
_kind = "unknown"
cur.execute("SELECT to_regclass(%s)", (GROUPS,))
if cur.fetchone()[0] is not None:
    cur.execute(f"""SELECT source_year, source_author FROM {GROUPS}
                     WHERE group_id = %s""", (args.group,))
    _r = cur.fetchone()
    if _r:
        _rep_year = _r[0]
    if _surn:
        # 11 Oct 2026: EITHER SIDE. The native can sit on the target side of a row
        # (La Riviere 1626 x Malherbe 1628, 11200313904); a source-only search
        # returned None and the override was recorded as [unknown].
        cur.execute(f"""SELECT MIN(y) FROM (
                          SELECT source_year AS y FROM {args.table}
                           WHERE group_id = %s AND source_author ILIKE %s
                          UNION ALL
                          SELECT target_year FROM {args.table}
                           WHERE group_id = %s AND target_author ILIKE %s) z""",
                    (args.group, f"%{_surn}%", args.group, f"%{_surn}%"))
        _nat_year = cur.fetchone()[0]
    # THE NATIVE IS A WORK, NOT AN AUTHOR — 23 Sep 2026. The surname test
    # above finds the earliest row by the attributed AUTHOR, and when the
    # witness displacing the native is by that same author -- his letter, a
    # draft, an earlier edition -- that row IS the displacer, and the verdict
    # comes out "tie" at the displacer's own year. It did so on all 29 Thomas
    # Gray groups (6 Sep): Gray's letters of 1746-58 fronting Les poesies of
    # 1797, recorded as same-year ties. Where the attributed TITLE locates
    # rows, it decides the native's year; the surname is the fallback only.
    _nat_basis = "author"
    _rep_au = _r[1] if _r else None
    if ti:
        _tkey = re.sub(r"\s+", " ", str(ti).strip())[:25]
        cur.execute(f"""SELECT MIN(y) FROM (
                          SELECT source_year AS y FROM {args.table}
                           WHERE group_id = %s AND source_title ILIKE %s
                          UNION ALL
                          SELECT target_year FROM {args.table}
                           WHERE group_id = %s AND target_title ILIKE %s) z""",
                    (args.group, _tkey.replace("%", "") + "%", args.group, _tkey.replace("%", "") + "%"))
        _ty = cur.fetchone()[0]
        if _ty is not None:
            _nat_year, _nat_basis = _ty, "title"
    if (_nat_basis == "author" and _surn and _rep_au
            and _surn.lower() in str(_rep_au).lower()):
        # The displacer carries the surname and the title found nothing:
        # the two cannot be told apart here, so say so instead of guessing.
        print("\n  *** The displacing witness is itself by the attributed "
              "author, and the\n      attributed title matches no row, so "
              "tie and inversion cannot be told\n      apart here. Recorded "
              "as undetermined. ***")
        _nat_year = None
if _nat_year is not None and _rep_year is not None:
    if str(_nat_year) == str(_rep_year):
        _kind = "tie"
    elif _nat_year > _rep_year:
        _kind = "inversion"
    else:
        _kind = "earlier"

print(f"""
  WHICH FAULT
    representative source_year   {_rep_year}
    native's earliest source_year {_nat_year}""" + ("""
    -> TIE. The native is present at the SAME year and lost the tie-break,
       which is `rowid` -- insertion order. No merge repairs it, because
       merging changes no row's rowid. The override records the ruling the
       tie-break cannot make.""" if _kind == "tie" else """
    -> DATE INVERSION. The native's surviving edition postdates a witness
       quoting it, so it loses on source_year before any tie-break. This is
       permanent under any tie-break rule.""" if _kind == "inversion" else """
    -> The native is dated EARLIER than the representative, so it should
       already be winning. Something else is wrong here -- read the group
       before recording anything.""" if _kind == "earlier" else """
    -> Could not be determined (no groups table, no surname, or the native
       is not in this group under a matching author string). The evidence
       will say so rather than guess."""))
# TARGET SIDE ONLY -- 22 Oct 2026 (Phase P t01: Molière's Psyché, Racine's Esther under a 1692 libretto
# collection). The representative row is chosen among SOURCE rows only; a native whose earlier-dated document sits
# only on the TARGET side cannot win however early it is. That is a real fault, not "something else wrong".
if _kind == "earlier":
    _q = [args.group]; _w = []
    if ti:
        _w.append("source_title ILIKE %s"); _q.append(re.sub(r"\s+", " ", str(ti).strip())[:25].replace("%", "") + "%")
    if _surn:
        _w.append("source_author ILIKE %s"); _q.append(f"%{_surn}%")
    _src_year = None
    if _w:
        cur.execute(f"SELECT MIN(source_year) FROM {args.table} WHERE group_id = %s AND (" + " OR ".join(_w) + ")", _q)
        _src_year = cur.fetchone()[0]
    if _src_year is None or (_rep_year is not None and _src_year > _rep_year):
        _kind = "target_only"
        print(f"""    -> but on the SOURCE side the native is {'absent' if _src_year is None else 'dated ' + str(_src_year)}:
       it sits (earlier) only as a TARGET, and the representative is chosen among
       source rows, so it cannot win. TARGET-SIDE-ONLY: the override records it.""")
if _kind == "earlier":
    sys.exit("\n  Refusing: the native already sorts earliest and should be "
             "displayed. An override would paper over a different fault.")

stamp = time.strftime("%Y-%m-%d")
who = f"Glenn, {args.ruling_date}" if args.ruling_date else "Glenn"
# How the presence claim was established is part of the record. A reader two
# rounds from now cannot tell an author-string match from an unverified
# assertion unless the evidence says which one this was.
if _native_shown:
    _basis = (f"author string '{_surn}' found on a row of "
              + ", ".join(str(c) for c, *_r, h in cand_info if h))
elif not _surn:
    _basis = ("presence NOT machine-checked: no surname could be parsed from "
              "the attributed author")
else:
    _basis = (f"presence NOT machine-checked: '{_surn}' appears on no row of "
              f"any candidate group; recorded with --skip-native-check")
if _kind == "tie":
    _fault = (f"The native is present as a SOURCE at the same year as the "
              f"row that displaces it ({_rep_year}), so the earliest-year "
              f"rule reached its tie-break, which is `rowid` -- insertion "
              f"order. No merge repairs that, because merging changes no "
              f"row's rowid.")
    _standing = ("The override stands until the representative-row rule "
                 "breaks ties on the attribution rather than on rowid; it "
                 "records a ruling, not an unrepairable defect.")
elif _kind == "inversion":
    _fault = (f"The native's surviving edition ({_nat_year}) postdates the "
              f"witness that displaces it ({_rep_year}), so it loses on "
              f"source_year before any tie-break is reached. Merging would "
              f"place (or has already placed) the earlier-dated witness in "
              f"the same group, where it still wins.")
    _standing = ("The override stands permanently: no tie-break rule can "
                 "reach a row that has already lost on year.")
elif _kind == "target_only":
    _fault = (f"The native ({_nat_year}) is earlier than the displayed row ({_rep_year}) but sits only on the "
              f"TARGET side of the group's rows, and the representative is chosen among source rows only, so "
              f"it cannot win on any year.")
    _standing = ("The override stands until the representative-row rule considers target-side documents.")
else:
    _fault = ("The relation between the native's year and the displayed "
              "row's could not be determined here, so the fault is recorded "
              "as observed rather than diagnosed: the page does not show the "
              "attribution.")
    _standing = ("The override stands unless the reason above is superseded "
                 "by a reading of the group.")
new_evidence = (
    f"{stamp}: native_override [{_kind}]. Native present at group(s) "
    f"{', '.join(str(c) for c, *_ in cand_info)} ({_basis}). {_fault} "
    f"{who}: \"{args.reason}\" {_standing} {args.note}".strip())
if evidence:
    new_evidence = f"{new_evidence}\n[superseded] {evidence}"

print("\n  new evidence:\n")
for line in new_evidence.splitlines():
    print(f"      {line}")

if not args.commit:
    print("""

  Dry run. Nothing written. Rerun with --commit.
""")
    sys.exit(0)

cur.execute(f"""UPDATE {args.prov}
                   SET native_status = 'native_override', evidence = %s
                 WHERE group_id = %s""", (new_evidence, args.group))
n = cur.rowcount
conn.commit()
print(f"\n  updated {n} provenance row(s)")

header = ["group_id", "status", "resolved_by", "attributed_author",
          "attributed_title", "attributed_year", "note", "passage_excerpt",
          "review_file"]
seen = set()
if os.path.exists(args.tsv):
    with open(args.tsv, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            seen.add((r.get("group_id"), r.get("review_file")))
key = (str(args.group), "record_native_override.py")
if key in seen:
    print(f"  {args.tsv}: already logged, not duplicated")
else:
    new = not os.path.exists(args.tsv)
    with open(args.tsv, "a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        if new:
            w.writerow(header)
        w.writerow([args.group, "native_override",
                    ",".join(str(c) for c, *_ in cand_info),
                    au, ti, yr, new_evidence.splitlines()[0], "",
                    "record_native_override.py"])
    print(f"  appended 1 line to {args.tsv}")

cur.execute(f"""SELECT native_status, COUNT(*) FROM {args.prov}
                 GROUP BY 1 ORDER BY 2 DESC""")
print("\n  native_status distribution now:")
for st, c in cur.fetchall():
    print(f"      {str(st):<22} {c:>4}")
print("""
  Rebuild the page so it reflects the ruling:

      python3 build_top_passages_page.py --out /path/to/site
""")
cur.close(); conn.close()
