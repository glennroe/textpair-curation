# Phase P t18 review of NOISE calls (rv_K.txt -> rvv_K.tsv) — Glenn's rulings of 4 Nov evening

You check NOISE calls the first readers made under two rules Glenn has now narrowed. Read EVERY row shown (S and T passages) yourself; no scripts, no sampling. The first reader's note is a claim to test.

Glenn's rulings on the t18 digest (4 Nov):
1. **Literary reuse is always KEEP.** An author repeating a passage in a DIFFERENT work of his own is KEEP (self-reuse across works), whether literary or technical. Partial incorporation, citation or quotation of a text in another work is KEEP. Only a FULL REPRINT of a text — the same work again: a later edition, a reissue, a second copy of the same book or of the same volume in the corpus, an entire piece reprinted whole — is a doublon: NOISE. Duplicate copies of one text go: when a third witness is aligned with two copies/editions of the SAME work, keep its row to one copy (the earliest) and the row to the other copy is NOISE.
2. **Legal and revolutionary texts: when in doubt, KEEP with out_of_scope** (verdict OOS), not NOISE. NOISE only when the row is plainly one printing of the act against another printing of the act (both sides collections/editions/digests printing the text, no argument), or a bare list/tariff/figures.
5. One text under two authors' names in the corpus (Anti-Machiavel/Examen, Condorcet's Bibliothèque reprinting Voltaire, Observateur/Espion anglois, Bachaumont/Mairobert, Voltaire's Essay/Essai): all literary reuse, KEEP.
Unchanged: paratext, lists/figures/tariffs, stock formulas, short untraceable fragments stay NOISE. A row pairing two complete translations of the same work stays NOISE.

Each CASE gives a group (its rows as in the first reading) and a QUESTION line naming the rows the first reader set aside and why. Decide for each named row (or the whole group if the QUESTION says WHOLE):
- KEEP  — different works, literary reuse, partial incorporation, quotation; or (two-author cases above).
- OOS   — legal/revolutionary text where there is doubt (one side quotes or argues from it, or you cannot tell it is printing v. printing).
- NOISE — a full reprint / second copy or edition of the same work (say which two documents), printing v. printing of an act, or a class that stays NOISE (paratext, list, formula, untraceable fragment, two complete translations).

Output rvv_K.tsv, header `group	row	verdict	note`: one line per named row (row = rowid), or one line with row empty for a WHOLE case. note: a few words — the two documents and why (e.g. "Voltaire Essai 1756 v. Questions 1771: different works", "1735 and 1756 editions of Sanadon's Horace: same work", "Jousse quotes art. 4 in argument").
Finish by checking that every named row has exactly one line.
