# Phase P — short-KEEP check (sk_K.txt -> skv_K.tsv), revised 3 Nov 2026

Glenn: "the most pernicious form of noise is just short passages that repeat common words and aren't actual reuse" — AND (3 Nov) "lots of good stuff almost got swept away". Every group in your file was KEPT by the first reader and its longest aligned span is short. Your job is to catch KEEPs that are really common-word matches, WITHOUT sweeping away clipped quotations of known texts.

Read EVERY row of EVERY group, both S and T. No sampling, no scripts to classify.

**Step 0 — recognition comes first.** Ask: is this span part of a KNOWN text — a line or couplet of verse (La Fontaine, Boileau, Racine, Corneille, Molière…), a famous sentence or mot (Montaigne, Pascal, La Rochefoucauld, Rousseau, Voltaire…), a maxim, a proverb, a verse of scripture quoted at a locus? The aligner often clips the start or end of a line: a clipped piece of a known line is still that quotation. If you recognise it, or the group's own rows show the passage is being copied (same distinctive wording in a chain of witnesses), it is KEEP — Glenn 2 Nov: fragments of passages demonstrably copied are KEEP. Proverbs with a written tradition are KEEP (claim native_proverbial). Say what the text is in the note.

**Only for spans nobody can place,** apply the three tests in order:
1. Quotable unit — would anyone quote these words as a unit?
2. More than common words — not stock phrasing, a formula recurring at many loci (biblical blessing/regnal/narrative formulas, legal or liturgical formulae), a bare list or string of attributes (especially with figures).
3. Transmission, not convergence — the witnesses share an ancestor; independent translations of one ancient sentence that part where a translator must choose are convergence (NOISE).

Output skv_K.tsv, header `group	row	verdict	note` (row empty for a whole-group verdict). verdict KEEP or NOISE; for NOISE say which test failed AND confirm you could not recognise the text. Report counts and the cases Glenn should see.
