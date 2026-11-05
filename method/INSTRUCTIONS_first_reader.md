# READ THIS FIRST (Glenn, 2–4 Nov 2026)

**Two errors to avoid, both serious.** (a) Keeping short passages of common words that are not actual reuse: stock phrasing, formulae (biblical, legal, liturgical), lists or strings of attributes (especially with figures), two writers stating the same thing in the standard words. (b) Throwing away real quotation because it is short or clipped: "lots of good stuff almost got swept away" (Glenn, 3 Nov) — La Fontaine's "va point sans soupirs. On fait beaucoup de bruit" was nearly called common words.

**So RECOGNITION COMES FIRST.** For every short span ask: is this part of a KNOWN text — a line or couplet of verse (La Fontaine, Boileau, Racine, Corneille, Molière, Voltaire…), a famous sentence, mot or maxim (Montaigne, Pascal, La Rochefoucauld, La Bruyère, Rousseau…), scripture quoted at a locus, a classical tag? The aligner often clips the start or end of a line; a clipped piece of a known text is still that quotation. If you recognise it, or the group's own rows show the same distinctive wording passing along a chain of witnesses, it is KEEP: say what the text is in the note. A dictionary quoting an author verbatim as a citation is a quotation: "a quote is a quote" (Trévoux quoting Bouhours, Sévigné, Vertot, Marivaux: KEEP).

**Only for spans nobody can place**, apply the three tests in order: (1) a quotable unit, not a fragment that merely contains some distinctive words; (2) more than common words, formula or list; (3) transmission, not convergence (independent translations of one ancient sentence that part where a translator must choose are convergence). A span that fails any test is NOISE, however exact; your note must say which test failed AND that you could not recognise the text.

# Phase P: reading every small group (2–9 rows) — ModERN / TextPAIR, French printed works 1500–1800 (22 Oct 2026)

Each row is one alignment between two documents: year, author and title of each side (S: source, T: target) and
the aligned passages (first 400 characters). A GROUP should hold ONE coherent passage and the rows that carry it:
a sentence or paragraph, a verse run, an anecdote, a letter, a speech; one poem / tirade / scene = one group.
The group's displayed author is its FRONT row (marked FRONT: the earliest year, ties broken by rowid). The front is
often wrong: a journal, anthology or refutation dated earlier than the work it quotes, or a late edition of the
work itself.

Groups in a batch are ordered by their front document and position in it, so neighbouring groups often come from
the same work: two groups may carry ONE passage split in pieces.

READ EVERY ROW YOURSELF, BOTH SIDES. No classifying scripts, no default verdicts, no sampling, no judging a group
by its first row or its FRONT label. A verdict on a group is a statement about every one of its rows.

## Your output: one TSV line per group, header `group	verdict	dest	rows	source	note`

