# TextPAIR curation pipeline

Code and reader instructions for the editorial curation of a large text-reuse database of French printed works, 1500–1800 (TextPAIR alignments, ModERN project, ERC grant 101043369). The database holds aligned passage pairs (rows) gathered into groups, each group one reused passage; curation decides, group by group, what is reuse and what is noise, which rows belong together, and which text is the source.

## How it runs

1. **Tranche dump** — the next batch of unread groups (2–9 rows) is dumped and compacted for reading.
2. **First readers** read every row of every group against the instructions in `method/` and give each group a verdict (KEEP, NOISE, PART, MOVE, EDITION) and, where they can, its source.
3. **Digest** — the readers' questions are merged for the editor, who rules; the rulings are written back into the instructions.
4. **Second readers** check every proposed move, fold, short NOISE and short KEEP call, and re-judge NOISE calls when a ruling changes.
5. **Compile** turns verdicts and checks into a row-level plan; **apply** sets rows aside or regroups them, and records what was read.
6. **Rebuild** the derived tables; **claims** record each group's source (author, work, first printing) and front overrides; the **native search** finds the group holding a source text the readers named; **joins** merge it.

Everything is read by people or by language-model readers working to the instructions; no step classifies text by script. Every write has a dry run first and a backup or ledger.

## The method (reader instructions)

- `method/INSTRUCTIONS_first_reader.md` — READ THIS FIRST (Glenn, 2–4 Nov 2026)
- `method/RECHECK_second_reader.md` — Phase P second reading (t01) — read INSTRUCTIONS_P.md first; these checks apply its rules
- `method/SHORTKEEP_second_reader.md` — Phase P — short-KEEP check (sk_K.txt -> skv_K.tsv), revised 3 Nov 2026
- `method/REVIEW_noise_calls.md` — Phase P t18 review of NOISE calls (rv_K.txt -> rvv_K.tsv) — Glenn's rulings of 4 Nov evening
- `method/NATIVE_search.md` — Phase P native joins (t01) — read INSTRUCTIONS_P.md first (scope, chunk rule, translations)

## Reading every small group

