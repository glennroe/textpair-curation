#!/usr/bin/env python3
"""compile_P.py -- Phase P: v_*.tsv (first readers) + mcv_*.tsv (second readers on every MOVE) -> plan_P.tsv
(rowid from_group comp action dest batch why), the format agent/partB_apply_21oct.py reads.
A MOVE (whole group or PART row) is applied only when the second reader AGREEs (plus OVR below);
otherwise the group stays (KEEP) / the PART row becomes its own NEW group. source lines -> sources_P.tsv."""
import csv, os, glob, re, sys
from collections import Counter, defaultdict
csv.field_size_limit(sys.maxsize)
rows = defaultdict(list); batch = {}
for f in glob.glob("p_*.txt"):
    b = f[2:6]; g = None
    for l in open(f, encoding="utf-8"):
        m = re.match(r"--- GROUP (\d+)", l)
        if m: g = m.group(1); batch[g] = b; continue
        m = re.match(r"\s+(?:FRONT )?row (\d+) \|", l)
        if m: rows[g].append(m.group(1))
chk = {}
for f in glob.glob("mcv_*.tsv"):
    for r in csv.reader(open(f, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
        if not r or r[0] == "group": continue
        r += [""] * 5; chk[(r[0].strip(), r[1].strip())] = r[3].strip()
# Glenn / my calls on second-reader UNSUREs (22 Oct)
OVR = {("300018080", ""): "AGREE"}          # Toussaint, AMOUR CONJUGAL: a short Encyclopédie article = one unit
EXTRA_ROW_MOVES = {"1158673": "300029447"}  # Bacon/Deleyre: the one row that shares the keeper's aphorism
TAG = sys.argv[1] if len(sys.argv) > 1 else "P"
OVR0 = OVR
if TAG != "P": OVR = {}; EXTRA_ROW_MOVES = {}
if TAG == "t15":  # Glenn 2 Nov: parallel Gospel passages are different versions, not one passage
    OVR = {("11200018022", ""): "DISAGREE", ("10300005517", ""): "DISAGREE"}
if TAG == "t16":  # Glenn 3 Nov: distinct verse passages with no overlap stay separate groups (the overlap is key); maxims to their fable's group allowed
    OVR = {("11200307176", ""): "DISAGREE", ("11200307304", ""): "DISAGREE", ("10300010832", ""): "DISAGREE", ("11200036109", ""): "DISAGREE", ("10300010844", ""): "DISAGREE", ("10300010845", ""): "DISAGREE", ("10300010851", ""): "DISAGREE", ("10000000761", ""): "DISAGREE", ("10300010900", ""): "DISAGREE", ("300012758", ""): "DISAGREE", ("11200036171", ""): "DISAGREE", ("11200036173", ""): "DISAGREE", ("11200036179", ""): "DISAGREE", ("10300010920", ""): "DISAGREE", ("300013185", ""): "DISAGREE", ("11200314718", ""): "DISAGREE", ("10000000766", ""): "DISAGREE", ("10300010942", ""): "DISAGREE", ("11200036230", ""): "DISAGREE", ("10300010969", ""): "DISAGREE", ("10300010975", ""): "DISAGREE", ("10300010982", ""): "DISAGREE", ("10300010992", ""): "DISAGREE", ("11200314721", ""): "DISAGREE", ("11200314720", ""): "DISAGREE", ("300014830", ""): "DISAGREE", ("300014189", ""): "DISAGREE", ("11200029670", ""): "DISAGREE", ("10300017315", ""): "DISAGREE", ("10300017320", ""): "DISAGREE", ("10300142632", ""): "DISAGREE", ("300010109", ""): "DISAGREE", ("10300082196", ""): "DISAGREE", ("10300082197", ""): "DISAGREE", ("10300062340", ""): "DISAGREE", ("10300018166", ""): "DISAGREE", ("11200313593", ""): "DISAGREE", ("11200313606", ""): "DISAGREE", ("11200057520", ""): "DISAGREE", ("10300142568", ""): "DISAGREE", ("10300018177", ""): "DISAGREE", ("10300018180", ""): "DISAGREE", ("11200108189", ""): "DISAGREE", ("11200108191", ""): "DISAGREE", ("11200108192", ""): "DISAGREE", ("11200108193", ""): "DISAGREE", ("11200108194", ""): "DISAGREE", ("11200108198", ""): "DISAGREE", ("11200036218", "1835075"): "DISAGREE"}
if TAG == "t01":  # my calls on second-reader AGREEs that rest on topic, not text (MOVE only when rows prove it)
    OVR = {("900253957", ""): "DISAGREE", ("900246609", "449696"): "DISAGREE", ("600019262", ""): "DISAGREE",
           ("600003035", ""): "DISAGREE", ("1500247159", ""): "DISAGREE"}
if TAG == "t02":  # my calls on second-reader AGREEs that rest on topic in a long work, not on text (Buffon, Clermont-Lodève)
    OVR = {("900124100", ""): "DISAGREE", ("900299773", ""): "DISAGREE", ("1200106730", ""): "DISAGREE"}
    # Glenn 22 Oct: Rochon de Chabannes, Satyre sur les hommes (1758) is too long for 'one poem = one group';
    # group its passages by shared text only. The Alexander passage (vainqueur de l'Asie ... l'enceinte du monde)
    # is carried by five groups -> keeper 900143234; every other passage stays its own group.
    for g in ("900118453", "900143233", "900118458", "900280359", "900143234", "900144884", "900279157", "900291022", "900143236"):
        OVR[(g, "")] = "DISAGREE"
    for r in ("339369", "339775", "339370"): OVR[("900143239", r)] = "DISAGREE"
    # UNSURE whole-group moves where only some rows share the keeper's text: move those rows alone
    EXTRA_ROW_MOVES = {"698985": "1500081961", "699009": "1500081961",   # Marguerite de Valois, "cavalier d'honneur"
                       "858991": "300053604", "797029": "900010920",
                       "486964": "900143234", "486965": "900143234", "341161": "900143234", "341162": "900143234",
                       "485781": "900143234", "485782": "900143234", "497297": "900143234", "497298": "900143234"}
if TAG == "m1":  # Bossuet, Henriette-Marie: portrait rows fold to 10300011125; "prendre la multitude" (562076-80) stays its own group
    OVR = {("1200015291", ""): "DISAGREE"}
    EXTRA_ROW_MOVES = {r: "10300011125" for r in ("562068", "562069", "562070", "562071", "562072", "562073", "562074", "562075", "989201", "989202")}
if TAG == "t03":  # Glenn 23 Oct: LENGTH decides, not genre -- Colardeau's Héloïse and Armide run past 200 lines: fold only on shared text
    OVR = {(g, ""): "DISAGREE" for g in ("900191854", "900228070", "11200322532", "11200322531", "900191856", "900191857", "1200147425",
                                         "1200146070", "900118075", "900191862", "900191864", "900118467", "900190356", "900118468",
                                         "900118469", "900118470")}
    for r in ("485071", "485072", "485073"): OVR[("900278628", r)] = "DISAGREE"
    EXTRA_ROW_MOVES = {"485071": "900228070", "485072": "900228070"}  # "L'amour n'est point un crime": shares text with 900228070
if TAG == "t04":  # my calls on second-reader verdicts (24 Oct): MOVE only when rows prove it; verse only when shown short
    OVR = {(g, ""): "DISAGREE" for g in ("300024507",            # Keill, long treatise, no overlap
                                         "900223953", "900186049",  # Palissot notices: rest on the name only
                                         "900022192", "300011511", "300006720", "300007964", "300008434",  # Du Cerceau, length not shown
                                         "900186272", "900186273")}  # Desmarais ode, length not shown
    for r in ("870038", "941140"): OVR[("1500185944", r)] = "DISAGREE"  # Louis XI maxim: vocabulary only
    # Profession de foi, Gospel/Socrates-Jesus: one paragraph quoted as a unit (m1 gathered it under 1500209274)
    for g in ("1200099518", "1200143410", "900271298", "600037898", "900207628", "11200322256",
              "1500197631", "1500197661", "1500197662", "1500197663", "1500197665"): OVR[(g, "")] = "AGREE"
    EXTRA_ROW_MOVES = {"169092": "900118380",   # Aymar: the one row sharing the keeper's text
                       "808904": "1500151780"}  # Misson, Naples marbles: shares the keeper's text
if TAG == "t05":  # my calls (25 Oct): unsure whole-group moves -> only the rows that share the keeper's text move
    EXTRA_ROW_MOVES = {"405059": "1500169377", "290042": "1500169377",       # Guénard: rows sharing the keeper's passage
                       "127382": "1200147459", "127383": "1200147459",       # Bossuet, Discours sur l'hist. univ., conclusion
                       "286514": "1500165951", "286515": "1500165951",       # d'Alembert 1754: rows sharing "lumière générale"
                       "490976": "900077563", "490977": "900077563", "490978": "900077563"}  # Ésope à la cour, the governor scene
if TAG == "t06":  # my calls (25 Oct): MOVE only when rows prove it
    OVR = {("900258516", ""): "DISAGREE"}  # Rigoley: only row 462957 shares the keeper's text; the rest is later in a long extract
    LEBRUN_LONG = False  # Glenn 25 Oct: Lebrun, Ode patriotique 1792 is a 4-page poem -> one poem, one group
    if LEBRUN_LONG:
        for g in ("1200139650", "900326481", "900326482", "900326483", "900326438", "900326488",
                  "900326943", "900326486", "600047476", "900326487"): OVR[(g, "")] = "DISAGREE"
    EXTRA_ROW_MOVES = {"462957": "900257740",                                    # Rigoley, the shared row
                       "195909": "11200326454", "354632": "11200326454",         # Baillet, Vie de Richer: the run-on rows
                       "826592": "11200326454", "195905": "11200326454"}
if TAG == "t07":  # my calls (25 Oct): MOVE only when rows prove it
    OVR = {(g, ""): "DISAGREE" for g in ("300055339", "300055345", "300055348")}  # Scioppius' letter on Bruno: 2-3 pages, no shared text
    OVR[("1500232933", "988709")] = "DISAGREE"  # Buffon: run-on rests on recollection, not on the rows
    EXTRA_ROW_MOVES = {"789802": "300019663", "47571": "300019663"}  # Simon, Greek nuns: shared text / visible run-on (47570 stays)
if TAG == "t08":  # Glenn 26 Oct: Boileau's Discours au Roi follows the long-work rule (mc_0 already DISAGREE; kept explicit)
    OVR = {(g, ""): "DISAGREE" for g in ("1200095885", "1500054534", "900021147",
                                         "900229599", "1200081261")}  # Marguerite, St Bartholomew: long work, joined only by quoters' extracts
if TAG == "t09":  # my calls (27 Oct) on mc_0's four DISAGREEs: split by the rows that share text
    OVR = {(g, ""): "DISAGREE" for g in ("900157601", "900234722", "900043765")}
    OVR[("900157614", "355316")] = "DISAGREE"
    EXTRA_ROW_MOVES = {"355268": "1200013626", "355279": "1200013626",   # Hermant detractor/tyrant rows (355266/355267 are Annales doublons)
                       "436246": "900259729", "436248": "900259729",     # Joconde: the two rows sharing the Dissertation's text
                       "457297": "900252276"}                            # Voltaire's verse reply to Boufflers (fc_2)
if TAG == "t10":  # my calls (29 Oct): Hutcheson, long work, inferred run-on only; Pliny HN II.7 = two independent translations
    OVR = {("1500215830", ""): "DISAGREE", ("1200119810", ""): "DISAGREE"}
if TAG == "t11":  # Glenn 31 Oct: the 4th of the Five Propositions -- row 43004 (Latin + start of French) stays with the Latin group (ROW_KEEP)
    OVR = {}
if TAG == "t12":  # my call (31 Oct): Terpsichore / Lucile couplets, same metre, scheme and witnesses = one short song
    OVR = {("1500241667", ""): "AGREE"}
if TAG == "t01":  # fold check found the four II.8 Esther chorus groups are one chorus; row 497938 ends the I.5 chorus
    EXTRA_ROW_MOVES = {"497938": "900291568"}
# my calls applying Glenn's rulings to first-reader verdicts, per tranche
VERDICT_OVR = {"t01": {g: "NOISE" for g in ("900141689", "1500191174", "900142946")},  # Geoffroy's order characters: taxonomic system (22 Oct)
               "t02": {g: "NOISE" for g in ("1200058254", "1200058259")},  # Glenn 22 Oct: Masonic songs only reprinted from collection to collection
               # Glenn 23 Oct: official acts quoted in argument are KEPT and claimed out_of_scope (1791 Constitution at the king's trial)
               "t07": {g: "NOISE" for g in ("1500063281", "900218674", "900218679")},  # Glenn 25 Oct: Jean II's Order of the Star (1351) is a statute
               "t05": {g: "KEEP" for g in ("600042455", "600037668", "600045127", "600037752", "600039580", "600039882",
                                            "11200308568", "600044813", "600044890", "600040121", "600038393")},
               "t08": {g: "NOISE" for g in ("1200147217", "600063698")},
               "t10": {g: "KEEP" for g in ("600008350", "1200112003", "1500204243")},  # Glenn 27 Oct ruling 21: Lamoignon's Arrêtés are a jurist's work
               "t11": {g: "KEEP" for g in ("900248671", "300008524")},  # t11 item 150: historians (Pitaval, Hélyot) quoting an act = KEEP (out_of_scope)
               "t13": {g: "NOISE" for g in ("1500184890", "1500184892", "1500184893", "1500184895", "1500184897", "1500184898",  # Glenn 1 Nov (6): La Monnoye's office hymns = liturgy
                                             "1500184684",   # Doncourt's cantique, carried only by cantique books
                                             "1500153227",   # Glenn 1 Nov (8): Daran's testimonials = advertisement
                                             "600026096")},  # Faure de Beaufort / Lannoy = promotional
               "t16": {g: "NOISE" for g in ("11200230871",)},  # Glenn 3 Nov: Raynal's table of matters = paratext, always NOISE
               "t15": {g: "NOISE" for g in ("11200211401",   # Catherine II's manifesto printed whole (reprint)
                                             "11200253293",   # Parlement's condemnation of Boncerf (judicial record)
                                             "600048938", "600048939", "600048945", "600048947",  # the 1792 address against royalty, voted by a body
                                             "11200019615")},  # Glenn 2 Nov (11): five-word Gospel incipit = NOISE
               "t14": {**{g: "NOISE" for g in ("600050513", "600050476", "600050510", "600050471", "600050632", "600050409", "600050316",  # Glenn 2 Nov (5): the 1795 Débats set aside as a judicial record
                                               "900311978",   # edict of 1681 restated by jurists / reported in Le Point du jour (item 82)
                                               "600041624", "1500276218", "1500276221", "1500276223",  # Glenn 2 Nov (6): Chabert's Instruction printed by government order
                                               "900141021")},  # Helvétius's remèdes du Roi, distributed by royal order
                       "600008305": "KEEP", "900250822": "KEEP"},  # Romans mémoire argues from the péage clause (out_of_scope); La Bourdonnais restored for its fold  # Faure de Beaufort's remedy pamphlets / Lannoy = promotional
               # Glenn 27 Oct: official acts argued from by a named writer are KEPT (out_of_scope claim); treatise-to-treatise and chancery formula stay NOISE
               "t09": {**{g: "KEEP" for g in ("600004620", "1500125703", "1500125722", "600064987", "1500077075", "900157135", "300027817")},
                       "300043392": "KEEP"},  # Lafosse dropsy causes: part of the short article (fc_1 fold)  # Glenn 26 Oct: Year III Declaration of duties art. 2 is the Declaration, not the Golden Rule
              }.get(TAG, {})
chk.update(OVR)
# short-NOISE second reading: (group,"") or (group,row) -> KEEP restores
snk = set()
for f in glob.glob("snv_*.tsv"):
    for r in csv.reader(open(f, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
        if not r or r[0] == "group": continue
        r += [""] * 4
        if r[2].strip() == "KEEP": snk.add((r[0].strip(), r[1].strip()))
SNK_OVR = {"t01": {("1500191177", ""), ("1500191363", "")}}.get(TAG, set())  # Geoffroy anatomical fragments: technical vocabulary (test 1 fails)
snk -= SNK_OVR
if TAG == "t12":  # exact but only strings of attributes = shared vocabulary (Glenn 31 Oct: exact copy, not shared vocab)
    snk -= {(g, "") for g in ("1500203138", "1500203143", "1500203176", "1500203018")}
if TAG == "t11":  # Glenn 31 Oct ruling 4: a description copied by another writer (not a reprint of the same work) is reuse
    snk |= {(g, "") for g in ("300014606", "300016256", "300009130", "300012577", "300006349", "300009418", "300016821", "300015540",  # Nouvelle instruction -> Trévoux
                              "300012841", "300008439",  # La Quintinie -> Trévoux
                              "1200129293", "1200129303", "1200129260", "1500231848", "1200129259", "1200129269", "1200129310")}  # Le Berryais -> Jolyclerc / 1782
if TAG == "t14":
    snk -= {("900264606", "918335")}  # Glenn 2 Nov (6): the Hôtel-Dieu formulary v. the 1780 hospital formulary = official remedy, NOISE stands
    snk |= {(g, "") for g in ("900053660", "1200132023", "600039685",
                              "1500151845", "1500151802", "1500151788")}  # Glenn 2 Nov: the 1770 Voyage copying Lambert 1750 verbatim = reuse
snk |= {"t04": {("11200319247", "1732571"), ("11200319247", "1732572")}}.get(TAG, set())  # pieces of the group's own passage
if TAG == "t16": snk |= {(g, "") for g in ("10300015479", "10300015486", "10300015549")}  # Glenn 3 Nov (9): Trévoux quoting Bouhours verbatim, "a quote is a quote" = KEEP
NEW_RELABEL = {"t02": {"978897": "P300042376:c"},
               "t11": {"457703": "P900253951:a", "457704": "P900253951:b", "100558": "P600010075:a"},
               "t13": {"701671": "P900293408:a"}}  # Henri IV, one letter carved twice  # t11 item 174: one passage carved twice (Papon marbles; 1615 declaration)
NEW_RELABEL = NEW_RELABEL.get(TAG, {})  # t02 Pegasus diagonals: same passage as 300042376 NEW:c
SAME_PASSAGE = {"t01": {"2111806"}, "t04": {"1732571", "1732572"}}.get(TAG, set())  # restored PART rows that carry the group's own passage
# fold check: group -> dest
fold = {}
for f in glob.glob("fcv.tsv"):
    for r in csv.reader(open(f, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
        if not r or r[0] == "group": continue
        r += [""] * 4
        if r[2].strip() == "FOLD": fold[r[0].strip()] = r[1].strip()
if TAG == "t03": fold.update({"900088850": "1500086790", "900102096": "1200106776"})  # Boileau Sat. XII: refused into the keeper, but each pair shares text
if TAG == "t04":  # refused folds: Grégoire's 15-page letter is not a short unit; La Motte fold rests on metre alone
    for g in ("1200136252", "1200136253", "1200136254", "600034591", "1200136256", "1200136258", "900120971"): fold.pop(g, None)
if TAG == "t06":  # refused folds: subject only, or long work without visible run-on; Richer moves by row (EXTRA_ROW_MOVES)
    for g in ("300010349", "300019886", "1500032684", "1500032685", "900026658", "900328913", "300007069"): fold.pop(g, None)
if TAG == "t07":  # refused folds: subject, structure or inference only, or long work without visible run-on
    for g in ("1500129557", "1500250159", "1500103421", "300037469", "900164336", "1500132650", "600030433"): fold.pop(g, None)
if TAG == "t08": fold.update({"1500107132": "300050067", "1500107133": "300050067", "1500107142": "1200073771"})  # Kaempfer tea / paper: keeper rows share the candidates' text
if TAG == "t10": fold.update({"900145958": "900145957"})  # Varillasiana, Naples: visible run-on between the two candidates
if TAG == "t11": fold.update({"900029298": "1500032636"})  # Glenn 31 Oct: the same French text of the 4th Jansenist proposition
if TAG == "t12":
    fold.update({"1500172649": "900284431",                     # Aspasie song: two keepers, one song
                 "1500053412": "900124270", "1200048065": "1200048089", "1500053178": "1500053407",  # one pericope, two keepers (2 P 1,19; 1 Tm 6,17-19; Mt 25)
                 "600049359": "600051984",                       # Rousseau, Économie politique: same sentence in both keepers
                 "900194404": "900144402", "900144399": "900144402", "1500196973": "900144402", "900195317": "900144402",  # Boissier de Sauvages memoir (Glenn ruling 7)
                 "900190519": "900190522", "900190520": "900190522", "900190521": "900190522"})  # Cato's amurca section, one Gazette extract
    fold.pop("900265037", None)  # Cléophile: two songs to one woman, not shown one song
ARG_KEEP = ("11200144485", "11200144237", "11200263043", "11200262545", "11200078714", "11200078648", "10300063798", "11200319541", "11200190145",
            "11200272880", "11200272887", "11200255000", "11200255001", "10900339820", "11200323742", "11200255987", "11200127283") if TAG == "t17" else ()
if TAG == "t17":  # Glenn 4 Nov: Isnard v. Necker overlap on one clause = fold; mc_0 keeper pairs carrying one passage; short prose anecdotes with a near run-on
    fold.update({"10300056975": "11200163488", "11200066623": "10300050906", "10300110912": "10300110911", "11200027347": "10300008364"})
if TAG == "t16":  # verse folds without overlap refused; Vertot's Fabia anecdote (prose) one unit
    for g in ("10300111552", "11200284916", "10000000756", "10300111549", "11200314723", "10300143897", "10300143898", "300041228", "300041242", "11200027010"): fold.pop(g, None)
    fold.update({"10300051519": "10300051518"})
if TAG == "t15":
    fold.pop("11200018897", None)  # Decalogue: Exodus 20 and Deuteronomy 5 are two texts, not two wordings of one
    fold.update({"11200206841": "11200206840"})  # Contrat social III.15: row 2015660 runs on
if TAG == "t13":  # Levret's "Résumé de pratique" printed as one extract (Gazette salutaire, JdM 1770): one short piece
    fold.update({g: "900175454" for g in ("900175439", "900175440", "900175441", "900175449", "900175450")})
if TAG == "t01": fold.update({"900291580": "900291578", "900291582": "900291578", "900291584": "900291578"})  # Esther II.8, one chorus
V = {}; srcs = []
for f in sorted(glob.glob("v_*.tsv")):
    for r in csv.reader(open(f, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
        if not r or r[0] == "group": continue
        r += [""] * 6; V[r[0].strip()] = [x.strip() for x in r[:6]]
        if r[0].strip() in VERDICT_OVR: V[r[0].strip()][1:4] = [VERDICT_OVR[r[0].strip()], "", ""]
        if r[4].strip(): srcs.append((r[0].strip(), r[1].strip(), r[4].strip(), r[5].strip()))
act = {}; flags = []
def put(rid, g, a, d, why): act[rid] = [g, a, d, why]
for g, (g_, v, d, rr, src, note) in V.items():
    if v in ("KEEP", "NOISE", "EDITION", "LATIN"):
        for rid in rows[g]:
            if v == "NOISE" and ((g, "") in snk or (TAG in ("t13", "t14", "t15", "t16", "t17", "t18") and (g, rid) in snk)): put(rid, g, "KEEP", "", "short-NOISE overturned by second reader")
            else: put(rid, g, v, "", v)
    elif v == "MOVE":
        ok = chk.get((g, "")) == "AGREE"
        for rid in rows[g]: put(rid, g, "MOVE" if ok else "KEEP", d if ok else "", "MOVE agreed" if ok else f"MOVE not confirmed ({chk.get((g,''),'?')}): stays")
    elif v == "PART":
        for t in rr.split():
            rid, w = t.split(":", 1)
            if w == "NOISE" and (g, rid) in snk:
                if rid in SAME_PASSAGE: put(rid, g, "KEEP", "", "PART short-NOISE overturned by second reader")
                else: put(rid, g, "NEW", f"P{g}:sn{rid}", "PART short-NOISE overturned: its own short passage")
            elif w in ("KEEP", "NOISE", "EDITION", "LATIN"): put(rid, g, w, "", "PART")
            elif w.startswith("NEW:"): put(rid, g, "NEW", NEW_RELABEL.get(rid, f"P{g}:{w[4:]}"), "PART new")
            else:
                ok = chk.get((g, rid)) == "AGREE"
                put(rid, g, "MOVE" if ok else "NEW", w if ok else f"P{g}:to{w}", "PART row move agreed" if ok else "PART row move not confirmed: own group")
ROW_KEEP = {"t02": {"339369", "339775", "339370"}, "t04": {"141691"},
            "t10": {"575120", "575121", "575180"},  # Glenn 29 Oct: Polier's 1747 Pensées v. the 1751 Philosophie morale = different authors, reuse
            "t11": set("43004 143287 533005 141927 133036 133037 133038 133039 133040 133041 133042 128314 128315 128316 128317 125664 125665 127256 127257 127258 127259 127260 127261".split()),
            # t11: 43004 Latin proposition (Glenn 31 Oct 7); the rest: 1793-era declarations argued from in pamphlets / histories, not deputies (Glenn 30 Oct)
            "t14": set("758318 758334 758343 758349 758353 758355 758361 758363 758372 758377 758379 758435 758446 758468 758471 758489 758495 758523 273404 273405 273444 273445 699392 699395 1721345".split())  # Glenn 2 Nov (3): Du Tertre, La Porte, Barthélemy recast under a new title = self-reuse, KEEP
                   | set("690813 1003151 690818 1003152 1003153 475791 700213 470864 514901 705702 705703 700215 475796 1003178 1003179 1003186 1003193 146076".split()),  # Hilliard d'Auberteuil, the Lettres historiques, the Histoire des désastres argue from the acts (KEEP + out_of_scope)
            "t09": {"158349", "158350", "111943", "111944", "111945", "953534"}}  # Housset 1798, Rapport au Comité des domaines 1790, Maury 1790: argue from the edict  # t04: Declaration art. 7 quoted in argument (out_of_scope claim)
ROW_KEEP = ROW_KEEP.get(TAG, set())  # Rochon, Priam passage: stays in its own group 900143239
for rid in ROW_KEEP:
    if rid in act: act[rid][1:4] = ["KEEP", "", "row kept: ruling or row move refused (see compile block)"]
ROW_NOISE = {"t03": {"327468", "854252", "162966"},
             "t08": set("572062 572060 572501 572500 572513 572512 572538 572556 572555 572558 572557 572573 571936 572239 572238 572260 572259 572263 572268 572271 572270 572290 572289 572292 572291 572854 572860 572916 572588 572590 572593 572640 572648 572662 572663 572666 572670 572674 572715 572723 572728 572733 572542 572541 572569 571816 571817".split())}.get(TAG, set())  # t08: Glenn 26 Oct, the 1731 Tacite reprints d'Ablancourt (doublon with 1665/1674)  # Glenn 23 Oct: Collection académique reprints the Académie volumes whole (doublon)
if TAG == "t10":  # Glenn 29 Oct: Piganiol 1742 Description de Paris recasts the 1722 Paris volumes (same work, same author); Pliny pair = independent translations
    ROW_NOISE = set("840418 840421 840424 840456 840544 840546 840557 840583 840585 696709 696710".split())
if TAG == "t11":  # Glenn 30-31 Oct: own later collection = doublon (Buc'hoz, La Caze); jurist's formula (731558); Nouvelle instruction v. its 1716 reprint
    ROW_NOISE = set("1001380 926008 925993 926073 950285 731558 812817".split())
if TAG == "t12":  # Glenn 31 Oct (4): doublons tested on the true author/text -- Cornaro 1701 v. the 1782 reprint of the same translation; Coulanges 1710 v. 1754
    ROW_NOISE = set("813690 823931 823933".split())
if TAG == "t13":  # Le Cat's own pieces across his own recueils (doublon, Glenn 1 Nov); independent translations (Anacreon; Mengs Jansen twice); Portal T2 v T5; Sully 1745 v 1788; Lamy 1694 v 1699; Tablettes stock rows; cantique book v cantique book
    ROW_NOISE = set("902717 902720 902721 902722 902615 902618 902619 910305 902777 902778 902779 902780 902782 902783 902784 902786 902598 902599 902800 902801 902802 902510 902511 902513 902512 280037 280038 902788 910287 902703 902704 902713 902714 902762 910338 902727 902728 902750 910285 902739 914513 667298 667299 1786326 963685 556033 802711 1009862 1003819 393416 393415 918376 1000885 1000886 717878 717879 717880".split())
if TAG == "t14":  # Glenn 2 Nov (4, 22): manual v. manual (Hombre 1718, Académie 1730, Quadrille 1739/1742) = one text in extenso; whole tales reprinted in the Cabinet des fées / the author's reissues; Les Cayes minutes as pièce justificative; Saint-Marc Adresse
    ROW_NOISE = set("54059 54060 835960 835961 835962 835951 835952 835939 835940 835941 835946 835947 835948 835949 858850 858851 858844 858845 858846 858847 858848 858849 835937 835921 835922 835923 835925 835926 835927 835928 835929 858852 858853 1025433 1023933".split())
    ROW_NOISE |= set("490362 490361 862870 862871 862876 862877 490366 490364 490365 490367 957158 957159 957160 957161 490371 490370 490369 490368 490373 490372 490374 490375 490377 490376 490379 490381 482395 482394 482411 490387 490388 490389 490390 490397 490401 490400 490402 490403 490408 490409 490410 490411 490412 490413 490415 490417 490414 490416 490418 490419 490420 490422 490423 490424 490425 490421 490431 490432 490435 490436 490433 490434 957171 957172 862883 862885 862888 862890 490437 490438 490439 490440 862897 862898 862899 862900 862901 490441 490442 490443 490444 490446 490447 490445 862920 862921 862922 862923 862931 862933 862934 862936 862937 862971 862979 862978 862988 862991 490471 490472 490473 490474 496155 862990 490470 496156 862989 490476 862994 862995 862996 490475 490477 490478 490479 490480 490483 490485 490495 490497 490493 490498 490501 490494 490499 490504 490505 957190 490503 825069 825070 825071 825072 825073 825074 825075 482366 825046 482370 482371 482374 825054 825055 825056".split())
if TAG == "t09":  # Glenn 27 Oct: doublons (Saint-Cyran, Gazaignes/Raynaud/Hermant, Gastier/Loyseau, Marandé, Senlis, Daniel, Du Perron, Thomé, Louail) and Condren's Idée as office
    ROW_NOISE = {l.split("\t")[0] for l in open("rownoise_t09.tsv", encoding="utf-8") if l.strip()}
for rid in ROW_NOISE:
    if rid in act: act[rid][1:4] = ["NOISE", "", "doublon: reprint of the same work (Glenn ruling)"]
if TAG == "t08" and "726378" in act: act["726378"][1:4] = ["NEW", "P1200147217:a", "Le Bouvier-Desmortiers on curiosity: its own passage (Declaration rows set aside)"]
for rid, d in EXTRA_ROW_MOVES.items():
    if rid in act: act[rid][1:4] = ["MOVE", d, "second reader: shares the keeper's text"]
if TAG == "t12":  # rows sharing no text with the keeper they would travel to: their own groups
    for rid, lab, why in (("666783", "P1200093928:own", "Massillon, next paragraph of the sermon (paragraph rule)"),
                          ("628170", "P1200062380:volt", "Voltaire's own remark (Annales de l'Empire), not Cola's letter")):
        if rid in act: act[rid][1:4] = ["NEW", lab, why]
if TAG == "t14":  # second readers: rows kept but not the group's passage -> their own groups
    for rid, lab, why in [(r, "P1500236778:sug", "Raynal's sugar residue (cattle, chaux vive), its own passage") for r in ("506556", "506557", "506558", "992674")] +                          [(r, "P900284253:cyr", "Cyrano's duels (Le Bret via Niceron), not the Contes mogols") for r in ("1596280", "1596281")] +                          [("530835", "P1500259923:own", "second reader: a different passage"),
                          ("1289807", "P10900027162:dial", "opening of de Piles's Dialogue sur le coloris: does not travel with the fold")]:
        if rid in act: act[rid][1:4] = ["NEW", lab, why]
if TAG == "t16":  # second readers' single-row moves; compilations; paratext; short-KEEP check (translations only)
    for rid, d in {"2065631": "11200262249", "2065632": "11200262249", "1061432": "10300095606", "1840665": "11200326137"}.items():
        if rid in act: act[rid][1:4] = ["MOVE", d, "fold check: this row carries the keeper's passage"]
    for rid in open("scripcomp_rows.txt").read().split() + "2120883 1296796 1296798 1296800 1403876 2038795".split():
        if rid in act: act[rid][1:4] = ["NOISE", "", "liturgical compilation / catechism / stock definition / whole-tale reprint / paratext (Glenn 3 Nov)"]
    for g in ("11200230877", "11200032661", "11200024352", "10300126146", "10300007961"):
        for x in rows.get(g, []):
            if x in act and act[x][1] == "KEEP": act[x][1:4] = ["NOISE", "", "short-KEEP check: independent translations converge / paratext (Glenn 3 Nov)"]
if TAG == "t15":  # second readers: rows leaving their groups; scripture compilations; short-KEEP check
    for rid, d in {"1858677": "11200054424", "1858678": "11200054424", "1811154": "11200016679", "1812546": "11200017761",
                   "1813666": "11200018197", "1811781": "11200017243"}.items():
        if rid in act: act[rid][1:4] = ["MOVE", d, "fold check: this row carries the keeper's passage"]
    for rid, lab, why in [("966650", "P1500209858:mons", "Chappe, the Mons/Balk affair: its own anecdote"), ("966652", "P1500209858:mons", "Chappe, the Mons/Balk affair: its own anecdote")] + \
                         [(r, "P900178914:wolf", "Chappe / Delisle de Moncel, poisoning wolves: one passage") for r in ("378657", "378658", "378662", "378665")]:
        if rid in act: act[rid][1:4] = ["NEW", lab, why]
    for rid in open("scripcomp_rows.txt").read().split():  # Glenn 2 Nov (7, 3): scripture compilations, catechisms, prayer books NOISE in every row
        if rid in act: act[rid][1:4] = ["NOISE", "", "scripture compilation / catechism / prayer book (Glenn 2 Nov)"]
    SKX = {"11200260204", "300015354", "1500182652", "11200136083", "900292451", "900292453", "900292454"}  # act argued from; Glenn 2 Nov (12) fragments of certain copying KEEP
    for f in sorted(glob.glob("skv_*.tsv")):
        for r in csv.reader(open(f, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
            if not r or r[0] == "group": continue
            r += [""] * 4; g, rid, v = r[0].strip(), r[1].strip(), r[2].strip()
            if v != "NOISE" or g in SKX: continue
            for x in ([rid] if rid else rows.get(g, [])):
                if x in act and act[x][1] == "KEEP": act[x][1:4] = ["NOISE", "", "short-KEEP check: common words / formula / fragment"]
if TAG == "t17":  # Glenn 4 Nov rulings
    # (b) same author repeating his own text in technical / expository / economic prose = doublon (Masson, d'Éon, Necker, Duhamel, Linguet, Clicquot, Abot, Parmentier, Roland, Isnard, Le Trosne, Accarias)
    for l in open("sameauthor_t17b.tsv", encoding="utf-8"):
        rid = l.split("\t")[0]
        if rid in act: act[rid][1:4] = ["NOISE", "", "same author repeating his own technical/economic text = doublon (Glenn 4 Nov, rule b)"]
    # usance rules dense with figures NOISE (Glenn 4 Nov 3)
    for g in ("11200184527", "11200184549", "11200184580", "11200184675", "11200207611", "11200184640", "11200184680", "11200202035", "11200224000"):
        for x in rows.get(g, []):
            if x in act: act[x][1:4] = ["NOISE", "", "usance rule dense with figures (Glenn 4 Nov)"]
    # the 1761 trilingual Encyclopédie set aside (Glenn 4 Nov 8)
    for rid in open("trilingual_rows.txt").read().split():
        if rid in act: act[rid][1:4] = ["NOISE", "", "dictionary out of the books corpus: Encyclopédie françoise, latine et angloise 1761 (Glenn 4 Nov)"]
    # acts quoted in argument KEEP whatever their size (Glenn 4 Nov 2); compilations / digests / manuals / a party's own mémoires stay NOISE
    for g in ARG_KEEP:
        for x in rows.get(g, []):
            if x in act and act[x][1] == "NOISE" and act[x][3] in ("NOISE", "PART"): act[x][1:4] = ["KEEP", "", "act quoted in argument: KEEP + out_of_scope (Glenn 4 Nov)"]
    # second readers: mc_0 DISAGREE on row 1094420 (next paragraph, EL V.3): stays in its own group
    for rid in ("2069378", "2069383"):  # Isnard quoting Necker's Mémoire (sn_3): one passage with Necker's group (Glenn 4 Nov: overlap = fold)
        if rid in act: act[rid][1:4] = ["MOVE", "10600045951", "Isnard quotes Necker's Mémoire: the Necker group's passage (overlap)"]
    # Glenn 4 Nov: no double counting -- a third witness aligned with two volumes of one author's repeated text keeps only its row to the earliest volume
    for l in open("dupwitness_t17.tsv", encoding="utf-8"):
        rid = l.split("\t")[0]
        if rid in act and act[rid][1] in ("KEEP", "MOVE", "NEW"): act[rid][1:4] = ["NOISE", "", "same witness already counted against the author's earliest volume (Glenn 4 Nov: no double counting)"]
    # Franklin, Way to Wealth: two complete translations aligned with each other NOISE; a quoter following the other translation KEEP (Glenn 4 Nov)
    if "2048502" in act: act["2048502"][1:4] = ["NOISE", "", "Franklin Oeuvres 1773 v. Science du Bonhomme Richard 1777: two translations of the work"]
    if "1846284" in act: act["1846284"][1:4] = ["KEEP", "", "Coster's Éloge de Colbert quotes the 1673 Ordonnance preamble in argument (out_of_scope)"]
    for f in sorted(glob.glob("skv_*.tsv")):  # short-KEEP check (Glenn 4 Nov trace rule); every NOISE line read by me
        for r in csv.reader(open(f, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
            if not r or r[0] == "group": continue
            r += [""] * 4; g, rid, v = r[0].strip(), r[1].strip(), r[2].strip()
            if v != "NOISE": continue
            for x in ([rid] if rid else rows.get(g, [])):
                if x in act and act[x][1] == "KEEP": act[x][1:4] = ["NOISE", "", "short-KEEP check: not traced / same-author doublon / independent translations"]
    if "1094419" in act: act["1094419"][1:4] = ["MOVE", "11200163488", "second reader: row 1094419 overlaps the keeper (EL V.3); row 1094420, the next paragraph, stays"]
if TAG == "t17" and "1610747" in act: act["1610747"][1:4] = ["KEEP", "", "the Gazette 1774 reuses Franklin (1773 rendering): the only trace of that reuse"]
if TAG == "t18":  # Glenn 4 Nov evening (t18 rulings): literary reuse always KEEP; different works by one author KEEP;
    # only full reprints / duplicate copies NOISE; legal and revolutionary text in doubt KEEP + out_of_scope.
    # rvv_*.tsv: second readers on every NOISE call that cited double count / rule (b) / doublon / legal text
    for f in sorted(glob.glob("rvv_*.tsv")):
        for r in csv.reader(open(f, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
            if not r or r[0] == "group": continue
            r += [""] * 4; g, rid, v, note = r[0].strip(), r[1].strip(), r[2].strip(), r[3].strip()
            if v not in ("KEEP", "OOS"): continue
            for x in ([rid] if rid else rows.get(g, [])):
                if x in act and act[x][1] == "NOISE":
                    act[x][1:4] = ["KEEP", "", ("legal/revolutionary text in doubt: KEEP + out_of_scope" if v == "OOS" else "literary / different-work reuse: KEEP") + " (t18 rulings 1-2; second reader: " + note[:80] + ")"]
    for f in sorted(glob.glob("skv_*.tsv")):  # short-KEEP check (trace rule)
        for r in csv.reader(open(f, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
            if not r or r[0] == "group": continue
            r += [""] * 4; g, rid, v = r[0].strip(), r[1].strip(), r[2].strip()
            if v != "NOISE": continue
            for x in ([rid] if rid else rows.get(g, [])):
                if x in act and act[x][1] == "KEEP": act[x][1:4] = ["NOISE", "", "short-KEEP check: not traced / full reprint / independent translations"]
    for g in ("10000003907", "10000004687"): fold.pop(g, None)  # fcv: only one row of each overlaps the keeper (row moves, not whole folds)
    T18_EXTRA = "t18_extra.tsv"  # my calls after reading the second readers (rowid, action, dest, why)
    if os.path.exists(T18_EXTRA):
        for l in open(T18_EXTRA, encoding="utf-8"):
            p = l.rstrip("\n").split("\t")
            if len(p) >= 4 and p[0] in act: act[p[0]][1:4] = [p[1], p[2], p[3]]
for g, d in fold.items():
    for rid in rows[g]:
        if act[rid][1] == "KEEP": act[rid][1:4] = ["MOVE", d, "fold check: same unit"]
# resolve MOVE chains and dests that are not staying groups
def keeps(g): return any(x[0] == g and x[1] in ("KEEP",) for x in act.values())
mv = {g: x[2] for x in act.values() for g in [x[0]] if x[1] == "MOVE" and all(act[r][1] == "MOVE" and act[r][2] == x[2] for r in rows[g])}
mv.update(fold)
for rid, x in act.items():
    if x[1] != "MOVE": continue
    d = x[2]; seen = set()
    while d in mv and d not in seen: seen.add(d); d = mv[d]
    if d != x[2]: x[3] += f" (chain -> {d})"; x[2] = d
    if d == x[0]: x[1], x[2] = "KEEP", ""
    elif d in V and not keeps(d) and d not in [y[2] for y in act.values() if y[1]=="MOVE" and y[0]!=x[0]] and V[d][1] in ("NOISE","EDITION","LATIN"):
        flags.append(("DEST_NOT_STAYING", rid, x[0], d)); x[1], x[2], x[3] = "KEEP", "", x[3] + " / dest set aside: stays"
miss = [g for g in rows if g not in V]
with open(f"plan_{TAG}.tsv", "w") as fh:
    fh.write("rowid\tfrom_group\tcomp\taction\tdest\tbatch\twhy\n")
    for rid in sorted(act, key=int):
        g, a, d, why = act[rid]; fh.write(f"{rid}\t{g}\t{g}\t{a}\t{d}\tP{batch[g]}\t{why}\n")
with open(f"sources_{TAG}.tsv", "w") as fh:
    fh.write("group\tverdict\tsource\tnote\n")
    for s in srcs: fh.write("\t".join(s) + "\n")
print("rows", len(act), dict(Counter(x[1] for x in act.values())), "groups without verdict", len(miss), "flags", flags[:5])
print("rows in batches", sum(len(v) for v in rows.values()), "source lines", len(srcs))
