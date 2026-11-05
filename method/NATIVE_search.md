# Phase P native joins (t01) — read INSTRUCTIONS_P.md first (scope, chunk rule, translations)

Each HELD group was claimed by a first reader to a source author ("claimed: ..."), with the native judged absent
from the group. A search found CANDIDATE groups that share a witness document with the HELD group at the same
place (rows marked * share a byte span of that witness) and contain rows by the claimed author. Your job: decide,
by READING the passages, whether the HELD group's passage is the SAME passage as a candidate's — the native's
own group — so the held group should fold into it.

Read EVERY row shown, both S and T passages. No scripts to classify.

Output npv_K.tsv, header `held	cand	verdict	rows	note`, ONE line per CANDIDATE shown:
- JOIN  the HELD group's passage is the candidate's passage (shared text, or one passage visibly continuing the
        other, or both parts of one poem / tirade / scene / short letter or speech — see the chunk rule). The whole
        HELD group folds into this candidate. At most ONE JOIN per HELD group: if several candidates carry it, JOIN
        the one whose rows best carry the HELD passage (usually the one fronted by the claimed author) and say in the
        note which others also carry it.
- ROWS  only some HELD rows carry the candidate's passage; list them in `rows` (space-separated rowids); the other
        HELD rows stay.
- NO    a different passage (a neighbouring paragraph of a long work is NOT the same passage — e.g. two different
        letters of Julie, two different paragraphs of Émile), or the candidate is the ORIGINAL-LANGUAGE text of a
        translation (a translation never joins its original), or you cannot tell.
note: the shared words or the reason. If a candidate itself looks conflated (several unrelated passages), say so.

Finish: one line per CANDIDATE block, 5 tab-separated fields.