- `reading/dump_phaseP.py` — agent/dump_phaseP.py -- 22 Oct 2026. READ-ONLY. Complete reading, Phase P (groups of 2-9 live rows).
- `reading/build_P.py` — build_P.py -- Phase P batches: dump_<tag>.tsv -> p_<batch>.txt (one file per server batch), groups in front-file order. python3 build_P.py dump_t02.tsv                       full files (t01 format) python3 build_P.py dump_t02.tsv --compact [--out DIR] compact files (22 Oct streamlining test): within each group,     every document occurring in more than one row is printed once (d1, d2 ...) and ever
- `reading/cover_P.py` — cover_P.py p_NNNN.txt v_NNNN.tsv -- checks a Phase P verdict file against its batch.
- `reading/run_readers.sh` — agent/phaseP/run_readers.sh -- 27 Oct 2026. Phase P FIRST READERS, run headless on the server with Claude Code.
- `reading/build_rc.py` — build_rc.py DIR -- Phase P second-reader files for one tranche directory (p_*.txt + v_*.tsv).   mc_K.txt  every MOVE (whole group, or PART row to a group id): keeper block + proposing group block(s)   sn_K.txt  every NOISE called on SHORTNESS (note mentions short/fragment/brief/quotable): whole groups,             and the NOISE rows of PART groups whose note says so   fc.txt    fold candidates lis
- `reading/compile_P.py` — compile_P.py -- Phase P: v_*.tsv (first readers) + mcv_*.tsv (second readers on every MOVE) -> plan_P.tsv (rowid from_group comp action dest batch why), the format agent/partB_apply_21oct.py reads. A MOVE (whole group or PART row) is applied only when the second reader AGREEs (plus OVR below); otherwise the group stays (KEEP) / the PART row becomes its own NEW group. source lines -> sources_P.tsv.
- `reading/apply_tranche.sh` — agent/phaseP/apply_tranche.sh -- 27 Oct 2026. Apply one Phase P tranche plan, in the fixed order.
- `reading/apply_plan.py` — agent/partB_apply_21oct.py -- 21 Oct 2026. Applies PART B (the full-row reading of the tangled components: 232 batches, 80,670 rows, every row read) from the row-level plan compiled offline (agent/partB/compile.py):   agent/partB/plan_rows.tsv   rowid from_group comp action dest batch why      KEEP     stays where it is      MOVE     group_id := dest (an existing group: a native, or a group that k
- `reading/joins.py` — agent/partB_joins_21oct.py -- 21 Oct 2026. Part B phase 2, last step: joins between groups that are NOT natives of the phase-2 plan (phase-1 groups that carry one passage under two wordings, Glenn 21 Oct 12:41; a few "wrong-way" sources; the restored convocation letter). Dry run by default; --commit.

## Attribution: claims, natives, translators

- `attribution/claims_P.py` — agent/phaseP/claims_P.py -- 22 Oct 2026. Claims from the Phase P readers' `source` lines (agent/phaseP/claims_P.tsv: group author title year status latin reason), after the regroup is applied and the tables rebuilt.
- `attribution/find_native_P.py` — agent/phaseP/find_native_P.py -- 22 Oct 2026. READ-ONLY. For each claim held as "native_absent but the author has rows in the corpus" (agent/phaseP/claims_P_report.tsv), look for the NATIVE's own group: another live group that shares a witness document with the held group AT THE SAME PLACE (byte spans overlap on the same file, either side), and that holds at least one row whose author carries the 
- `attribution/dump_native_pairs.py` — agent/phaseP/dump_native_pairs.py -- 22 Oct 2026. READ-ONLY. For reading the native candidates before any join. IN  agent/phaseP/native_candidates_<tag>.tsv (find_native_P.py) OUT agent/phaseP/native_pairs_<tag>.txt : per held group, ALL its rows, then for each candidate group the rows that     share a witness byte-span with the held group (marked *) and, if the candidate is larger, the next rows 
- `attribution/locate_markers.py` — agent/phaseP/locate_markers.py -- 3 Nov 2026 (t16 translation claims, second pass). Read-only.
- `attribution/locate_in_file.py` — agent/phaseP/locate_in_file.py -- 3 Nov 2026 (t16 translation claims). Read-only.
- `attribution/pluche_backdate.py` — agent/phaseP/pluche_backdate.py -- 4 Nov 2026. Writes agent/phaseP/claims_t17p.tsv (claims_P format). Read-only on the DB.

## Core database tools

- `core/rebuild_derived_tables.py` — rebuild_derived_tables.py Rebuilds <table>_groups and <table>_ordered from the alignment table, with indexes and ANALYZE. Idempotent, and safe to run at any time.
- `core/carry_forward_tombstones.py` — carry_forward_tombstones.py Follow a provenance claim whose group was merged away to whatever is LIVE now, and record that in `resolved_by`. Dry run unless --commit.
- `core/record_attribution.py` — record_attribution.py Write ONE scholarly attribution into the provenance table. Dry run by default; --commit required.
- `core/record_native_override.py` — record_native_override.py Write a PERMANENT override to the database: the native is confirmed present, and no merge will ever make the representative-row rule show it. Dry run by default.
- `core/fix_document_year.py` — fix_document_year.py Correct `source_year` / `target_year` for one document, BY BYTE BAND. Dry run by default; --commit required. Nothing is ever deleted.
- `core/surname_key.py` — surname_key.py ONE definition of the surname key that `attributed_surname` stores and that the representative tie-break (representative.py) matches as an unanchored, case-insensitive substring of `source_author`. Import it; do not re-derive it.
- `core/corpus_source.py` — corpus_source.py One place that knows what "the corpus" means. Import it; do not re-derive it.
- `core/check_native_candidate.py` — check_native_candidate.py Does a located native edition actually contain the passage? STRICTLY READ-ONLY.
- `core/rewrite_author_variants.py` — rewrite_author_variants.py -- item 5: rewrite variant author strings to one canonical string per person (Glenn, 19 Oct 2026: "I'm happy to rewrite the strings at this point", superseding the 8 Sep authority-map ruling). MUTATING with --commit; dry run by default.
- `core/reading_ledger.py` — agent/reading_ledger.py -- 21 Oct 2026. The reading ledger: which rows a reader (Claude or an agent) has READ IN FULL, when, in which campaign, with what verdict. Coverage becomes a query instead of a guess.

## Requirements

Python 3, psycopg2, a PostgreSQL database in the TextPAIR schema; connection settings are read from a local configuration file, never stored in the code.

## Licence

MIT (code). The corpus, alignments and annotations are not included.
