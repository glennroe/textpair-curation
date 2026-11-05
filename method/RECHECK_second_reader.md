# Phase P second reading (t01) — read INSTRUCTIONS_P.md first; these checks apply its rules

You check a first reader's proposals. Read EVERY row shown, both S and T passages, yourself. No scripts to
classify, no sampling. Be independent: the first reader's note is a claim to test, not evidence.

## MOVE check (mc_K.txt -> mcv_K.tsv, header `group	row	dest	verdict	note`)
Each CASE shows a keeper group and one or more proposals to fold a group (WHOLE) or a single row (PART) into it.
One line per `>>> PROPOSED` line: `row` empty for a WHOLE-group proposal, the rowid for a PART row.
- AGREE    the rows PROVE it: the proposal's passage shares text with the keeper's, or visibly continues it
           (one row's passage runs on into the other's); OR both are parts of ONE poem, tirade, scene, or a letter/
           speech/article short enough to be quoted as a unit, and you can see from the text that it is the same unit.
- DISAGREE a different passage (a neighbouring paragraph of a long work, same topic, same chapter is NOT enough);
           or a translation proposed into a group fronted by its original-language text.
- UNSURE   you cannot tell from what is shown. Say why.
note: a few words of evidence (the shared words, or why not).

## Short-NOISE check (sn_K.txt -> snv_K.tsv, header `group	row	verdict	note`)
The first reader set these aside as too short. Apply the SHORT SPANS rule in INSTRUCTIONS_P.md (Glenn 22 Oct):
length is never the test. "Fuyez des mauvais sons le concours odieux" is reuse; "ayant aucune partie de pouvoir
exécutif" is noise. KEEP when the span's wording is AUTHORED (verse, figure, sententia, unusual collocation,
something a reader could name as a quotation), even if cut mid-clause. NOISE when it is the ordinary vocabulary of
a discourse (legal, constitutional, administrative, technical, devotional), a stock phrase, a bare list, or for
another scope reason (taxonomy, law as law, work aligned with itself).
One line per NOISE row for PART cases (row = rowid), one line with `row` empty for a WHOLE-group case.
verdict NOISE or KEEP. note: the span's key words and which test decided it.

## Fold check (fc.txt -> fcv.tsv, header `group	dest	verdict	note`)
Each CANDIDATE group may be the same unit as its keeper although the rows share no text. One line per candidate.
- FOLD   same poem / tirade / scene (a chorus of one scene) / short letter, speech or document, recognisable from
         the text shown (name the work and locus).
- APART  a different unit (another scene, another chorus, another document) or you cannot tell.

Finish by checking: one line per proposal/candidate/NOISE row, tab-separated, no extra columns.