- `KEEP`    every row is real reuse of the group's one passage; the group stays. dest, rows empty.
- `MOVE`    every row carries the SAME passage as another group of THIS batch (dest = that group's id): this group
            folds into it. The keeper gets KEEP. Pick as keeper the group fronted by the true source if there is one,
            else the one with most rows. Never MOVE into a group carrying a DIFFERENT passage, even a neighbouring
            sentence of the same work (unless both are parts of one poem/tirade/scene/letter — see the chunk rule).
- `NOISE`   every row is not literary reuse (scope below). dest, rows empty.
- `EDITION` every row has a LATIN passage with an edition or translation volume of its classical author on one
            side and a modern work on the other.
- `LATIN`   every row is Latin v. Latin between classical texts/editions/translations, or classical Latin v. a
            translation of it, or an ancient commentator/grammarian (Servius, Porphyrio, Donatus, Macrobius,
            Gellius) quoting a classical text.
- `PART`    the rows disagree. dest empty; `rows` lists EVERY rowid of the group, space-separated, as rowid:WHERE,
            WHERE = KEEP (stays), NOISE, EDITION, LATIN, a group id of THIS batch (moves there), or NEW:x (a real
            passage that has no group here; rows of one group with the same label become ONE new group).

`source` (optional, fill it ONLY when you are sure): when the FRONT row is NOT the true source of the passage and
you can name the source, give `author | work, locus | year of first printing | status`, status one of:
  `resolved` — the source's own text is one of the documents in this group (say which in the note);
  `first_printing` — the front document PRINTS the work whole for the first time (a periodical or collection
                     printing a poem, letter or song), not quoting it inside another text;
  `absent` — the source is not among the group's documents.
Leave `source` empty when the front is right, or when you are unsure. Never guess an author.
Years in `source` (Glenn 22 Oct): year 99 ONLY when the passage itself is in LATIN (the PHI convention). An
ancient text quoted in TRANSLATION goes to that translation: if the translation's own volume is among the
group's documents, name it (status resolved); otherwise name the translation and its first known printing
(a verse rendering such as Brébeuf's Pharsale is the translator's: "Brébeuf | La Pharsale, III | 1655"). If you
cannot tell WHOSE translation the French is, leave `source` empty and say so in the note. A translator's or editor's OWN commentary (Dacier's remarks on Horace, Mme Dacier's preface to the
Iliad) goes to the commentator, not to the ancient author shown on the document.
Scripture: Latin -> the Vulgate, French -> La Sainte Bible (the corpus's two Bible authorities); give book,
chapter and verse. Year 1450 for BOTH (never 99: the Vulgate is a printed book, not a PHI text).
Church Fathers and other post-classical Latin (Glenn 28 Oct): NOT 99 (PHI holds only classical Latin). Use the
Father's name and the year of his FIRST COLLECTED OPERA (never a 17th- or 18th-century edition): Augustin 1506
(Amerbach), Jérôme 1516 (Erasmus), Tertullien 1521 (Rhenanus), Bernard de Clairvaux 1508 (Paris), Ambroise 1492,
Cyprien 1520 (Erasmus), Grégoire le Grand 1518, Lactance 1465. For a Father not listed, give the earliest Opera you
know and say so in the note; if unsure, leave the year as '?' and say so. A Latin author of late antiquity who is
not a Father (Martianus Capella, Boèce) takes the first printing of the work (Capella 1499).
note: a few words naming the passage (author, work, locus when known) and the reason for the verdict.

NEW labels are local to a group (NEW:a in two different groups makes two new groups).

Check before you finish: exactly one line per group of your batch; every PART line lists every rowid of its
group exactly once; every MOVE/PART dest is a group shown in your batch.

## Scope (Glenn's rulings)

NOISE = not literary reuse:
- title pages, imprints, privilèges, approbations, catalogues, prospectuses, advertisements, prices;
  tables of contents and chapter headings (even reprinted in reviews); book titles circulating through reviews;
- legal / notarial / chancery / commercial / epistolary FORMULAS; stock phrases, lists, tables, numbers;
- the TEXT of laws, decrees, ordinances, arrêts, coutumes, treaties, constitutions and their articles, the
  Declaration of Rights, oaths, official addresses/arrêtés voted or issued by a body, administrative circulars,
  remedies and instructions issued by authority, court records — law circulating AS law;
- liturgy (offices, psalters, motets, catechisms, devotional manuals reproducing prayers or psalms);
- standard statements independent witnesses phrase the same way (definitions, theorems, bare anatomical/
  botanical descriptions, recipe stock phrases, independent translations of the same Latin): convergence, not
  transmission;
- academy prize-question announcements; heraldic blazons; descriptions of the insignia of orders of chivalry
  (cross, ribbon, collar, motto), even when copied verbatim from one book to another (Schmid -> Poncelin; Glenn 22 Oct); bare coin/medal legends; the Porte Saint-Denis
  inscription; the 1789 convocation règlement (the letter is KEEP);
- SHORT SPANS (Glenn 22 Oct: the hardest category, and the one reading every row exists for). Length is never
  the test. "Fuyez des mauvais sons le concours odieux" (4 content words) is reuse; "ayant aucune partie de
  pouvoir exécutif" (4 content words) is noise. Ask of the span itself:
    1. AUTHORED or IDIOMATIC? Marked wording (verse, metre, rhyme, figure, antithesis, an unusual collocation,
       a sententia) that points to ONE writer, versus the ordinary vocabulary of a discourse (constitutional,
       legal, administrative, technical, devotional) that any writer in it would produce.
    2. Could you NAME it? A reader of the period would recognise a quotation (Boileau, Art poétique I) -> KEEP;
       nobody could say whose words they are -> NOISE.
    3. A UNIT? A verse, a maxim, a proverb, a complete sentence, versus a stretch cut out of running prose
       mid-clause. A cut stretch can still be KEEP when its wording passes test 1.
  NOISE when it fails 1 and 2. KEEP when it passes 1 (a short marked line is reuse even if you cannot name it).
  TextPAIR cuts spans on common words and skips numbers, so a span often starts and ends mid-verse or mid-clause:
  judge the wording in the middle, never the ragged edges. Glenn's examples:
    "encor nous partager ses soins; il m'aimerait peut"     KEEP  (Racine; the verse is truncated, still reuse)
    "donner vingt coups de bâton sous la plante des pieds"  NOISE (generic usage, a number inside a stock phrase)
  OCR garbage is NOISE;
- a work aligned with ITSELF (Glenn 22 Oct): another copy or edition of it, the same book under another title,
  an author repeating his own sentence within ONE work (self-reuse across two DIFFERENT works stays KEEP); a
  mémoire or piece reprinted WHOLE in its author's later collection (Portal's Rapport in his Observations, Le Roy's
  Mémoires in his Mélanges) is a doublon of the same work (Glenn 22 Oct).
  A DOUBLON REQUIRES THE SAME AUTHOR ON BOTH SIDES (Glenn 29 Oct): two rows with the same text in two works by
  DIFFERENT authors are exactly the reuse this project looks for (a compiler, anthologist or controversialist
  reprinting another writer is KEEP, with the original as source). For texts with no author (edicts, acts,
  anonymous pieces) the test is the same SOURCE TEXT reprinted IN EXTENSO (a later reprint of the whole work);
  an extract or quotation of it is not a doublon;
- articles of coutumes, ordinances and laws quoted in jurists' briefs and treatises (bare legal text, Glenn 22 Oct);
- Masonic ritual reprinted in ritual collections (liturgy, Glenn 22 Oct) -- but a writer QUOTING it in argument
  (Barruel) is KEEP, like scripture quoted in argument;
- a row that merely pairs two INDEPENDENT translations of the same ancient text (convergence). Renderings that
  carry one source passage into French texts still fold together (see grouping rules);
- taxonomic nomenclature (Glenn 22 Oct): Latin diagnoses, genus/species characters, phrase names and synonymy
  citations ("Geoff. Ins.", "Linn. Syst. nat.") copied from Geoffroy, Linnaeus etc. into later naturalists. NOISE
  not for their length but because they function like liturgy or law: a formal system circulating as itself.
  A naturalist's own French DESCRIPTION or observation copied into another book stays KEEP.
- recipes and definitions in stock phrasing. A recipe, definition or description whose specific content shows it
  was COPIED from one book into another is KEEP (Glenn 22 Oct).
  A DESCRIPTION shared by two works is NOISE when all they share is the descriptive wording the subject imposes;
  it is KEEP only when the rows show CITATION or COPYING (the later work names the earlier, or reproduces it beyond
  what the subject imposes: the same order, the same particulars, the same wording over several sentences). Not a
  matter of word count (Glenn 31 Oct). A reprint of the SAME work is noise/doublon.

KEEP as real reuse:
- quotation, plagiarism, reprint or extract of literary, learned, scientific, historical or religious prose/verse;
- scripture QUOTED in argument; classical tags quoted in a modern work; proverbs (the Golden Rule); song refrains;
- LETTERS (even printed in official papers); SPEECHES by named speakers (kings' spoken words included), reports by
  a named rapporteur, remonstrances, academic harangues; papal letters;
- a legal text QUOTED IN ARGUMENT or paraphrased by a historian (Louis X's 1315 ordinance quoted against serfdom;
  the Strasbourg Oaths; Ulpian); an act of a body that quotes an author, where the aligned text is the author's;
- a description copied verbatim from one dictionary/treatise into another (shared ancestor = transmission);
  signed legal treatises copied jurist to jurist (not a bare rule restated);
- epitaphs and commemorative inscriptions; self-reuse across two works of one author;
- a row with a liturgical book on ONE side and a real quoter on the other.

Grouping rules:
- ONE COHERENT CHUNK = one group (Glenn 15 Oct, sharpened 22 Oct):
  * ONE group, even when the quoted lines are not adjacent: a poem, a tirade, a scene, and a letter, speech,
    article or sermon passage SHORT ENOUGH TO BE QUOTED AS A UNIT (a page or two).
  * VERSE, by length (Glenn 23 Oct): a poem of up to roughly 200 lines (ode, sonnet, héroïde, short épître,
    fable, song) is ONE group; a PSALM (in verse or in a psalter's prose) follows the same rule (Glenn 31 Oct),
    so Ps 118 and other long psalms fall under the long-work rule. VERSE THEATRE (Glenn 30 Oct): the unit is the TIRADE (one character's continuous
    speech, a récit included, however long); two tirades of one scene by different speakers are TWO groups. The
    SCENE is the unit only for short exchanges (stichomythia, rapid dialogue) or when the aligned rows themselves
    run across the change of speaker. Longer poems — long épîtres, verse tales (Griselidis),
    satires (Boileau, Regnard, Rochon), poems in cantos or chants (La Grâce, Loi naturelle), long descriptive poems
    (Les Alpes, La Chartreuse, Fontenoy) — follow the LONG-work rule below: passages fold only on shared text or a
    visible run-on.
  * PROSE, case by case (Glenn 30-31 Oct): an éloge of a page or two is ONE group; a longer éloge, discourse or
    plea follows the paragraph rule. The same holds for any short prose piece or short official text (an Esprit des
    lois chapter, a one-page declaration or arrêt, a short mémoire, letter, avertissement, a Bacon essay, a gospel
    pericope): a page or two is ONE group (Glenn 31 Oct). Two tirades or passages of a speech fold only if the rows overlap or run on.
  * LONG works (scientific memoirs, treatises, histories, long letters such as Bayle's Lettre sur la comète,
    long Encyclopédie articles, prefaces of many pages, books of aphorisms): the chunk is the PARAGRAPH, or a
    continuous run where the rows themselves show the text running on (one row's passage continues into the
    next's). Different passages of a long work stay SEPARATE groups, even from the same chapter or article.
  * MOVE only when the rows prove it: the two groups share text, or one's passage visibly continues the other's.
    Same work, same chapter, same topic is NOT enough.
- DIFFERENT WORDINGS or French RENDERINGS of the same source passage go in ONE group, even when the source is
  absent (Glenn 21 Oct). Exception: Henri IV's panache blanc stays two groups (Péréfixe / Voltaire).
- A TRANSLATION never joins a group fronted by its ORIGINAL-LANGUAGE text (Latin, Greek, English...).
- A translation is attributed to the original author, unless the reused text is certainly the translator's own.
- A work reprinted inside an anthology/collection is a witness, not the source.
- Leave DATES alone: no notes on wrong dates unless the date decides who the source is (then one short phrase).

## Dictionaries (Glenn 25 Oct)
Dictionaries do not belong in the BOOKS corpus. The reference dictionaries already sit in their own collection and are
read like any other witness, NOT flagged: Trévoux, the Encyclopédie and its Supplément (Robinet 1776), the Académie
dictionary, Savary's Dictionnaire universel de commerce, and the titled Encyclopédie méthodique volumes (Philosophie,
Arts et métiers, Beaux-arts, Théologie, Architecture, Manufactures, Encyclopediana, Assemblée constituante...). Olivier's
Insectes, Bruguière's Vers and Tableau encyclopédique, Valmont de Bomare, Sainte-Palaye's and Ragueau's Glossaires, Nau, Lapeyrère, Laplace's Maximes journalières, Magnien and (26 Oct) Aubin's Dictionaire de marine have
been set aside; Liger, Ladvocat, Colonia's Bibliothèque janséniste, the Vocabulaire austrasien, La Porte's Dictionnaire
dramatique and Lacombe's Dictionnaire portatif des beaux-arts are KEPT (do not flag them), and so (26 Oct) are Bayle's Dictionnaire historique et critique, Prosper Marchand's Dictionaire historique, Clément's Anecdotes dramatiques, the Petit dictionnaire de la cour et de la ville, Leroy's Traité de l'orthographe en forme de dictionaire, Borel's Trésor de recherches, the Dictionnaire walon-françois, Girard's Synonymes françois, Rémond de Saint-Sauveur's Calepin littéraire, Laplace's Introduction aux droits seigneuriaux, the 1797 Compendium des règles de la langue françoise and Coiffier de Verfeu's Dictionnaire biographique. Flag under FOR GLENN only OTHER volumes that are dictionaries in form (alphabetical articles), with the
title and year.

## Added for t15 (Glenn, 2 Nov 2026)

**Reprint v. reuse is not binary.** The doublon rule (NOISE) applies only when an ENTIRE prose text is reprinted elsewhere — a whole tale in an anthology (Cabinet des fées), an author's piece reprinted whole in his own later collection, one anonymous manual reprinting another in extenso. Verbatim passages copied into a different work are REUSE (KEEP), including compilers and geographers copying wholesale (e.g. the 1770 Voyage copying Lambert 1750), jurists transcribing Ferrière or Le Brun, rules copied into the Encyclopédie or Trévoux, recipe steps copied exactly. Poems are reprinted by nature and follow the poem rules. Exact copies that are only strings of attributes or lists (especially with figures) stay NOISE as shared vocabulary. A work recast under a new title by its own author (Du Tertre, Wicquefort, Barthélemy, Le Roy, La Porte, Boulanger) is self-reuse across works: KEEP.

**Amelot de La Houssaye's Tacite.** The volumes labelled "Tacite (0055?-0120?) | Tacite" or "Tacite avec des notes politiques et historiques", dated 1731 (modern_all / modern_all_pruned), are Amelot de La Houssaye's translation with his political notes, in an edition of 1731 or later that adds later notes. When the reused text is one of Amelot's own notes, give the source "Abraham-Nicolas Amelot de La Houssaye | Tacite, avec des notes politiques et historiques | 1683-1692 (first printing of the volume) | absent". When the note was added after 1706 (it quotes or cites a later work, e.g. the Lettres persanes 1721), leave it with the 1731 volume. When you cannot tell, leave the source empty and flag it FOR GLENN.

**Remedies.** Remedies or instructions printed by government or royal order (Chabert, Huzard, Helvétius's remèdes du Roi) and hospital formularies are NOISE. A signed physician's text copied exactly by another writer is KEEP.

**Native absent.** Never assume a work is absent from the corpus because its native is not in the group: the native may sit in another group. State "absent" only for works you know are not in the corpus; otherwise give the source and let the native search decide.

## Added for t16 (Glenn, 2–3 Nov 2026)
- An author's text reworked and republished inside another work is reuse (KEEP); only an entire work reprinted is a doublon (NOISE). "Esprit de…" collections are reuse.
- **Translations: the original author by default** (a translation of Cicero → Cicéron; of Hume → Hume; of Plato → Platon), with the translation's first printing. Only exceptional literary translations go to the translator on the Brébeuf model (Brébeuf, La Pharsale de Lucain; Boileau's Longin; La Motte's Iliade). The translator's own notes, prefaces and discourses go to the translator.
- Judicial records (arrêts against persons, condemnations, sentences) NOISE. Scripture compilations, catechisms, prayer books (incl. the Book of Common Prayer) NOISE in every row. Phrase-book dialogues NOISE. Addresses voted by a body NOISE. Diplomatic letters: KEEP + out_of_scope.
- Parallel Gospel passages (Matthew / Mark / Luke on one episode) are different versions: separate groups, never a MOVE. The Song of Songs is a long work. A five-word incipit is NOISE.
- Dictionaries: exact copying of real passages KEEP; short definitions NOISE.
- Dates: a volume whose contents postdate its date (wrong front) — flag FOR GLENN with the title page if visible; a file carrying several parts of different years — flag for a band split.
- Before giving a source as "absent", remember the native may be in another group or catalogued under another name (translations under the ancient author; titles in capitals): when unsure, give the source without "absent".

## Added for t17 (Glenn, 3–4 Nov 2026)
- **Overlap is the key to grouping.** Two groups go together (MOVE, or a FOLD CANDIDATE) only when their passages OVERLAP: the rows share text, or one row's span visibly runs into the other's. Distinct passages with no overlap stay SEPARATE groups, even inside one poem, one fable, one tirade or one speech. Never MOVE verse on "same poem" alone. A maxim or moral detached from a fable and quoted on its own goes to the fable's group when the fable's group carries it.
- **Prose short units** — an anecdote, a short letter, a caractère, a fable in prose — are one unit when the rows run on; otherwise the overlap rule applies.
- **Paratext is always NOISE**: tables of matters, indexes, avertissements and notices reprinted with the work, running heads, lists of contents.
- **A whole short prose piece reprinted by another compiler** (an Avertissement, a prose fable standing entire in an anthology) is a doublon: NOISE. A short fable or poem in VERSE quoted or reprinted is reuse (poems are reprinted by nature).
- **Proverbs:** KEEP when the row carries it as quoted; give a source only when it can be traced to a written text (a fable → that fable). Otherwise leave the source empty; do not invent one.
- **Translations (ruling 5, restated):** the original author with the translation's first printing; Brébeuf's Pharsale, Boileau's Longin, La Motte's Iliade, Benserade's rondeaux and Corneille's Imitation are translator exceptions. When a translation volume mixes several authors (Holbach's Art de la verrerie = Neri + Merret's observations + Kunckel's remarks and second part; Holbach's Minéralogie = Wallerius + Holbach's notes; Diderot's Essai = Shaftesbury + Diderot's notes; La Bruyère's Théophraste + Discours), say which part the passage is in if you can see it, otherwise give the volume and "part unclear".
- **Raynal:** the Histoire des deux Indes is in the corpus only as the 1780 edition; a passage in it with a witness before 1780 is claimed to Raynal 1770 at the claims stage — leave the source empty unless it is not Raynal's text (Diderot's Fragments 1772, the Nakaz 1774, de Pauw).
- **Back-dating by claim:** the Plutarch volumes now dated 1762 are Dacier's translation (Vies 1721); Amelot's Tacite notes 1683–1692 (as above). Give these first-printing years in `source`.

## Added for t18 (Glenn, 4 Nov 2026)
- **Fragments:** a short or clipped span that can be traced to an authorial text is KEEP (name the text in `source`); an untraceable fragment of common words is boilerplate NOISE. Recognition first: if you know the text, it is KEEP.
- **Quoted in argument:** anything a writer quotes in argument (a clause of a law, an article of a treaty, a line of an ordinance, a maxim) is KEEP whatever its size; add `out_of_scope` in the note when the quoted text is legal, commercial or diplomatic. A collection or digest that PRINTS the act as text (a recueil of edicts, a code, a treaty collection) is NOISE.
- **Commercial usance and tables:** rules of usance, exchange or days of grace stated with figures, tariffs, tables of weights and coins, lists of prices are NOISE.
- **Same author repeating himself (rule b):** an author repeating his own text in technical, expository or economic prose — later editions, reissues, expanded or retitled versions of the same treatise — is a doublon: NOISE on the rows that pair the two versions. A LITERARY author reworking his text (Voltaire's Dictionnaire philosophique → Questions sur l'Encyclopédie) stays KEEP. "Esprit de …" anthologies made by other hands are reuse (KEEP), not doublons.
- **No double counting:** when a third witness is aligned with two volumes or editions of one author's repeated text, keep only its row to the EARLIEST volume; the row to the later volume is NOISE (say "double count" in the note).
- **Translations:** a row aligning two complete translations of the same work is NOISE. A writer quoting one translation stays KEEP, with the original author as source.
- **Dates:** the corpus date stands unless there is evidence it is wrong (the volume quotes or cites a later work, names a later edition, or its contents postdate the date). Only then flag FOR GLENN, with any title-page wording you can see; a corrected date is taken from the title page. Do not guess a year.
- **Esprit de Raynal** is the 1782 edition, not 1777. The Histoire des deux Indes rule above stands (claims stage).
- **Encyclopédie articles** are not split by contributor (no d'Alembert / Jaucourt sources for Encyclopédie text); the Encyclopédie volume is the witness.
- **Diderot** is the source for his own passages (Miscellanea, Fragments, contributions printed under Raynal's name) whatever the date of the volume carrying them.
- **Pluche, Spectacle de la nature:** the corpus files are the Estienne reissue (1752–1755); first printings are t.1 1732, t.2–3 1735, t.4 1739, t.5–7 1746, t.8 1750. When Pluche's own prose is the source, give that first-printing year. When Pluche QUOTES (Scripture, verse, Réaumur's or another author's text in his own words aside), the source is the quoted author.
- **Prévost, Histoire générale des voyages:** a compilation; when it copies an earlier travel account (Ulloa, Frézier, Labat, Weber), the source is that account; when the account is in the corpus only after Prévost, still name it (claims will decide). Gumilla's Orénoque: leave Prévost (1756) in front.
- **Dictionaries kept (4 Nov):** Abot de Bazinghen's Traité des monnoies, Paganucci's Manuel des négociants, Bellet-Verrier, Léris and La Croix stay (do not flag). The 1761 trilingual Encyclopédie is set aside (NOISE).
