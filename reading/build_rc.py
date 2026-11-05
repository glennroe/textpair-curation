#!/usr/bin/env python3
"""build_rc.py DIR -- Phase P second-reader files for one tranche directory (p_*.txt + v_*.tsv).
  mc_K.txt  every MOVE (whole group, or PART row to a group id): keeper block + proposing group block(s)
  sn_K.txt  every NOISE called on SHORTNESS (note mentions short/fragment/brief/quotable): whole groups,
            and the NOISE rows of PART groups whose note says so
  fc.txt    fold candidates listed in FOLD (groups the first reader kept apart although they may be one unit)
Verdict files the second readers write:
  mcv_K.tsv  group row dest verdict note    (row empty = whole group; verdict AGREE / DISAGREE / UNSURE)
  snv_K.tsv  group row verdict note         (row empty = whole group; verdict NOISE / KEEP)
  fcv.tsv    group dest verdict note        (verdict FOLD / APART)"""
import csv, glob, os, re, sys
from collections import defaultdict
csv.field_size_limit(sys.maxsize)
D = sys.argv[1]
FOLD_T01 = [  # (keeper, [others]) from the t01 first readers' notes
    ("11200319237", ["1200100706"]), ("900263490", ["10900128265"]), ("900202467", ["900203758"]),
    ("900235587", ["900235589"]),
    ("900291568", ["900291578", "900291580", "900291582", "900291584", "900291588"]),
]
FOLD_T02 = [  # (keeper, [others]) from the t02 first readers' notes: short units only (letters, speeches, poems, songs,
              # scenes, short articles, one case history / anecdote); long works fold only on shared text (MOVE)
    ("10300034621", ["10300034624", "900148339"]),            # L'Hospital's testament (Colomiès, Bayle, Brantôme)
    ("600036683", ["600022175"]),                              # Lefèvre de La Planche paragraph (Boncerf, Barère)
    ("1500097581", ["900123041"]),                             # "Rien n'est si beau" refrain, one song?
    ("900298415", ["1500097584"]),                             # "Maris, vous vous fâchez" couplet of the hymen song?
    ("600060713", ["600060711"]),                              # Directory's 1798 message on Rome
    ("1200144003", ["900328696"]),                             # 18 Fructidor text
    ("10900313720", ["300008576"]),                            # Destouches, Le Dissipateur, one scene?
    ("1500279896", ["1500279898"]),                            # Villette letter (Boyer-Brun)
    ("1500275581", ["1200143625"]),                            # 1788 Grève episode, run-on?
    ("900321946", ["1200147029"]),                             # philosophes' speech in Crillon
    ("1500279937", ["1500279939"]),                            # one 1792 pamphlet (Boyer-Brun)
    ("1500212025", ["1500212026", "1500212027", "1500212029"]),# one Young lament (Bardou)
    ("11200326563", ["1200066413", "900089592", "900089593", "1200066418"]),  # Temple de la Félicité emblem verses
    ("1200143744", ["1200143746", "1200143747", "1200143748", "1200143752"]),  # Escherny, Fête de la Fédération
    ("300053410", ["300053412"]),                              # Watelet, CHEVALET, short article
    ("900259262", ["900258381"]),                              # Hilliard d'Auberteuil on Gage
    ("1500140202", ["1500140203", "1500140204"]),              # Grondine tale
    ("900308955", ["900308956"]),                              # Duclos, petite-maîtresse portrait
    ("900257277", ["900257278"]),                              # Ou-tse's dialogue (Amiot)
    ("900110218", ["900110240", "900110241"]),                 # one argument against transubstantiation (Le Febvre)
    ("1500262160", ["1500262162"]),                            # one letter, Rohan affair
    ("1500154243", ["1500154248", "1500154249"]),              # minister's letter to La Bourdonnais
    ("1200118765", ["900251982"]),                             # Ducis, Oedipe chez Admète, curse scene
    ("1200042812", ["1200042813"]),                            # one note on swans (Horace edition)
    ("900330912", ["900330913"]),                              # Lichtenstein quotations (Le Riche)
    ("1500232131", ["1500232215"]),                            # Richelieu letter about Marion
    ("1500209162", ["1500209163", "1500209165"]),              # Kang-hi and European music (Arnaud)
    ("900204152", ["900204153"]),                              # Blanchard on self-praise
    ("600034956", ["600034957", "600034958"]),                 # La Métherie self-quotation
    ("600035062", ["600035063"]),                              # clergy deputies' speech
    ("1200134406", ["1200134407"]),                            # Besenval amnesty
    ("600036258", ["300054372", "600031828"]),                 # Mirabeau's address on the troops
    ("900328384", ["11200317104"]),                            # Fabre d'Eglantine, Philinte, Alceste tirade
    ("1500202745", ["1500202746"]),                            # Yvette water-analysis report
    ("600027727", ["11200310212", "1200133657", "10600068757"]),  # Luchet's portrait of Necker
    ("1200141627", ["900286594"]),                             # Seneca NQ VII.25 in French (renderings fold)
    ("900286586", ["1200141645"]),                             # one quoted narrative of Newton's first ideas
    ("900286567", ["900245986"]),                              # Roucher, Les Mois, astronomy tirade
    ("11200322543", ["1500199337"]),                           # Lalande phrase shared via the Abrégé
    ("900164455", ["900164456", "900164457", "900164459", "900164461"]),  # Hautesierck chest-dropsy case
    ("900189254", ["900189255"]),                              # petrified ox brain
    ("900125172", ["1500168239"]),                             # Méry's transposed viscera
    ("1200143971", ["1200143972"]),                            # one quoted speech (Lachappelle, Pagès)
    ("1200137718", ["1200132929", "1200139432"]),              # Raynal on society and government, quoted by Paine as one block
    ("600055883", ["600055885"]),                              # Louis XVI's answers at his trial
    ("900246708", ["900246709", "900246710"]),                 # Luchet's Discours extracts in one Journal de Paris review
]
FOLD_T04 = [  # (keeper, [others]) from the t04 first readers' notes: short units only; poems of unknown length go to the
              # fold reader with the 200-line rule (Glenn 23 Oct)
    ("900101689", ["900099924", "900099925"]),                 # L'Orphelin de la maison de Tchao, one scene?
    ("900221988", ["1500115599", "1200078471", "1500115619"]), # L'Hôpital's speeches reported by de Thou, same harangue?
    ("900019640", ["900019642"]),                              # verse in de Thou's Mémoires, one poem?
    ("1200039419", ["1200039422", "1200039423"]),              # de Thou's speech on the Council of Trent
    ("900216851", ["900216853"]),                              # Bonneval, Les Romans, one entrée?
    ("1500120311", ["1500120312", "300017689"]),               # Girard, ACTION/ACTE, one article
    ("900259399", ["900261620", "900259401"]),                 # Möller, Le Comte de Waltron, one scene?
    ("1200136251", ["1200136252", "1200136253", "1200136254", "600034591", "1200136256", "1200136258"]),  # Grégoire's letter of 8 June 1791
    ("900168062", ["11200324440"]),                            # Ernelinde, one scene?
    ("900168065", ["900168067"]),                              # Ernelinde, one scene?
    ("900168051", ["900168052"]),                              # Ernelinde I.1
    ("11200018606", ["11200319691"]),                          # Laujon, Aeglé ("Paisibles bois"), Mercure row runs on
    ("1200133950", ["1200133952", "1200133953"]),              # address to the King in Gouy d'Arsy's Lettre
    ("600031424", ["10600070018"]),                            # one letter, Correspondance secrète (Saint-Domingue)
    ("900117182", ["900118841", "900117968", "900117969", "900117183"]),  # d'Arnaud, La Mort du maréchal de Saxe (length?)
    ("10300128161", ["300037241"]),                            # de Thou, Mantua Cupid anecdote
    ("1200039349", ["1200039348"]),                            # de Thou, Canigou ascent
    ("900170024", ["900170025"]),                              # Roussillon verses (Gazette littéraire, Mercure 1769)
    ("900107444", ["900107445"]),                              # Gentil-Bernard, Adonis entrée
    ("900304478", ["900304479"]),                              # Le Philosophe marié, Marquis/Mélite scene
    ("900304482", ["900304483"]),                              # Le Philosophe marié, Ariste/Damon scene
    ("1500068268", ["1500068269"]),                            # Santeul, Santolius poenitens (Latin poem)
    ("1200030938", ["900120971"]),                             # La Motte ode, "Un bon mot ne prouve rien"
    ("900218013", ["1200145874"]),                             # Piron, Gustave, one scene?
    ("1500276553", ["1500276554", "1500276555", "1500276556", "1500276557", "1500276558", "1500276559"]),  # Laya, Jean Calas scenes
    ("1200108833", ["1200108835"]),                            # Rosset, cartel prose and verses
    ("1200100764", ["1200145785"]),                            # Critique de Mérope
    ("1200112894", ["900257263"]),                             # Chinese maxims (Levesque)
    ("900304599", ["900304600", "900304601", "900304603"]),    # Belloy, Le Siège de Calais, Act IV/V scene?
    ("900304564", ["10900210214"]),                            # Belloy, Eustache's speech
    ("1500096293", ["900061229"]),                             # duc de Bourgogne, Élémens, run-on
    ("900196936", ["900196935"]),                              # Saurin, L'Orpheline léguée, one scene?
    ("600025166", ["600025167"]),                              # Maimieux, Éloge de l'impertinence, one paragraph
    ("1200031431", ["1200031432"]),                            # recipe for painting prints under glass
    ("900041775", ["1500038611"]),                             # Tacitus, Annals III.26-27, renderings
    ("1500140216", ["1500140217", "1500140218", "1500140219", "1500140221", "1500140223"]),  # verse portraits of actors, one verse letter?
    ("900103603", ["900103604", "900103610", "900103613"]),    # d'Estaing, Le Plaisir, rêve (length?)
    ("900170071", ["900170072"]),                              # Carmontelle, La Médaille d'Othon, one scene?
    ("900226724", ["900230842", "900226727"]),                 # Dorat, Épître à l'ombre d'un ami (length?)
    ("600055801", ["600055803"]),                              # Le Brun, Discours en vers sur les notables (length?)
    ("1500231559", ["1500231560"]),                            # Brantôme, one anecdote?
]
FOLD_T03 = [  # (keeper, [others]) from the t03 first readers' notes: short units (letters, speeches, scenes, short poems,
              # anecdotes, one notice); poems longer than an épître wait for Glenn's ruling on length (23 Oct)
    ("900248749", ["900247343"]),                              # Villemain d'Abancourt, verse letter to Salaun
    ("900177493", ["900176690"]),                              # Linguet on La Condamine, one paragraph
    ("900135238", ["900135240"]),                              # Samoyed description
    ("900128532", ["1500118629"]),                             # Chinese emperor's speech and instructions to his son
    ("900020229", ["900035355"]),                              # La Mesnardière's reception harangue
    ("900330749", ["900330747", "900330206", "900330748"]),    # Baour-Lormian, Mon second mot
    ("900143393", ["900161038"]),                              # Aubert, L'Amour filial (fable)
    ("600052250", ["10600079021"]),                            # Mme Roland's defence speech
    ("900042207", ["900042208"]),                              # Madame Sagona anecdote
    ("1500028307", ["1500028310", "1500028311"]),              # Hélène de Tournon's story (Marguerite de Valois)
    ("900044254", ["1200117610"]),                             # portrait of Columbus
    ("900191853", ["10600080912"]),                            # Colardeau, Héloïse à Abailard
    ("900113375", ["900257823"]),                              # Pope's Héloïse, renderings of one passage (Feutry/Colardeau)
    ("900242628", ["900242629"]),                              # Dorat epistle in one review
    ("900304548", ["600020614"]),                              # Crébillon, Rhadamiste, ambassador scene
    ("900304551", ["900304552", "900304553"]),                 # Rhadamiste, act III scene?
    ("900025338", ["900025339"]),                              # Sémiramis to Ninias
    ("900025334", ["900025337"]),                              # Ténésis scene
    ("900271339", ["900271340"]),                              # Iphigénie en Tauride, Oreste's furies
    ("900317002", ["1500102052"]),                             # Molay's scaffold speech and summons
    ("900209716", ["900209717"]),                              # Bertrand de Got's election (Vertot)
    ("900064681", ["900090856"]),                              # Louis Racine, Épître à Valincour
    ("900157050", ["900157052", "900157054"]),                 # one letter on the Martel affair
    ("600011102", ["600011103", "600011104"]),                 # Naudé's precepts of tyranny, one run
    ("1500243999", ["1500244000"]),                            # Amiot, one ceremony description
    ("10900092378", ["900079163"]),                            # Le Franc, Didon, ambassador scene
    ("900296839", ["900130477", "900050966", "900296840", "1200050950"]),  # Didon, farewell / imprecation scene
    ("1200076587", ["1200076588"]),                            # Godeheu's letter
    ("1500011995", ["11200327039"]),                           # Frénicle, Francus prophecy
    ("1200071769", ["1200098448"]),                            # Régiment de la Calotte vaudeville
    ("1500128886", ["1500016907"]),                            # Boyvin's quoted discourse
    ("1200073672", ["1200073674"]),                            # Brittany fish voyage (Histoire de l'Académie)
    ("1200073670", ["1200073671"]),                            # notice on Duverney and honey
    ("900000149", ["900000150"]),                              # preformation paragraph
    ("900000167", ["900000168", "1500105789"]),                # Duclos on desalinating sea water
    ("900255898", ["10900305564", "900255895"]),               # Malvaux's run of anecdotes on the blind
    ("900060391", ["900060393", "900048631"]),                 # Rivard's dedicatory epistle
    ("900071354", ["900071355", "900071356"]),                 # Moncrif, Les Abdérites, one scene?
    ("1200119232", ["1200093459", "10600083137"]),             # J.-B. Rousseau, épître (à Thalie)
    ("10300141299", ["10900400310", "10900400311"]),           # J.-B. Rousseau, one épître?
    ("900209427", ["900209426"]),                              # Linguet, Réflexions, one period
    ("1200049227", ["300003422"]),                             # Machiavel ch.?: text runs on (Frederick / Bayle)
    ("1200049257", ["11200320888"]),                           # Prince ch.7, Borgia: few-word overlap
    ("900228730", ["900228732"]),                              # Montyon, "Tu veux de l'or" apostrophe
    ("900277724", ["1200104506"]),                             # Linguet letter on the duc d'Aiguillon
    ("11200318080", ["11200318081", "11200318082", "11200318083"]),  # Lettre d'un académicien de Berlin
    ("600021179", ["600021180"]),                              # Monmouth narrative (Saint-Foix)
    ("900314299", ["900314295", "900314296", "900314297"]),    # Comte de Lorges narrative
]
import sys as _s
FOLD_T05 = [  # (keeper, [others]) from the t05 first readers' notes; short units only, long works left to the long-work rule
    ("900233470", ["900233471", "900233472"]),                 # Funérailles d'Arabert
    ("900212934", ["900212935", "900212936"]),                 # Chabanon, De l'esprit de parti (poem; length?)
    ("900250083", ["900250084", "900255722", "900250089"]),    # Guyétand, Le Génie vengé
    ("900250717", ["900250718", "900250719"]),                 # Bastide, Euphémie/Mélidor tale
    ("1500183644", ["900301193"]),                             # phantom limb paragraph
    ("900193547", ["900193549"]),                              # Portal, Gazette salutaire
    ("900247281", ["900247292"]),                              # Jay-Allemand, Journal de Paris
    ("1500172092", ["1500172093", "1500172094"]),              # Guidi, Épître d'un constitutionnaire (length?)
    ("900237912", ["900238930", "900237914", "900237915"]),    # Neufchâteau, Phocion (one scene?)
    ("900145590", ["1200099423"]),                             # Deparcieux, aqueducts
    ("1500085891", ["300012487"]),                             # Boileau, Épître II
    ("10900177620", ["900176259"]),                            # Menagiana basket/monkeys anecdote
    ("300051555", ["300051554"]),                              # La Varenne ana
    ("1500085834", ["900145893"]),                             # Grandier deposition / confession
    ("900092008", ["900092010"]),                              # Requête des Dictionnaires
    ("1200141123", ["1200141124"]),                            # Robert, Plan de finances
    ("1200127757", ["1200127758"]),                            # Boursault, letter to his son
    ("900098688", ["900098689"]),                              # Voltaire, Lettres philosophiques XXV
    ("900180351", ["900180352"]),                              # Sévigné in Gazaignes
    ("1500160077", ["1500160078"]),                            # Macquer, sel sédatif (run-on)
    ("1500160098", ["1500160099"]),                            # Macquer, Almaden
    ("10900271003", ["900212126", "900212127", "900212128"]),  # Lubersac, obelisk description
    ("10600055253", ["600028431", "10600055256"]),             # Lubersac, Discours
    ("600052226", ["600052224", "600052219", "600052220", "600052221", "600052223"]),  # Rafin, Pétition 1794
    ("900245782", ["900245784", "900245785"]),                 # Retz/Buissart hygrometer
    ("900155052", ["900155053", "900155054"]),                 # La Caille, decimals
    ("900117170", ["1500092201"]),                             # Leibniz, monads
    ("1200143938", ["1200143933"]),                            # Page on Pitt
    ("1200084311", ["1500000669", "1500000676"]),              # League arrêts
    ("900234749", ["900145905", "900145904"]),                 # Menagiana, ordeals
    ("1500085829", ["900145887", "900145889", "300029821"]),   # Menagiana, Grandier
    ("10900256883", ["10900256885"]),                          # Gilles Boileau, Didon's speech
    ("900233276", ["900233277"]),                              # Vandermonde
    ("1200030469", ["1200030470", "1200030473", "1200030474"]),  # Pagès copying Mézeray
    ("300002272", ["300002273"]),                              # Bayle quoting Mézeray, crusade
    ("600008852", ["600008853"]),                              # Code national / Mézeray
    ("900077563", ["900284635"]),                              # Ésope à la cour, governor scene
    ("900256594", ["900271010"]),                              # Prince de Conti 'dit' run-on
    ("900263198", ["900270636"]),                              # abbé losing his memory
    ("600012476", ["600012477"]),                              # Bodin, good king / tyrant
    ("1200078269", ["900144261"]),                             # discourse of 3 Feb 1751
    ("1500081014", ["1500081015"]),                            # Souvenel, Lettres
    ("1500043405", ["1500043406"]),                            # Le Pays letter via Joyeux
    ("1200141133", ["1200141130"]),                            # Mauriceau, caesarean
    ("300031906", ["300031907", "300031908"]),                 # Mauriceau, the nurse
    ("1200127733", ["1200127734", "1200141512", "1200127735"]),  # Racine to his son, reading
    ("1200127736", ["1200127737"]),                            # Racine to his son, Holland
    ("1200065757", ["10900265165"]),                           # Racine to Maintenon 1698
    ("1500033393", ["1500033392", "1500033394"]),              # Voiture, Corbie letter
    ("900265148", ["11200321529"]),                            # Daire, synodal statutes (run-on)
    ("1500082716", ["1500082717"]),                            # Noodt, prince/tyrant
    ("1500082746", ["11200318985"]),                           # Noodt, loi vivante
    ("600041459", ["600056184"]),                              # Beauharnais/Bourdon
    ("900321152", ["900321153"]),                              # protest v Sixtus V bull
    ("900140010", ["900140009"]),                              # anti-Jesuit prophecy
    ("1200139518", ["600052138", "11200322842"]),              # Poirier, Arras prisons
    ("900278549", ["900278550"]),                              # Le Tourneur notes, Winter's Tale
    ("900288719", ["900288720"]),                              # Grimod, Lorgnette
    ("10300143080", ["1500167493"]),                           # Sévigné, maréchal du Plessis
    ("1200146781", ["1200146783", "1200146780"]),              # Sévigné, spring 1672
    ("1200146845", ["1200146849", "1200146846", "1200146848", "1200146853"]),  # Sévigné, Pomponne 1679
    ("11200318245", ["1500167557", "1200146810", "1200146804", "1200146807", "1200146812"]),  # Sévigné, Turenne 1675
    ("1200118434", ["1200146881"]),                            # Sévigné, Livry
    ("900280746", ["900280747", "900280748", "900280749"]),    # La Chau, Orpheus gem
    ("900280754", ["900280755"]),                              # spintrian medals
    ("900280756", ["900280758", "900280762"]),                 # Secular Games gem
    ("10900316686", ["10900316687", "1200112645", "900259046"]),  # water-company Prospectus 1781
    ("900130867", ["1500190475"]),                             # Merlange certificate
    ("900300377", ["900300378", "900300379"]),                 # Amoreux, éloge of Linnaeus
    ("600051979", ["600051981"]),                              # Astruc, guaiac
    ("900187616", ["900187617", "900139431"]),                 # Duclos 1747 discourse
    ("10900164200", ["10900164201"]),                          # Paulmy 1748
    ("900232080", ["900227222", "1500165951"]),                # d'Alembert's portrait of Surian
    ("900227224", ["900236742", "900099880"]),                 # reply on Surian as preacher
    ("10900411437", ["10900411438", "10900411439"]),           # Vicq d'Azyr on Buffon
    ("300043918", ["10900346976"]),                            # Guibert on Thomas
    ("1500254813", ["11200318876"]),                           # Lassone report via Denman
    ("900226694", ["900226696", "900226698", "900226699", "900226703", "900226704"]),  # Cardonne tale of Sadi
    ("900308355", ["900308356"]),                              # Mulot, Ptolemy
    ("1200072386", ["1200072387"]),                            # Thomas via Robinet
    ("900186687", ["900186688"]),                              # Thomas, 1772 journals
    ("10600036019", ["10600036020"]),                          # Mézeray via d'Éon
    ("900007501", ["900007548"]),                              # Perrault, Ode sur la Paix
    ("900007173", ["1200067743", "1200067744"]),               # Perrault, reception speech
    ("900110664", ["900110663", "900110665"]),                 # Perrault, Dialogue de l'Amour et de l'Amitié
    ("300039040", ["300003594"]),                              # Anonimiana, Tacitus
    ("1500286256", ["600062614"]),                             # Hautefort on Sweden
    ("900203408", ["900207091", "900203406"]),                 # Formey/Gardanne, camphor
    ("900079344", ["900079346", "900079345"]),                 # La Font, Lettre 1746 motives
    ("900157140", ["900157141"]),                              # Jesuit sentence (run-on)
    ("1200096696", ["1200096699"]),                            # Formey on avocats
    ("300052892", ["300052893"]),                              # Collins
    ("300052884", ["900054563"]),                              # Collins
    ("900225962", ["900313203"]),                              # Émile I
    ("900257840", ["900083052"]),                              # Coyer, tax tariff
    ("900174737", ["900293372", "900293376", "900293377", "900293378", "900293379"]),  # Marchand, thunder essay
    ("900293357", ["900293358", "900293359", "900293360", "900293361", "900293362", "900293363", "900293365", "900293366", "900293367"]),  # Marchand, asses essay
    ("900293342", ["900293343", "900293344", "900293345"]),    # Marchand, preface
    ("900314275", ["900314276"]),                              # Hennet, preface
    ("900314279", ["900314280"]),                              # Hennet, Gospels
    ("1200126311", ["1200126312", "1200126313", "1200126314", "1200126315", "1200126316", "1200126317", "1200126318"]),  # Mulot/Carli
    ("600060135", ["600060136"]),                              # Destutt de Tracy in Say
    ("1500193485", ["1500193487"]),                            # Mella-Barral
    ("900043058", ["900043059", "900043062"]),                 # Vaumorière, Mecca letter
    ("900176281", ["900176283", "900176282"]),                 # Hemsterhuis (run-on?)
    ("1500136961", ["1500136962", "1200140357"]),              # Bazin, metamorphosis
    ("900242245", ["900242246", "900242247"]),                 # Théophile ode
    ("1200144419", ["10600082234", "1200146696"]),             # Ramel's letter to Génissieu
    ("10600081874", ["1200144153"]),                           # Army of Italy address
    ("1500172829", ["1500172831"]),                            # Winslow, the jaw
    ("1500247363", ["1500247367", "1500247370", "1500247371", "1500247372"]),  # La Chau, Psyche
    ("1500169377", ["11200316373"]),                           # Guénard
    ("1200122863", ["900259435", "1500203736"]),               # Winckelmann, Laocoon
    ("600059519", ["600059518"]),                              # Duverne's plan
    ("1500039075", ["1200022058"]),                            # Commynes
    ("900244030", ["900244032"]),                              # Paulet, sickroom
    ("1200100510", ["1200100511", "1200100512"]),              # Paulet, names of the diseases
    ("900293507", ["900293505"]),                              # Harris, the rector's nurslings
    ("900170557", ["900170556", "900170554", "1500181819"]),   # éloge of Verdier
    ("1200085186", ["1200085187", "1200085188"]),              # Almamoulin tale
    ("300027222", ["300027223"]),                              # Rollin, cadence
    ("1200110394", ["1200110395", "1200110397", "1200110402"]),  # Rollin, preachers
    ("1500249519", ["1500176581", "1500176570"]),              # Fléchier, Turenne oration
    ("1500249517", ["900137697"]),                             # Bossuet, Henriette-Marie oration
]
FOLD_T06 = [  # (keeper, [others]) from the t06 first readers' notes; short units only, long works left to the long-work rule
    ("300010348", ["300010349"]),                              # Malezieu, Divertissemens de Sceaux
    ("600030872", ["600042348"]),                              # Contrat social I.6 (short chapter)
    ("900145987", ["900145988"]),                              # Menagiana, syphilis
    ("1500118200", ["300002641", "300002642", "300002649"]),   # Mézeray via Bayle, Jeanne de Naples
    ("300000752", ["300000753", "300000754"]),                 # Mézeray, Jacqueline
    ("900014723", ["900100475", "300000764"]),                 # Mézeray, Liège
    ("29", ["30", "31"]),                                      # Costar on Voiture
    ("300019885", ["300019886"]),                              # Lambert on Descartes
    ("1500155641", ["1500155642"]),                            # Descartes tomb inscriptions
    ("10900022331", ["1200013512", "1200013513", "1200013514"]),  # Balzac, dissertation on the sonnet d'Uranie
    ("1500032682", ["1500032684", "1500032685"]),              # Costar on Scripture
    ("1500065596", ["1500065597"]),                            # Diemerbroeck, pelvis
    ("900253355", ["900254437", "900253356"]),                 # La Métherie, JdP
    ("1200061197", ["1200061202"]),                            # Fléchier, Turenne (oration: length?)
    ("10900155156", ["1200061225"]),                           # Fléchier, Turenne
    ("1200108093", ["10900155144"]),                           # Fléchier, Turenne
    ("900006829", ["1200061231"]),                             # Fléchier, Turenne
    ("900174312", ["1200046441"]),                             # Fléchier, Dauphine
    ("1200142229", ["10600079802"]),                           # Carra, Système (gap)
    ("1500083817", ["1500064655"]),                            # Charas, venom
    ("1200135779", ["600020577"]),                             # Bastille narrative
    ("300049536", ["600055681", "1200132168"]),                # EL XXIII.29
    ("1200103873", ["11200322258", "900202401"]),              # EL VI.2
    ("600008904", ["1200133117"]),                             # EL II.4
    ("1500277474", ["600062390"]),                             # Considérations sur la Pologne IV
    ("900086483", ["900123635"]),                              # Callières, Gustave-Adolphe's speech
    ("1200018421", ["1200018427"]),                            # Callières, nobles and trade
    ("1500143588", ["1500143602", "1500143605", "1500143613"]),  # Guettard table
    ("1200022343", ["1200022342"]),                            # La Fortune de la Cour, Thomas More
    ("11200326454", ["900026658"]),                            # Richer retraction
    ("1500203677", ["300042836"]),                             # Winckelmann, bronze
    ("900019529", ["900019530"]),                              # Ménerville funeral discourse
    ("1200116620", ["1200116621"]),                            # Mayeur / Gazette noire
    ("1200116633", ["1200116634", "1200116635"]),              # Mayeur / Gazette noire
    ("1200125479", ["1200125480"]),                            # Mayeur / Gazette noire
    ("1200065601", ["1200065602"]),                            # Pro Quinctio in French
    ("900302353", ["900302354"]),                              # Hardy, Théagène
    ("900257747", ["900257748"]),                              # Rigoley on Corneille
    ("1200058157", ["1200058158"]),                            # Fourmont / Mirabaud
    ("900076967", ["900076968"]),                              # Dole
    ("900059548", ["900059549"]),                              # Réaumur, gallinsects
    ("900060968", ["900065521"]),                              # Réaumur, flies
    ("900065522", ["300031212"]),                              # Réaumur, flies
    ("300028666", ["300028668"]),                              # Réaumur, kermès
    ("900065543", ["900061758"]),                              # Réaumur, heart
    ("900065544", ["900065545"]),                              # Réaumur, plane
    ("900083670", ["900092238", "900088935"]),                 # Maupertuis, definitions
    ("10900260585", ["1200103008"]),                           # Bailly, Éloge de Molière anecdote
    ("900237726", ["900237727"]),                              # Pagès, Louis XIV's speech
    ("900237833", ["900237718", "900236023"]),                 # Pagès, Fénelon's lessons
    ("1500011985", ["1500011986"]),                            # La Chèze / Senlis
    ("900039836", ["11200327102"]),                            # Jeanne d'Arc, sermon 1431
    ("1500107979", ["1500107981", "1500107982"]),              # Montereau 1419
    ("900040870", ["900039835"]),                              # frère Richard
    ("900285361", ["1500259496"]),                             # Le Gros
    ("900211770", ["900214829"]),                              # Lafisse, Discours
    ("1500258556", ["1500258559"]),                            # magnetism report 1784
    ("1200030496", ["1200030495"]),                            # Mézeray, Navarre mines
    ("1200030388", ["1200030389"]),                            # Mézeray, Saint-Quentin
    ("1200128936", ["1200128937"]),                            # Mézeray, Duprat
    ("1500116712", ["1500116794", "1500116793"]),              # Réaumur, bee hairs
    ("11200322429", ["1500116924"]),                           # Réaumur, queen/drone
    ("1500117218", ["1500117220"]),                            # Réaumur, caterpillar moults
    ("900236442", ["900236444", "300042378", "300042379"]),    # La Peyronie case history
    ("1500153398", ["1500153399", "1500153400"]),              # Bréquigny, Genoa
    ("900329378", ["900328913"]),                              # Legouvé, Mélancolie (length?)
    ("1200076033", ["900304480"]),                             # Destouches, Philosophe marié
    ("300020544", ["300020545"]),                              # La Martinière
    ("1200103501", ["1200103502", "1200103505"]),              # Gonthier case
    ("900300767", ["900300771"]),    # 's Gravesande, logic
    ("1500287598", ["1500286445"]),                            # Bonaparte, Arcole
    ("900207088", ["900209550"]),                              # Gardanne, drowned rescue (run-on)
    ("1500230833", ["1500230941"]),                            # mercurial pill
    ("900193640", ["900193639", "900193641"]),                 # Arbuthnot preface
    ("900111030", ["900111031", "900111032"]),                 # Vandermonde, mucilage
    ("1500048218", ["300007069"]),                             # Charas, cinnamon
    ("1500079612", ["1200134925"]),                            # Lettre d'un Sicilien
    ("1500040508", ["600009404", "600008862"]),                # Commynes V, taxes and Estates
    ("1200030511", ["1200030513"]),                            # Nevers, Amiens
    ("1200030531", ["1200030529"]),                            # Henri IV to Nevers
    ("900264018", ["900272452"]),                              # Touzla boatman's speech
    ("300054996", ["300054997", "300054981"]),                 # Mirabaud, Druids and Gauls
    ("900230720", ["11200320908"]),                            # Éloge de Voltaire
    ("11200323987", ["11200323986"]),                          # Mirabaud, rewards of virtue
    ("900003511", ["900003512", "900003513", "900003514", "900003516", "900016598"]),  # Choisy reception discourse 1687
    ("900007845", ["900007846", "900007847", "900007848", "900007852"]),  # Tournefort preface via NRL
    ("900007856", ["1200073591"]),                             # Tournefort, vomiting
    ("300013178", ["300013179"]),                              # Tournefort, morgeline
    ("900188446", ["900188447", "900188448"]),                 # Heinecken, Biblia pauperum
    ("900301065", ["1500260304", "900301070"]),                # Coxe, life of Linnaeus
    ("900267674", ["900267675"]),                              # Andry, magnet report
    ("11200314644", ["900083673"]),                            # Maupertuis, Essai de philosophie morale
    ("900305780", ["900305781"]),                              # Crêpe, convulsions
    ("1200086432", ["1200086433"]),                            # Tournefort, mélilot
    ("900237850", ["900237848", "900239019"]),                 # Büsching, Guanches
    ("900211119", ["900211120"]),                              # Deforis on faith
    ("1200099505", ["1200108200"]),                            # Émile IV, Jewish books
    ("1500195823", ["1500195830"]),                            # Émile IV, revelation
    ("900056053", ["900060779"]),                              # Boureau-Deslandes, Xénophane
    ("300018557", ["300018558"]),                              # Boureau-Deslandes, Aristotle on offerings
    ("1200118903", ["1200107052"]),                            # flatterer's speech in verse
    ("900180732", ["900180711", "900180757", "900180768"]),    # Port-Royal doctors' requête
    ("900290868", ["900290870"]),                              # Yvon, plan of the work
]
FOLD_T07 = [  # (keeper, [others]) from the t07 first readers' notes; short units only, long works left to the long-work rule
    ("300019486", ["300019488", "300019489", "300019490"]),    # Encyclopédie BRAYER (short article?)
    ("1500129556", ["1500129557"]),                            # Portal on Blegny, one anecdote
    ("300032938", ["300032939"]),                              # Encyclopédie paraphimosis
    ("300009297", ["300009298"]),                              # Trévoux effervescence
    ("300009724", ["300009725"]),                              # Trévoux cancer
    ("900187025", ["300038490", "300038491"]),                 # La Peyronie axe-wound case history
    ("300020338", ["300020340", "1200080911"]),                # Dionis on charlatans
    ("900158207", ["900158208"]),                              # Dionis, prejudice against surgeons
    ("300022975", ["300022976"]),                              # crooked fingers
    ("300015515", ["300015516"]),                              # rugines
    ("1500129543", ["1500227872"]),                            # Daran quoting Dionis on carnosities
    ("1500250158", ["1500250159"]),                            # Bourrit, Chimborazo
    ("900262500", ["900262501"]),                              # Bourrit, Devil's Bridge
    ("900240289", ["900240290"]),                              # Lens, preface
    ("1200142294", ["1200142295"]),                            # Highland music / Glengarry
    ("600046547", ["900250320"]),                              # Contrat social II.7, one paragraph
    ("900288624", ["900288625"]),                              # Bourrit
    ("900262487", ["900262489"]),                              # Bourrit, Valais people
    ("1500233080", ["1500233081", "1500233082"]),              # Büsching, Candia
    ("600028476", ["600028473"]),                              # Baudisson
    ("1200089337", ["1200089341", "1200089345"]),              # Plato via Dacier
    ("300044971", ["300004148"]),                              # Liger, horse teeth
    ("10300019249", ["10300019251"]),                          # Liger, dovecotes
    ("900288506", ["900288508"]),                              # Büsching, agriculture (footnote letters)
    ("600065407", ["600065408"]),                              # Maihows
    ("900117218", ["900117223"]),                              # de Fonte narrative
    ("1500064250", ["1500064251"]),                            # Lamy/Malebranche, pure love
    ("1500232948", ["1500232949"]),                            # Pernety, forehead
    ("1500103420", ["1500103421"]),                            # Houtteville, Providence (run-on)
    ("1500180057", ["1500180058"]),                            # Jèze, Enfants-Trouvés
    ("300037470", ["300037469"]),                              # Du Marsais, construction louche
    ("900108654", ["900108655", "900108656"]),                 # Du Marsais in JdS 1757 review
    ("10300039598", ["10300039599"]),                          # antiphrase/euphémisme
    ("10300085688", ["1500108704"]),                           # euphémisme
    ("300024620", ["300024621"]),                              # mots funestes
    ("1500060387", ["11200322364"]),                           # Dionis, rotule
    ("900134990", ["900134232", "1500190539"]),                # Profession de foi, miracles paragraph
    ("900077140", ["900077141", "900077142"]),                 # Deslandes on Lulle
    ("900147759", ["900147760", "900153004"]),                 # Baumé, distilled waters method
    ("300014436", ["300014437"]),                              # Trévoux PIVOT
    ("1500081717", ["1500081718"]),                            # Chomel, églantier article
    ("900243444", ["900243447"]),                              # Corsican shepherds anecdote
    ("1500098275", ["1500098276", "1500098277"]),              # Daniel, Utrecht/Régius
    ("1500098413", ["1500098416"]),                            # Daniel/Cajot
    ("1500183316", ["1200135005"]),                            # Fléchier, Montausier
    ("900126422", ["900126423", "900126424"]),                 # d'Açarq, verbs (one review)
    ("900130903", ["900130904", "900130905"]),                 # d'Açarq, moods (JdS 1762)
    ("900121452", ["900121453"]),                              # Ramsay, Plato
    ("900121454", ["900121457"]),                              # Ramsay, golden age
    ("900036884", ["900036885"]),                              # Ramsay, Cyrus in JdS
    ("1200065122", ["1200065123"]),                            # Rivière, Temple de Cythère
    ("300037479", ["300037478"]),                              # La Chambre on the senses
    ("300049499", ["300049498", "300049500"]),                 # Baumé, drying roots
    ("900276663", ["900276664"]),                              # fairy tale
    ("900164335", ["900164336"]),                              # Du Perron, poem on Mary Stuart
    ("900288627", ["900288629"]),                              # Bourrit, St Bernard hospice
    ("1500129484", ["1500129486", "300008892"]),               # Dionis, diérèse
    ("300037634", ["300037635"]),                              # Encyclopédie SÉTON
    ("1500071287", ["300040555"]),                             # Liger, vine planting (run-on)
    ("300018226", ["1500071310", "300018227"]),                # Liger, andouilles recipe
    ("900093696", ["900093697"]),                              # Justi, teintures de Saxe
    ("300044020", ["300044021"]),                              # Isaiah 53:5-6
    ("600030432", ["600030433"]),                              # Pey on Grotius (run-on)
    ("600026350", ["600026351"]),                              # Pey
    ("300026525", ["300026526"]),                              # Léon, the ghet
    ("300007133", ["300007134", "300007137"]),                 # Karaites
    ("1200123084", ["1200123086"]),                            # Frederick II letter in Guibert
    ("900272787", ["900272788"]),                 # Parmentier, army provisions
    ("300045798", ["300045800"]),                              # Stapart
    ("900194337", ["900194338", "900194339"]),                 # Germanes on Neuhoff
    ("900145834", ["900085644"]),                              # Simon examination anecdote
    ("300005743", ["1200058500"]),                             # Léon, ark
    ("300038818", ["900042739"]),                              # tefillin
    ("10300058653", ["1200058504"]),                           # alms
    ("900004850", ["300033190", "300033191", "300033192"]),    # Passover
    ("900062334", ["900042109", "900062336", "900062337", "900163116"]),  # Du Marsais, figures I
    ("300039803", ["900058021"]),                              # uses of tropes (numbered list)
    ("900211434", ["900211435"]),                              # Vaugelas, vers dans la prose
    ("1500047308", ["1500047309"]),                            # Lemery, silver crystals
    ("10300058663", ["1200058520", "1200027807", "900059028"]),  # Simon, Greek errors list
    ("300031660", ["300031663"]),                              # Nestorians
    ("300055130", ["300055136"]),                              # Vanini (near run-on)
    ("900115016", ["11200317942", "900025451"]),               # Vanini's end
    ("300025336", ["300025338", "300025341"]),                 # La Chambre, rules for scripture
    ("300055836", ["1500121977"]),                             # Matt 16:17-18
    ("900121588", ["900121589", "900121590"]),                 # Gerdil
    ("900121592", ["900121593", "900121594"]),                 # Gerdil
    ("300013840", ["300029793"]),                              # Belidor, pilots
    ("1500171225", ["1500171230"]),              # plaidoyer, religious profession
    ("900115590", ["900115591"]),                              # François, gift of tongues
    ("1500158866", ["1500158868"]),                            # Bossuet DHU
    ("1500207651", ["1500207652"]),                            # Genesis 2-3
    ("11200324877", ["1500034968", "11200324878"]),            # La Chambre, preface
    ("1500060476", ["1500060477"]),                            # Dionis
    ("1500060489", ["1500060493", "1500060494"]),              # Dionis, uterus
    ("1500060502", ["1500060505", "1500060506"]),              # Dionis, external parts
    ("300009179", ["300009180"]),                              # pericardium
    ("10900176622", ["1500132420"]),                           # Filles-Dieu custom
    ("1500132604", ["1500132607"]),                            # Billettes miracle
    ("1500132647", ["1500132650"]),                            # Hospitalières
    ("300029761", ["300029769"]),                              # cendrée de Tournay
    ("300029764", ["300029765"]),                              # Belidor, salts
    ("900179028", ["11200324447", "11200324448"]),             # Kaempfer, Nagasaki festival
    ("300025381", ["300025382"]),                              # Bourgelat, tissu cellulaire
    ("10600066723", ["600032392"]),                            # Exposition des principes, closing
    ("1200028012", ["1200028011", "1200028013"]),              # de Piles, honour of painting
    ("1200027972", ["1500043859", "1500043858"]),              # de Piles, passions
    ("900094703", ["1500043871"]),                             # de Piles, advice
    ("1200122855", ["1200080869"]),                            # de Piles, drapery
    ("900170013", ["900170014"]),                              # Rigoley, Mémoire pour l'asne
    ("1500133063", ["1500133062"]),                            # Brice, one hôtel
    ("300037686", ["300037687"]),                              # Kaempfer, pyramid tower
    ("1500106772", ["300040364"]),                             # Kaempfer, varnish tree
]
FOLD_T08 = [  # (keeper, [others]) from the t08 first readers' notes; short units only, long works left to the long-work rule
    ("1500066440", ["1500066441"]),                            # Parodies bachiques 1696, one song?
    ("900250932", ["900250933"]),                              # translator's preface, Extrait de Roland 1780
    ("900155490", ["900155491", "900155492"]),                 # Pellerin Supplément, one review extract
    ("1200124248", ["1200124250", "1200124251", "1200124252", "1200124253", "1200124254", "1200124228"]),  # Mesmer, Paradis affair narrative
    ("1200119411", ["1200119407"]),                            # Mesmer's propositions
    ("1200124256", ["1200124257"]),                            # Mesmer's arrival in Paris
    ("900086522", ["900086524", "900086525", "900086526"]),    # Béthune, Mercure (L'Épilogueur), one narrative
    ("900086488", ["900086486"]),                              # Béthune, marriage contract / wife's liberties (run-on?)
    ("900110253", ["900110254"]),                              # La Beaumelle, Roi toujours coupable
    ("1200145959", ["1200145960"]),                            # Favart, Bastien et Bastienne, two airs
    ("1500030417", ["1500030418", "1500030419"]),              # Vigier, Baudouin testament case
    ("900304893", ["900304894", "900304895"]),                 # Anquetil, palanquin description
    ("900056548", ["900056547"]),                              # Kaempfer, house garden
    ("300050067", ["1500107132", "1500107133"]),               # Kaempfer, tea processing
    ("1200073771", ["900133179", "300032834", "1500107142"]),  # Kaempfer, paper-making
    ("1500106958", ["1500106965"]),                            # Kaempfer, goods lists
    ("900112218", ["900112219"]),                              # Chamousset, cases
    ("1500067143", ["1500027769"]),                            # Vaugelas, menté-je remark
    ("1500045678", ["1500027646"]),                            # Vaugelas, poitrine/face remark
    ("1500061834", ["1500061835"]),                            # La Bruyère, Des biens de fortune, one remark
    ("1500061888", ["1500061889"]),                            # La Bruyère, Du souverain, final remark
    ("300008905", ["900021410"]),                              # Préface, Analyse des infiniment petits
    ("600037330", ["600040467", "600042338"]),                 # Contrat social II.7, short chapter
    ("600040264", ["600054180"]),                              # Contrat social III.15
    ("1500048044", ["1500048048", "1500048055"]),              # Tavernier, Saint-Amant / Dom Philippe anecdote
    ("1500246133", ["1500246134"]),                            # Condillac Logique via Lavoisier, one excerpt
    ("1200108239", ["1200108240"]),                            # Maubert, Lettres iroquoises, one letter
    ("10900153520", ["10900153521"]),                          # satirical portraits of hero and heroine
    ("900327505", ["1200113624"]),                             # Franklin, Way to Wealth speech
    ("1500211732", ["900195834"]),                             # Pernety, hummingbird
    ("11200313965", ["11200313956", "11200313948"]),           # J.-B. Rousseau's letter on Voltaire in Brussels
    ("10900342690", ["900283648", "900283650"]),               # Travenol affair narrative
    ("900330395", ["1200145839", "1200148374"]),               # Voltaire, Sophonisbe, one scene?
    ("1200140480", ["1200140482", "900302939"]),               # Franklin, Avis (short pamphlet)
    ("900099217", ["10900296279"]),                            # Turpin de Crissé verse, one poem?
    ("1500212926", ["1500212927"]),                            # letter reproaching Voltaire
    ("600049436", ["600049437"]),                              # Mérindol narrative
    ("900271947", ["900272903"]),                              # one speech, Journal de Nancy 1784
    ("900057562", ["900147032"]),                              # Vie du P. Coton, one anecdote
    ("1500162797", ["1500162798", "1500162799"]),              # La Marre, Titon et l'Aurore airs
    ("600046251", ["600046252", "600046253"]),                 # Belidor, Roman aqueducts paragraph
    ("900204833", ["900204836"]),                              # Maret on sea-bathing, one abstract
    ("1200027645", ["1200027646", "1200027653", "1200027654"]),# Spanish Regents' letters 1700
    ("1200055494", ["1500071864", "11200317577", "1500071866"]),  # French memorial to the States General
    ("900016459", ["900009946"]),                              # Académie harangue to Philip V
    ("900157380", ["900157381"]),                              # Monpersan, procession story
    ("1500005797", ["900140377", "900140378", "1500131196"]),  # Châtel pyramid inscriptions
    ("300001944", ["1500050168", "1500050169", "1500050170"]), # L'Hôpital's testament
    ("1500040524", ["1500040525"]),                            # Thévenot, arrow divination
    ("900109330", ["900109331"]),                              # Choisy letters
    ("1500067322", ["900007192", "1500069139"]),               # harangue to Louis XIV
    ("1200081834", ["1500067736"]),                            # Athalie II.5?
    ("900180698", ["900180699", "900180700"]),                 # Saint-Évremond, Canaye and the horse
    ("900029242", ["900180695"]),                              # Saint-Évremond, La Frette
    ("900146006", ["300034180"]),                              # Huetiana, burns on leaves
    ("900146000", ["900146001"]),                              # Huetiana, Roman roads
    ("900280995", ["900280996"]),                              # Bertholon, colic remedy
    ("1500239527", ["1500239530", "1500239525"]),              # Ehrmann, Instruction on bites
    ("1500165335", ["1500165337"]),                            # one magistrate's speech
    ("1500165392", ["1500165395"]),                            # ambassador's letter from Trent
    ("1200137767", ["900203671"]),                             # Delisle de Sales, apostrophe to conquerors
]
FOLD_T09 = [  # (keeper, [others]) from the t09 first readers' notes (server batches 0-19 + here 20-24); short units only
    ('300014105', ['300016843']),  # La Quintinie avant-pêche / pêche de Troie, keeper row carries the candidate
    ('300014583', ['300015629']),  # pomme-rose / pomme sans fleurir, front row carries both
    ('300006638', ['300006639', '300006640', '300006641', '300006642']),  # Bon-chrétien, one stretch into Trévoux
    ('300016457', ['300016458']),  # Trévoux terre neuve article
    ('300010616', ['300043745']),  # FRUIT article
    ('300013473', ['300013474']),  # NOUER article
    ('300012011', ['300012012']),  # jauge / fumer à vive jauge
    ('300016418', ['300016419']),  # tempérament de terre
    ('1500238571', ['1500238572']),  # Navier, one procedure
    ('300015837', ['300006538']),  # serfouir / béquiller
    ('300005445', ['300043467']),  # fumier
    ('300005732', ['300005733']),  # choosing a tree, Trévoux ARBRE
    ('300011985', ['300016339', '300016244']),  # tailler article
    ('1500067343', ['1500067394']),  # planting instructions
    ('300010090', ['300006797', '300006798', '300006799']),  # branche cluster
    ('1200145883', ['1200145884']),  # Boissy, Les dehors trompeurs, one scene
    ('1500048929', ['1500048930']),  # Malebranche propositions in Lamy
    ('300008188', ['300008189']),  # Corinthe grape
    ('1500254962', ['1500253877']),  # Détail 1782, visible run-on
    ('300050313', ['300050334']),  # Laborie, mitte, shared text
    ('900110219', ['900110220', '900110221']),  # one quotation in Le Febvre
    ('900028406', ['900028407']),  # Koran sura 27
    ('900028404', ['900028405']),  # Koran sura 18
    ('300014565', ['300014566', '300014567', '300014569']),  # Simon, polyglot Bibles, one article
    ('300041131', ['300041132']),  # Simon, two judgements quoted together
    ('900247613', ['900251845']),  # animal trials, one passage
    ('900016590', ['900016591']),  # éloge of Bourdaloue
    ('900180597', ['1500077155', '1500077157']),  # bishops' letter to Louis XIV
    ('600002274', ['600002275']),  # one letter praising the Jesuits
    ('1500059611', ['1500059612']),  # Sainte-Beuve cas de conscience
    ('1500046674', ['1200078851']),  # Matthew 18:15-18 pericope
    ('1500090772', ['300013399']),  # Vaugelas remark on the ear
    ('300035535', ['1200129661']),  # Montaigne II.5 torture
    ('900292604', ['900292605']),  # Crusoe and Friday, one conversation
    ('300018088', ['300018089', '300018090']),  # Malebranche pure love, one quotation
    ('900094389', ['1200103225']),  # Rapin, one paragraph
    ('1500045719', ['1500045720', '1500045721']),  # Crasset Passion stations
    ('1500178065', ['1500178066']),  # Lafosse nail injuries
    ('300043366', ['300043367']),  # Lafosse pleurésie
    ('300043364', ['300043365']),  # pulmonie
    ('300043394', ['300043395']),  # suppression d'urine
    ('300043391', ['300043392', '300043393']),  # hydropisie
    ('300043400', ['300043401', '10300119843', '300043403']),  # rage
    ('300043223', ['300043224']),  # col / mal de garrot run-on
    ('300043304', ['300043306']),  # saignée du col
    ('300043267', ['300043268']),  # cheval morfondu
    ('300043324', ['300043325', '300043326', '300043327']),  # trépan
    ('300043335', ['300043336', '300043337']),  # queue à l'angloise
    ('900228267', ['900228268', '900228269']),  # farcin in 1778 journals
    ('10900229658', ['10900084852']),  # Manon Lescaut, one scene?
    ('900255592', ['900252274', '10900313357', '900235166']),  # Boufflers letter from Switzerland
    ('900252276', ['1200102502']),  # Voltaire épître to Boufflers
    ('900252275', ['900253529']),  # Boufflers verse to Voltaire
    ('300043344', ['300043345']),  # Lafosse vertigo
    ('300043347', ['300043348', '300043349', '300043350']),  # Lafosse mal de cerf
    ('11200326352', ['11200326351']),  # gourme maligne
    ('300043300', ['300043297', '300043298']),  # Lafosse fractures
    ('300043239', ['300043240']),  # clou de rue
    ('300018030', ['300018031']),  # Bougeant, one argument
    ('900210258', ['900210259']),  # Tessin, one letter
    ('900038231', ['900038233']),  # life of Vaillant
    ('900175006', ['900175007', '900175008', '900175009', '900175010', '900175011']),  # Le Camus, one argument reviewed
]
FOLD_T10 = [  # (keeper, [others]) from the t10 first readers' notes (server run 28 Oct); short units only
    ("1200127841", ["1200130679"]),  # Voltaire, Charles XII VIII, Stralsund bomb anecdote
    ("900290816", ["1500182612"]),   # Rousseau, Lettre à d'Alembert, apostrophe of a few lines
    ("900145978", ["900145979"]),    # Varillasiana, Psammetichus anecdote
    ("900145956", ["900145957", "900145958"]),  # Varillasiana, Naples remark (unsure)
    ("1500166244", ["1500166245"]),  # Lafosse 1754, objections and replies
    ("11200324750", ["11200324754"]), ("11200324753", ["11200324749"]), ("1200095384", ["1200095385"]),  # Castera
    ("300001616", ["1200103172"]),   # Monconys, Loudun prioress anecdote
    ("900033303", ["900079665"]),    # Oratoire 1678 act, session 6
    ("1200109545", ["900248053"]),   # Montlinot, hospital manufactures paragraph
    ("900210264", ["900210271"]),    # Tessin letter?
    ("900039852", ["300051344", "900066346"]),  # Boileau's reported speech in d'Olivet
    ("900068398", ["10900405504"]), ("900042014", ["900110932"]), ("900060726", ["1500108252"]),
    ("900043794", ["900141900"]), ("1500108312", ["1500108313"]),  # d'Olivet / Fontenelle paragraphs
    ("900266156", ["900278583"]),    # translator's avertissement to Bradley
    ("900308014", ["900163476", "900163477"]),  # Masque de fer anecdote
    ("900173075", ["900173076"]), ("1500129395", ["1500129396"]), ("10900242971", ["300049950"]), ("900082980", ["900082986"]),
    ("1500055674", ["1500055675"]),  # Sainte-Marthe epitaph
    ("1200046719", ["1200046721"]), ("1500046199", ["1500046198"]),  # Malebranche paragraph; Gassendi objection
    ("900164190", ["900164191"]),    # Artaud, one short letter
    ("1200126354", ["1500188002"]),  # burlesque preacher sayings
    ("900276982", ["10900340173"]),  # Rotrou scene?
    ("300038898", ["300038899"]), ("300050632", ["300050633"]), ("900072730", ["900072734"]),
    ("1200097019", ["1200078585", "1200078586", "1200078587", "1200078588"]),  # Claudius' Lyon speech
    ("900221057", ["900221059"]),    # 1636 Saint-Jean-de-Losne act
    ("900094807", ["900094808"]),
    ("300053889", ["300053890"]), ("300053898", ["1200092133"]), ("900124234", ["900124235", "900087104"]),
    ("900098755", ["900124187"]), ("300048746", ["900119645"]), ("900124215", ["900098753"]),  # Diderot, Pensées
    ("900099129", ["10900158255"]),  # Condillac dedication
    ("1200080019", ["1200080059", "1200080058", "1200080057", "1200080018"]),  # Collins, list of admissions
    ("1500203533", ["600031207", "1500212523"]),  # La Ville plaidoyer via Bouchotte
    ("300019575", ["300019573"]), ("900119599", ["900119597"]),
    ("900122491", ["900220699"]),    # J.-B. Rousseau ode
    ("1500111916", ["900110921"]), ("1500111919", ["1500111920"]), ("11200327153", ["11200327152"]),  # Lebrun
    ("900111609", ["1200072496"]), ("900102213", ["1200072474"]),  # Diderot, Interprétation
    ("1500212274", ["1500212311"]), ("1200079760", ["900116265"]),
    ("1200045351", ["1200045352", "1200045353", "1200045354"]), ("300034038", ["300034039"]),  # Tourreil
    ("900182966", ["900182968", "900182978"]),  # Brie shepherds case
    ("1500066027", ["1500066029", "1500066031", "1500066033"]),  # Érard plaidoyer
]
FOLD_T11 = [  # (keeper, [others]) from the t11 first readers' notes (server run 30 Oct); short units only, tirade rule
    ("900173966", ["900035662"]),    # Louis XIV to Fabert, the Cordon bleu letter
    ("1500065955", ["900008990", "900138847"]), ("1500065972", ["900007103", "900218907"]),  # Perrault, Hommes illustres: Duquesne; d'Herbelot
    ("900013852", ["1200037909"]), ("900014174", ["900043764"]),  # Perrault: Varin; La Fontaine
    ("900020611", ["900036634", "900036638"]),  # Perrault on Patru (third doubtful)
    ("1500065957", ["900205261"]),   # Patru, Éclaircissemens sur l'Astrée (only if a short letter)
    ("10600041492", ["900243148"]),  # Champlair, ordre procedure paragraph
    ("1500284033", ["1500284035"]),  # Montesquiou's dispatch, Sept 1792
    ("900047718", ["900047719", "900047720", "900047721"]),  # académique éloge of Tourreil
    ("1200045470", ["900048447"]),   # Tourreil's Philip bons mots (Rollin)
    ("1500254983", ["1500254984"]),  # La Borde on the Rose-Croix
    ("300015337", ["900037490"]),    # Martin, the Rhine as judge of adultery
    ("300050919", ["900033959", "300050920"]),  # homage to a bishop (Piganiol / Beaunier / HLE)
    ("1200086523", ["1200086525"]),  # charbon, short article
    ("900270233", ["900248280"]),    # Julius Caesar III.2, Antony's oration (Le Tourneur)
    ("1200093440", ["900273109"]),   # Crébillon, Idoménée I.1, the storm récit (tirade)
    ("1200107096", ["1200107051", "1200107042"]),  # J.-B. Rousseau (?) ode
    ("900186689", ["900329795"]),    # "L'effort d'une vertu commune" ode stanza
    ("1500178621", ["11200308863", "11200308864"]),  # verse-and-prose Loire voyage
    ("1500263482", ["1500068495", "900168924"]),  # duchesse de Liancourt's portrait
    ("300019062", ["900144691"]),    # Tatian, Oratio ch. 1 (Deslandes)
    ("300042461", ["300042462", "300042463", "300042464"]),  # genre diacommatique article
    ("300005180", ["300005176"]),    # Pitaval, penalties for adultery
    ("10300111594", ["300041266"]),  # Villiers case speech
    ("1500124017", ["1500124018"]),  # Harlay, the "vieux singe"
    ("1200085359", ["1200085360", "1200126616"]),  # Sévigné on the Brinvilliers
    ("900210830", ["900210831"]),    # Pitaval / AL 1775 dialogue scene
    ("1500123503", ["1500123504"]),  # Pitaval, "la guerre de l'écritoire"
    ("900217097", ["900228459"]),    # Saurin to Mme Voisin 1710
    ("300013339", ["300013341"]),    # Nompareil narcissus passage
    ("1500172135", ["1500172136", "900222215"]),  # La Caze on Boerhaave (section of a few pages?)
    ("900164487", ["900164488"]),    # La Caze on the newborn
    ("900011656", ["900011657"]),    # Andry/Lémery, bone nutrition
    ("900107972", ["300011146"]),    # Deshoulières (?) on gambling, one poem
    ("1500072913", ["900016700", "900017537", "900017536"]),  # HARS 1708, worm in the frontal sinus
    ("900069904", ["900012268"]),    # Fontenelle, HARS 1700 on Dodart
    ("1500124195", ["11200327160"]), # the lady's speech in the Pitaval cause
    ("900110864", ["900129598", "900102745"]), ("1200050960", ["900142463"]), ("1500072027", ["900030480"]),  # Ps 67, 9, 71 (one poem if within the poem limit)
    ("1500123695", ["1500123696", "1500123698", "1500123699"]),  # Gardel to Beon, letter
    ("300029685", ["300029686", "300029687"]),  # Pitaval in ASSASSINAT
    ("600047239", ["1500262326"]),   # EL V.2, short chapter
    ("900238156", ["900226720"]),    # Castilhon, Sou-Ou anecdote
    ("1200146716", ["1200146715"]),  # Bonaparte to the Anciens, 18 brumaire
    ("1200146718", ["1200146720", "600064972", "1200146722", "1200146723"]),  # Bonaparte at Saint-Cloud
    ("900197155", ["900197156"]),    # Grandier's execution anecdote
    ("900290758", ["900290759"]),    # Brun de la Combe, projected decree
    ("1500259636", ["1500259637"]),  # Halle au blé dome
    ("900147368", ["900147369"]),    # romance, consecutive stanzas
    ("1500184698", ["900132886"]),   # Favart, Annette et Lubin, one song
    ("1500282421", ["600055832", "1200142263"]),  # Louis XVI's testament (3-4 pp)
    ("900083760", ["900083761", "900083762"]),  # prize discourse on gloire
    ("1500225742", ["1500225743"]),  # Lignac, Russian baths
    ("900291957", ["900291958", "900291959"]),  # Lombard 1786 review extract
]
FOLD_T12 = [  # (keeper, [others]) from the t12 first readers' notes (31 Oct); short units (Glenn 31 Oct: a page or two is one unit)
    ("1200101512", ["1200101513"]),  # poissard dialogue song
    ("900317012", ["300051872"]),  # Palissy anecdote
    ("900296166", ["900296167"]),  # Villenfagne note
    ("1200041968", ["1500142546"]),  # death of Osman
    ("1500061692", ["1500053761"]),  # Ps 83
    ("1500053941", ["1500053944"]),  # Ps 148
    ("1500052980", ["1500052985"]),  # Ps 36
    ("1500053551", ["1500053802"]),  # Mt 23,37
    ("1500053407", ["1500053005"]),  # Mt 25,31-46 pericope
    ("900140447", ["900140449"]),  # Jaureguy anecdote
    ("900295796", ["900296774"]),  # L"Estoile, the Italian ex-slave
    ("900081577", ["900028329"]),  # L"Estoile entry, Cardinal de Lorraine
    ("300016324", ["10300119053"]),  # philosophers" drinking song
    ("900276781", ["900276786"]),  # drinking song
    ("1500101233", ["600044317"]),  # Epicurean song
    ("900271175", ["900279121"]),  # moine poem
    ("1500099466", ["1500099469"]),  # dialogue song
    ("900243401", ["900243403"]),  # boudoir song
    ("1200112378", ["900265037"]),  # Cléophile song?
    ("900045489", ["11200317725"]),  # Du Cerceau épître (length?)
    ("900045486", ["10900295563", "10900295564"]),  # Du Cerceau, La Nouvelle Eve
    ("300011252", ["300011157"]),  # Du Cerceau, soldier portrait
    ("1500172650", ["300032688"]),  # Alix et Alexis romance?
    ("600036873", ["600036871"]),  # Confession générale de Joseph II pamphlet?
    ("1200142511", ["900242347"]),  # Elvire romance
    ("300038449", ["300038450"]),  # Bacon, Of Superstition (Deleyre)
    ("300031146", ["300031147"]),  # Bacon, Of Death
    ("900104648", ["900104647", "900104636"]),  # Bacon, Of Nobility
    ("900265296", ["600022919"]),  # Tom Jones, Allworthy"s speech
    ("1200066653", ["1200066655"]),  # Lattaignant echo song
    ("900190522", ["900190521", "900190519", "900190520"]),  # Gazette du commerce 1772 article on amurca
    ("600065369", ["600065370", "1500210073", "600031064"]),  # Déclaration du clergé 1682 (one page)
    ("900259418", ["900258458"]),  # short review
    ("1500134110", ["900073082", "300020410"]),  # Geoffroy, Table des rapports 1718
    ("900288342", ["900288344", "900288346", "1500255596", "900288347"]),  # Lagrenée preface (short?)
    ("900043490", ["900043491"]),  # Franco lithotomy anecdote
    ("900118382", ["900118383", "900118384", "900118385"]),  # Lebrun"s letter of questions
    ("1500076686", ["1500076687"]),  # Ruleau (judge)
    ("1500077901", ["300014198", "1500171612", "300014305"]),  # Lémery, Perdrix
    ("300016889", ["300016892", "300016894"]),  # Lémery, Truite
    ("300014116", ["300014118", "300014119"]),  # Lémery, Pêches
    ("1500077948", ["1500077951"]),  # Lémery, Perche
    ("1500077942", ["900105192", "300019514"]),  # Lémery, Brochet
    ("1500091719", ["300009171"]),  # Lémery, Eau
    ("300017939", ["300010147"]),  # Lémery, Amandes
    ("300008907", ["300008893", "300008912"]),  # Lémery, introduction, digestion
    ("1500077959", ["300011018", "300039862"]),  # Lémery, Anguille
    ("900250825", ["900254972"]),  # abbé Malotru anecdote
    ("900099906", ["1200092726"]),  # Canute anecdote
    ("600030824", ["600030825"]),  # Gregory and Maurice"s law
    ("11200322501", ["11200322500", "11200322498"]),  # portrait of ill-taught princes
    ("600031473", ["1500210076", "1500210077", "600026539", "600032391"]),  # arrêt du Conseil 24 May 1766 (one page)
    ("900144402", ["900194404", "900144399", "1500196973", "900195317"]),  # Boissier de Sauvages, origine du miel
    ("900191210", ["1500072860", "900191124", "900288485"]),  # Cornaro Avertissement
    ("1500152215", ["1500152216"]),  # Callières, one chapter
    ("1500207840", ["1500207839", "600037662", "11200317332", "900300948"]),  # EL VI.5 (two pages)
    ("1500207818", ["1200132571"]),  # Bielfeld definitions
    ("1500081382", ["1500081383"]),  # Malebranche anecdote
    ("1500207844", ["1500207845"]),  # Beccaria ch. 4 paragraph
    ("1200055353", ["1200055355"]),  # Malebranche III.i.1 paragraph
    ("300033773", ["300033772", "300033774"]),  # Malebranche II.ii.3 list
    ("300037984", ["300037985"]),  # Malebranche closing paragraph on sorcerers
    ("900051457", ["11200326306"]),  # Mercure 1735 piece
    ("900220030", ["900220031"]),  # Lemaire, Bussang
    ("1500212183", ["1500212184"]),  # Bodin paragraph
    ("1500168947", ["900195027"]),  # Télémaque V paragraph
    ("1500168918", ["1500168919"]),  # Deut. 17 propositions
    ("1500136558", ["1500136559"]),  # Le Cat, Mariotte
    ("1500080696", ["1500080697"]),  # Wicquefort run-on?
    ("300031809", ["300031810"]),  # Geoffroy noix de galle run-on?
    ("1500134653", ["10300138993"]),  # Geoffroy bardane paragraph
    ("300034802", ["900108193"]),  # Bordeu pouls inférieur
    ("1500243873", ["1500243874"]),  # Besson glaciers run-on?
    ("1200058988", ["900176651"]),  # Barre faida paragraph
    ("900193632", ["900193633", "900193634"]),  # Fouquet paragraph?
]
FOLD_T13 = [  # (keeper, [others]) from the t13 first readers' notes (1 Nov); short units
    ("1500110223", ["1500110224"]),  # La Sarraz, minister and languages
    ("300014338", ["300014339"]),  # Van Helmont anecdote
    ("1200129628", ["1200129629"]),  # Mme Legros article
    ("900158239", ["900158246", "900158277", "900158287", "900158325"]),  # letter praising Bordeu
    ("900207276", ["900207275"]),  # Bordeu, Recherches III
    ("900145427", ["900145429", "900145436", "900145438"]),  # Harvey account
    ("1500124101", ["1200090019"]),  # Fourcroy anecdote
    ("1500155929", ["1500155930", "1500155931"]),  # La Porte, opening praise
    ("1500155948", ["1500155949"]),  # La Porte, XXIV.5 objection
    ("11200315836", ["1500155952"]),  # La Porte, XXIV.26 objection
    ("1500155968", ["1500155969"]),  # La Porte, XVI.2 remark
    ("1500155976", ["1500155978"]),  # La Porte, XIV.12 remark
    ("1500155988", ["1500155989"]),  # La Porte, text plus note
    ("1500214476", ["900063612"]),  # Bertier conclusions?
    ("300034612", ["11200326808"]),  # EL XXIII.11 (short chapter)
    ("1200081090", ["1200142108"]),  # EL XXIII.17
    ("1500159428", ["600055682"]),  # EL XXIII.29
    ("1500159436", ["1200093432"]),  # EL XXIV.6
    ("900238207", ["900238208"]),  # Conti"s declaration
    ("1500256989", ["1500256991"]),  # Mesmer"s 27 Propositions
    ("1500256987", ["1500256990"]),  # Mesmer"s magnet cure
    ("900216839", ["900216840"]),  # Tissot review sentences
    ("900293251", ["900293252"]),  # Vairasse paragraph
    ("1500138258", ["1500138259", "1500138260", "1500138261", "1500138262"]),  # Chalettes, Lettre 1745 (short?)
    ("900314113", ["900287794"]),  # Louis, cornée run-on
    ("900262203", ["1500173368"]),  # Tolomas, hyène
    ("900200162", ["900200163"]),  # Louis, Éloge de Petit
    ("1200121938", ["1500156152"]),  # EL III.5
    ("1500156167", ["1500156168", "1500156169", "1500156170"]),  # La Porte on Gresset"s Sidnei
    ("900094041", ["900094042"]),  # JdS 1753 review run-on
    ("900094004", ["11200324322", "900094296"]),  # JdS 1753 review, three examples
    ("900094289", ["1500149167"]),  # Frère Côme on the urine
    ("1500091920", ["1500091921"]),  # cancer description
    ("900181136", ["900181137", "900181138"]),  # Deleurye extract
    ("900293502", ["900293503"]),  # Burton paragraph
    ("900209607", ["900209606"]),  # translator"s avertissement to White
    ("900205991", ["900205992"]),  # White paragraph
    ("900205993", ["900205994", "900205995", "900205996"]),  # White"s advice run
    ("1500131088", ["1500131114"]),  # Ligue letter 1593
    ("1500232630", ["1500232631", "1500232633"]),  # plant-analysis entry
    ("900182537", ["900182538", "900182539", "900182540"]),  # Grace"s recipe
    ("1500010138", ["900314196"]),  # François de Sales on a visionary nun
    ("900250195", ["900250196", "900250197", "900250198"]),  # Brumoy, grieving father episode
    ("1500130851", ["1500130852"]),  # Brumoy, l"Espérance
    ("1500130857", ["1500130858"]),  # Brumoy, Fear
    ("900128893", ["900128889", "900128891"]),  # Argens, transmigration letter
    ("900083812", ["900056803"]),  # Saint-Evremoniana remark
    ("1500250113", ["900259357"]),  # Füssli letter
    ("1500127989", ["300006075", "300015334"]),  # Boileau Épître III?
    ("300010961", ["300005879", "300009853", "300007718", "300011506", "300005532", "300009997", "300009510", "300009816", "300010900"]),  # sixain ode on Hell
    ("300011276", ["300010059", "300007724"]),  # religious ode
    ("900078805", ["900078807"]),  # Ps 103 paraphrase
    ("900210737", ["900210738"]),  # sacred ode
    ("900232298", ["900111765"]),  # sacred ode
    ("1200140568", ["1500127936"]),  # prayer poem
    ("900276794", ["900276790", "900276791", "900276792", "300011298", "900276795", "10900151118"]),  # Villiers, on Solitude
    ("1500118050", ["1500118051"]),  # letter on Fourmont
    ("1500046466", ["1500046467", "1500046469", "1500046473"]),  # chapter on the sick (Règle de S. Augustin)
    ("900164386", ["900164387"]),  # theatre description
    ("300009388", ["300002463"]),  # Ancillon on Bodin
    ("1500054808", ["1500123885", "900210678"]),  # Dijon case report
    ("900248570", ["900248571"]),  # preacher portrait
    ("1500119830", ["1500119831"]),  # Poncet anecdote
    ("900112571", ["900112573", "900112574", "900109027"]),  # Siri, portrait of Urban VIII
    ("1500159991", ["1500159990", "1500185909"]),  # Fra-Paolo, Inquisition of State
    ("900087240", ["900087241"]),  # Saint-Foix letter
    ("900115970", ["900115971"]),  # Mithridates portrait
    ("900118778", ["900118779"]),  # Timotheus portrait
    ("900175454", ["900175439", "900175440", "900175441", "900175449", "900175450"]),  # Levret, résumé on pessaries
]
FOLD_T14 = [  # (keeper, [others]) from the t14 first readers' notes (2 Nov); short units
    ("900216836", ["1500207142"]),  # Carrère art. ARABES
    ("900280442", ["900280443"]),  # Éloge de Prost de Royer
    ("900019336", ["900019337"]),  # Chambon, salt mines
    ("300018656", ["300018657", "300018659"]),  # ART NOTOIRE
    ("900172073", ["900169513"]),  # inoculation argument
    ("11200321207", ["1200113936"]),  # Portal"s protocol
    ("300034021", ["300034022", "300034023", "300036131", "300033819", "300033820", "300034025", "300034027", "300034028", "300034029", "300034031", "300034032", "300034034"]),  # Piquet laws (one code?)
    ("300027446", ["300027448", "300027449", "300027451", "300034927", "300036507"]),  # quadrille/hombre laws (one code?)
    ("900150642", ["900150643"]),  # Gueullette, Muslim paradise
    ("1500201677", ["900284251"]),  # Gueullette footnote on Guzarate
    ("10900051860", ["10900027162"]),  # de Piles, blind sculptor
    ("900271375", ["900271376", "900271377"]),  # George Dandin divertissement
    ("1500044844", ["1500044845", "1500044846", "1500055902"]),  # Félibien decoration
    ("900301186", ["900301187"]),  # translator"s note, divine ells
    ("300048431", ["300048432"]),  # Engel, inaction
    ("900301167", ["900302495", "900301168", "300048405", "300048406"]),  # essay on Venus (Recueil 1787)
    ("900249585", ["900249586", "900249587"]),  # Carmontelle mock tragedy
    ("1200063187", ["300014787"]),  # Cologne paragraph
    ("300020075", ["300021539"]),  # Circles paragraph
    ("300039914", ["300039915"]),  # Turkish commerce
    ("1500094135", ["1500094136"]),  # Massialot, chou farci
    ("1200138050", ["1200138051"]),  # Bal des Ardents
    ("1200054126", ["600020075", "600058772"]),  # EL Préface
    ("1200093766", ["900326810"]),  # Bossuet, Politique II.1.12
    ("1500274397", ["1500257381"]),  # Martinique letter?
    ("300024044", ["1500159257"]),  # EL I.3
    ("1200082031", ["600060003"]),  # EL XIII.7
    ("900225977", ["300024317"]),  # EL XV.1
    ("1500158133", ["900098841", "900128699"]),  # LP 46
    ("11200327367", ["600056995", "600034645"]),  # LP 116
    ("1500158148", ["1500158150"]),  # LP 76 (two keepers)
    ("11200321788", ["900025971", "900090780"]),  # poem on marriage
    ("1200145936", ["1200145938"]),  # Voltaire, Samson scene
    ("300035342", ["300035343"]),  # puits forés article
    ("10900310185", ["10900310186"]),  # bombardier beetle
    ("300006199", ["300006198"]),  # Du Tertre, banana
    ("300035739", ["900140916", "900143062"]),  # Alléon-Dulac, lemming
    ("900143064", ["900143065", "900143066"]),  # Lettre sur le limaçon
    ("300018271", ["300018272"]),  # Regnault, microscopic animals
    ("300040363", ["300040365", "300040362"]),  # Japanese varnish article
    ("1500166118", ["900127754"]),  # Akbar"s feast
    ("1200089398", ["1200089249"]),  # Dacier, doctrine of goods
    ("1200089262", ["1200089263"]),  # Dacier, Laws XI
    ("900258543", ["900258544", "900258545"]),  # Hilliard, Franklin portrait
    ("1200114902", ["1200114904"]),  # Hilliard notes, servants
    ("1200114918", ["900266885"]),  # Hilliard notes, jury
    ("1500250861", ["1500250862", "1500250863"]),  # Endymion plate note
    ("1500267248", ["1500267249"]),  # Beaumarchais apostrophe
    ("900125384", ["900125383"]),  # bell-founding letter
    ("900250821", ["900250822"]),  # La Bourdonnais
]
FOLD_T15 = [  # (keeper, [others]) from the t15 first readers' fold candidates (2 Nov): short, uncertain and weak cases
    ('1500246955', ['1500246956', '1500246957']),  # La Borde, Tableaux de la Suisse -> Lettres sur la Suisse: th
    ('900110569', ['900110570', '900110571', '900110572']),  # Norden's letter from Egypt quoted in the preface of the Voya
    ('1200106139', ['1200106140', '1200106141']),  # one translator's note of the 1778 Sénèque (La Grange) quotin
    ('300026108', ['300026109', '300026110', '300026111']),  # Guer on Turkish funerals as carried by the Encyclopédie and 
    ('600048938', ['600048939']),  # two passages of one anti-royalist address of 1791 ("Il ne no
    ('900177702', ['1500209858']),  # Chappe: the Lapouchin sentence (beheading, the sister's knou
    ('900178917', ['900178914']),  # one short method for poisoning wolves (dog killed with nux v
    ('900170437', ['900170439', '900170441']),  # Morand's observation of the bullet in the skull (temporal bo
    ('900292453', ['900292451', '900292454']),  # Morand's anecdote of the diseased oxen at the Invalides (Gaz
    ('900130127', ['900130129']),  # torpedo, Réaumur via Savérien ("reprend sa convexité... coup
    ('900264438', ['1500211122']),  # Morand on frère Jacques: the attestation and his presentatio
    ('300053680', ['300053681']),  # de Piles, rectus abdominis: origin/insertion and the interse
    ('300053694', ['300053695']),  # de Piles, the fessiers: grand fessier insertion and the fess
    ('300053677', ['300053672', '300053676']),  # de Piles, arm: biceps and the muscles marked when the hand i
    ('900103232', ['900103235']),  # Bérard/Blanchet, the preface of L'Art du chant
    ('300047541', ['10300105145', '300047542']),  # Condillac's note praising the abbé de l'Épée (Grammaire, Cou
    ('11200135005', ['11200135006', '11200279531']),  # Rollin after Xenophon, Cyrus and the king of Armenia / Tigra
    ('11200135509', ['11200135511']),  # Plato/Dacier, Crito, speech of the Laws (about three pages)
    ('11200135995', ['11200135996']),  # Rollin, Alexander, the Cydnus and the physician Philippe (ba
    ('11200137152', ['11200137153']),  # Diogenes sold in Crete to Xeniades, then refusing ransom ("l
    ('300032758', ['300032760', '300032759']),  # Rollin's short passage on the Panegyrici veteres ("Nous avon
    ('10300013624', ['10300013625', '10300013626', '10300013627']),  # four pieces of ONE Dacier note on the shipwreck votive table
    ('11200049176', ['11200049177']),  # Marcus Aurelius, Meditations I.17 (thanks to the gods), both
    ('10900207884', ['11200325765']),  # DP "Julien" ("rend quelquefois justice bien tard" / "après a
    ('11200113925', ['11200113926']),  # Pythagoras in Hades / returning "des enfers" (Fénelon Abrégé
    ('11200323692', ['10300004865', '10300004866']),  # Genesis 18:1-15, the visit at Mambré
    ('10300004862', ['10300110184']),  # Genesis 17, the covenant of circumcision
    ('10300004870', ['11200323688']),  # Genesis 20:9 and 20:11-12, Abraham and Abimelech
    ('11200113480', ['11200016208', '10300143326']),  # Genesis 44:27-45:9, Judah's plea and Joseph's self-revelatio
    ('11200016679', ['11200016678']),  # 2 Sam 13:1-22, Amnon and Tamar, one short pericope that Géna
    ('11200017228', ['11200017221', '11200017222', '11200017240', '11200017243', '11200017245', '11200017252', '11200017253', '11200017257']),  # Song of Songs (about 117 verses), Voltaire's Précis du Canti
    ('11200017176', ['11200017178']),  # Prov 31:10-31, the acrostic poem of the femme forte (31:13-1
    ('11200017558', ['11200136672']),  # Ez 27, the lament over Tyre (27:4-7; 27:15-19), Goguet in bo
    ('11200017616', ['11200017617']),  # Dn 4, Nebuchadnezzar's madness (4:22-29; 4:30-31), Rollin in
    ('11200017620', ['11200017624']),  # Dn 5, Belshazzar's feast (5:2-3; 5:23-27)
    ('11200017761', ['300014967', '11200017763']),  # Mt 5:21-26, the first antithesis (5:21-22; 5:22 Raca; 5:25-2
    ('11200017768', ['11200017771']),  # Mt 6:1-18, almsgiving, prayer, fasting (6:1-5; 6:16-17); the
    ('10300005376', ['11200017840']),  # Mt 13:10-17, why parables (13:10-11; 13:13)
    ('11200017863', ['300049430']),  # the Transfiguration (Mt 17:1-4)
    ('11200017842', ['11200017846']),  # the parable of the tares (Mt 13:24-25) and its explanation (
    ('11200017898', ['11200266613']),  # the Sadducees on the resurrection, Mt 22:30-32 and Lc 20:34-
    ('11200017889', ['11200018223']),  # entry into Jerusalem, Mt 21:5-10 and Lc 19:37-44 (which also
    ('11200018236', ['11200018054']),  # the Last Supper, Lc 22:15 and Mt 26:26: synoptic parallels
    ('11200018197', ['10300015111']),  # "Last shall be first", Lc 13:30, the close of the narrow-doo
    ('10300005540', ['11200311906', '11200311791', '11200311697']),  # Nicodemus, Jn 3:1-21
    ('11200311726', ['11200046188', '11200311719']),  # the Samaritan woman, Jn 4
    ('11200311863', ['11200311866', '11200311775', '11200311943', '11200121042', '11200311776']),  # Jn 17, the priestly prayer, one prayer of about a page; 1120
    ('11200311831', ['11200311789', '11200311833', '11200311834']),  # Jn 13:1-17, the washing of the feet (13:1; 13:4-5; 13:8-9; 1
    ('11200311751', ['11200221514']),  # Jn 13:31-35 (rows 2119883/2120186 run on to 13:34 "je vous d
    ('11200311717', ['11200311891']),  # Jn 20:24-29, Thomas (row 2119708 ends at 20:25; 20:26-27)
    ('10300025038', ['11200018395']),  # Ac 23:1-10, Paul before the Sanhedrin (23:3; 23:6-7)
    ('11200018638', ['11200018640']),  # Ep 6:5-9, servants and masters, one paragraph; Bellon de Sai
    ('11200018834', ['11200018836']),  # Apoc 3:7-8 and 3:12-13, the letter to Philadelphia (Gibert 1
    ('11200018893', ['10300005897', '11200018897', '10300005956']),  # the Decalogue, Ex 20:2-17 / Deut 5:6-21, quoted by Beauzée a
    ('11200196261', ['11200018967', '11200018964']),  # Deut 15:1-11, the year of remission, in Mignot's Traité des 
    ('10300005870', ['10300005871']),  # Gen 3:16 and 3:17-19, the curses of the Fall (the Encyclopéd
    ('11200019327', ['10300006041']),  # Isa 11:1-2 and 11:10 (Supplément 1776 and Beauzée 1747 in bo
    ('11200019355', ['11200019358']),  # Isa 45:1-4 and 45:13, the Cyrus oracle (Beauzée and Mme Daci
    ('11200019534', ['11200019535']),  # Mt 11:25 and 11:27 (Carron / Pascal; different quoters)
    ('11200018814', ['11200018817']),  # 1 Jn 3:5-9 and 3:18-22 (different quoters)
    ('11200019776', ['11200019777']),  # 1 Cor 13:1-5 and 13:7, the charity pericope (Beauzée 1747 an
    ('11200054885', ['11200054886']),  # Plutarch, Solon and Croesus (Tellus, then Cleobis and Biton)
    ('11200054849', ['11200135078']),  # Solon's debt edict and its reception / the edict named "déch
    ('11200054702', ['11200054704', '11200054705']),  # Plutarch, Timoléon in old age at Syracuse (visits, the chari
    ('11200054424', ['11200054423']),  # Démétrius captive takes to drink and dice / dies of inaction
    ('11200055167', ['11200136249']),  # Pyrrhus's storm at sea and Pyrrhus throws himself into the s
    ('11200055172', ['11200290609', '11200326149']),  # Fabricius's letter and its sequel (Pyrrhus returns the priso
    ('11200079035', ['11200079036']),  # two quotations Mme Dacier takes from the same dialogue (adja
    ('11200262137', ['10300114488']),  # Anne Dacier's Préface du Plutus (1684) on Aristophanes
    ('11200206704', ['11200206706']),  # Rousseau, Contrat social II.1
    ('11200206815', ['11200206816']),  # Contrat social III.9
    ('11200206822', ['11200206826']),  # Contrat social III.11
    ('11200206838', ['11200206839', '11200206840', '11200206841']),  # Contrat social III.15 (about three pages); 206840 ends "si l
    ('11200044748', ['10300014647']),  # Fontenelle, Lettres galantes, ONE short letter on a secret m
    ('11200057982', ['11200057983']),  # Fontenelle, éloge de Malebranche, consecutive sentences on h
    ('11200231890', ['11200231892', '11200231619']),  # Holbach, Système de la nature: the Iliad from letters thrown
    ('10300091603', ['10300091604']),  # the 1768 Lucrèce translator's note: "les Grecs ont été désab
    ('10900315192', ['11200263031']),  # the duc de Praslin's letter to Vergennes (17 Dec 1779) on Be
    ('11200319370', ['11200267780']),  # two adjacent passages of Mesmer's Précis 1781 (the propositi
    ('11200145193', ['11200145195']),  # Duguet, Institution d'un prince: the minister who forbids re
    ('300009507', ['300006583', '300010231']),  # probably one short poem on love in the underworld ("bords de
    ('11200315023', ['11200315024']),  # Louis XVI's farewell to his family and his last morning, bot
    ('11200288824', ['11200288825', '11200288826']),  # Volney, Considérations sur la guerre des Turcs (a pamphlet o
    ('11200258131', ['11200258132', '11200258133']),  # d'Éon's Très-humble réponse ... à Caron de Beaumarchais (177
    ('11200134085', ['11200134086', '11200134096']),  # one arrêt on the administration of the Compagnie des Indes (
    ('11200144470', ['11200133999', '11200134000']),  # one royal declaration on the visa / liquidation of papers (e
    ('10300044791', ['10300044835']),  # Feuquières on defensive war and on contributions; the Encycl
    ('11200279325', ['11200252354', '11200252356']),  # Coquereau's Terray epigrams: 252354 carries the end of one e
    ('11200299721', ['10300137167']),  # Louis XVI's letter of 13 Sept 1791 accepting the Constitutio
    ('11200242058', ['11200242061', '11200242063', '11200242064', '11200242065', '11200242067', '11200242069', '11200242101']),  # the explanation of the constitutional medal/print in Les eff
    ('11200325927', ['11200325926', '11200325928']),  # probably one letter to Saint-Germain (the Maréchal de Brogli
    ('11200162889', ['11200162890', '11200162891']),  # Catiline's speech to the conspirators (one speech/tirade; Sa
    ('11200261801', ['10300124233', '10300124234']),  # Euripides, Électre (1750 translation), the exchange of Orest
    ('11200167049', ['11200261802']),  # Euripides, Électre, the exchange after the murder ("ô Terre,
]

FOLD_T16 = [  # (keeper, [others]) from the t16 first readers' fold candidates (3 Nov): short, uncertain and weak cases
    ('10900025776', ['900228068', '10900025781', '10900025783']),  # verse Héloïse to Abailard ("Interprète éloquente, une lettre
    ('11200326157', ['11200326156']),  # de Piles, Idée du peintre parfait (painting and history / pa
    ('11200248765', ['11200248767']),  # Aelian, Var. Hist. II.13 (Anytus' plot through the Nuées / t
    ('11200174904', ['10300114368']),  # Batteux on the origin of lyric poetry (first cry of man / "V
    ('11200262114', ['11200262115', '11200262116']),  # Euripides, Alceste (Brumoy), final scene of Heracles and Adm
    ('11200262249', ['11200262250']),  # Aristophanes, La Paix: Trygaeus meets Hermes, then Hermes sh
    ('11200259720', ['11200259721']),  # Sophocles, Oedipus at Colonus, Oedipus' last speech: 259720 
    ('300019880', ['300019877', '10300008567', '300019879']),  # Descartes, Méditations, the Abrégé (synopsis of the six medi
    ('10300128085', ['10300128087']),  # Falconet on Van der Helst (Amsterdam town hall), apparently 
    ('11200047860', ['11200047861', '11200047862', '11200047863']),  # La Bruyère, De la mode, the Onuphre portrait (haire et disci
    ('10300008622', ['10300008623']),  # two Scarron passages quoted in Trévoux (T.5 and T.1), perhap
    ('300000679', ['300000672', '300000683']),  # Bodin's Latin letter (to Pibrac?) quoted by Bayle, article B
    ('11200179580', ['11200179584']),  # Buffon's first man awakening (HN III 1749), a récit of two o
    ('10300036826', ['10300036827']),  # Lambert, Réflexions nouvelles sur les femmes: the pudeur par
    ('300009200', ['10300111552']),  # La Fontaine I.7 La Besace ("frère l'Ours..." / "Dame Fourmi 
    ('11200036045', ['11200284916']),  # La Fontaine I.8 L'Hirondelle et les petits Oiseaux
    ('11200036056', ['10300062176', '10000000756']),  # La Fontaine I.18 Le Renard et la Cigogne ("Honteux comme un 
    ('11200314703', ['10300111549', '11200314723']),  # La Fontaine III.18 Le Chat et un vieux Rat ("maître Mitis...
    ('10300010748', ['10300010749', '10300010753', '10300010756']),  # La Fontaine, Préface des Fables (1668, a few pages)
    ('11200027009', ['11200027010']),  # Tristan, La Mariane V: Hérode's lament ("Mariamne a des mort
    ('10300008946', ['300002423']),  # Gui Patin on Mayerne Turquet (the Apologie; "grand chymiste.
    ('10300008844', ['10300008863']),  # two Voiture letters quoted by Robinet's Supplément and the J
    ('10300095606', ['11200036763', '10300011306']),  # Pascal, Pensées VIII (about a page): "Je regarde de toutes p
    ('11200040110', ['11200040111']),  # Sévigné to Mme de Grignan, 9 Feb 1671 ("je fonds en larmes e
    ('11200326137', ['11200040187', '11200040187', '11200326139', '11200326138']),  # one Sévigné letter of 1671 as printed by Lévizac/Condillac (
    ('11200040110', ['11200040117']),  # Sévigné 1671, "il faut bien que je pleure en lisant vos lett
    ('300012108', ['10300143897', '10300143898']),  # Boileau, Épître III? ("des jugements d'autrui nous tremblons
    ('11200053178', ['10300136861', '300021567', '10300142628']),  # Deshoulières: "sans songer qu'eux et nous passerons comme un
    ('10300016493', ['10300016494']),  # Descartes to Mersenne, 15 April 1630, via Baillet (eternal t
    ('10300025081', ['10300025082']),  # Fénelon, Dialogues des morts, one dialogue on philanthropy (
    ('10300051518', ['10300051519']),  # Vertot, the two daughters of Fabius Ambustus (the lictor's k
    ('11200108120', ['300041228', '300041242']),  # J.-B. Rousseau, retreat-from-the-court stanzas ("Tout invite
    ('11200147042', ['11200292776']),  # Varenne, Mémoires de Ravanne, ONE anecdote (the ladies' pist
    ('11200024996', ['900068325']),  # Balzac, letter to La Motte Aigron describing his house on th
]

FOLD_T17 = [  # (keeper, [others]) from the t17 first readers' fold candidates (4 Nov): only cases with a run-on, near run-on or overlap (t16 ruling 1)
    ('10300055386', ['10300055387']),  # EL III.3, Athens / Chaeronea: the Encyclopédie row breaks off at "Quand P[hilippe]"
    ('10300055557', ['11200163739', '10300055559']),  # EL XII.13 "Des écrits": row 1146018 runs on from Cremutius Cordus
    ('10300055624', ['10300055625', '11200163840']),  # EL XV.10, row 1094676 ends "Telle", the opening of 10300055625
    ('10300055808', ['10300055810']),  # EL XXVIII.22, galanterie / "Les paladins..." near run-on
    ('11200164330', ['10300055859']),  # EL XXX.20 fredum: the Encyclopédie T of 1094903 runs on
    ('10300008364', ['11200027347']),  # Sully, the Alibour anecdote, a gap of a few words
    ('10300116389', ['10300116390']),  # Pluche on coinage, possible run-on
    ('10300091733', ['10300091734', '300045658']),  # building and firing a charbonnière, 733 ends / 734 begins
    ('11200223999', ['11200224000']),  # Palomba on jours de faveur, the example continues
    ('10300110911', ['10300110912']),  # Raynal, the European and the Chinese merchant (Encyclopediana)
]
FOLD_T18 = [
    ("900092110", ['900092111']),  # Juan & Ulloa, Lima's church silver, then the gold vessels; 900092110 e
    ("10900399574", ['11200299209', '11200296493']),  # Déclaration des droits 1789, preamble and arts. I–XVII; overlap only w
    ("11200298964", ['10300136736']),  # Constitution 1791, Titre I: start ("La Constitution garantit...") / li
    ("11200160045", ['10300054024']),  # Ordonnance 1669 tit. XXV on triage: row 1093379 of 10300054024 runs in
    ("11200171293", ['11200171295']),  # Duhamel, Élémens de l'architecture navale, quoted by Accarias: 1120017
    ("11200269293", ['11200269294']),  # Crèvecoeur, Lettres d'un cultivateur, the Quaker preacher Thomas: 293 
    ("11200217248", ['11200217249']),  # Chastellux, Voyages, the settler's clearing: [A] of 248 stops at "Tout
    ("11200286588", ['11200286589']),  # Clavière against tobacco culture: 588 stops at "Occupant déjà un sol",
    ("11200270825", ['11200270826']),  # Varenne de Fenille, forest memoir: "dans les différentes classes" / "e
    ("10300058217", ['300022652']),  # Burlamaqui / Encyclopédie on subjects' duties: 10300058217 ends on "Le
    ("10000003908", ['10000003907']),  # Voltaire's Reims inscription: the letter to Pigalle and the letter to 
    ("11200203586", ['10300075042', '11200203588']),  # acclamations at Commodus's death (Diderot's introduction, the Lampridi
    ("10000004851", ['10000004687']),  # Voltaire, Charlot: row 1046822 (letter to Damilaville) carries the ver
    ("11200136800", ['11200112184']),  # Pliny XXXV in Durand's French, Zeuxis and Parrhasius (grapes / curtain
    ("300050598", ['300050599']),  # Apelles and Protogenes, the contest of lines: row 76415 stops at "en d
    ("11200116215", ['11200116216']),  # marked quotation on tolls (balises / the Pont-Euxin), both to Dupin an
    ("11200197331", ['10300046373']),  # Diodorus I, 10 (Terrasson): same two witnesses (De Brosses, Naigeon), 
    ("11200103747", ['10300033651']),  # Pliny V, 6, end: "le corps plus sain" seems to follow directly on "un 
    ("11200175899", ['11200175900']),  # Rousseau, Lettre sur la musique, one sentence on the Serva padrona due
    ("11200279815", ['11200279816']),  # Pliny NH VII, apostrophe to Cicero / Cicero's powers (Guéroult), in La
]
FOLD = [] if "--nofold" in _s.argv else (FOLD_T18 if "--t18" in _s.argv else FOLD_T17 if "--t17" in _s.argv else FOLD_T16 if "--t16" in _s.argv else FOLD_T15 if "--t15" in _s.argv else FOLD_T14 if "--t14" in _s.argv else FOLD_T13 if "--t13" in _s.argv else FOLD_T12 if "--t12" in _s.argv else FOLD_T11 if "--t11" in _s.argv else FOLD_T10 if "--t10" in _s.argv else FOLD_T09 if "--t09" in _s.argv else FOLD_T08 if "--t08" in _s.argv else FOLD_T07 if "--t07" in _s.argv else FOLD_T06 if "--t06" in _s.argv else FOLD_T05 if "--t05" in _s.argv else FOLD_T04 if "--t04" in _s.argv else FOLD_T03 if "--t03" in _s.argv else FOLD_T02 if "--t02" in _s.argv else FOLD_T01)
SHORT = re.compile(r"short|fragment|brief|quotable|too generic|tiny|stock|ordinary|generic|plain", re.I)
block = {}; rows = defaultdict(list); order = []
for f in sorted(glob.glob(os.path.join(D, "p_*.txt"))):
    g = None; buf = []
    for l in open(f, encoding="utf-8"):
        m = re.match(r"--- GROUP (\d+)", l)
        if m:
            if g: block[g] = "".join(buf).rstrip() + "\n"
            g = m.group(1); buf = [l]; order.append(g); continue
        if g:
            buf.append(l)
            m = re.match(r"\s+(?:FRONT )?row (\d+) \|", l)
            if m: rows[g].append(m.group(1))
    if g: block[g] = "".join(buf).rstrip() + "\n"
V = {}
for f in sorted(glob.glob(os.path.join(D, "v_*.tsv"))):
    for r in csv.reader(open(f, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
        if not r or r[0] == "group": continue
        r += [""] * 6; V[r[0].strip()] = [x.strip() for x in r[:6]]
# MOVE cases, by keeper
cases = defaultdict(list)
for g, (_, v, d, rr, src, note) in V.items():
    if v == "MOVE": cases[d].append((g, None, note))
    elif v == "PART":
        for t in rr.split():
            rid, w = t.split(":", 1)
            if w.isdigit(): cases[w].append((g, rid, note))
def chunks(items, size):
    out = []; cur = []; n = 0
    for it in items:
        if cur and n >= size: out.append(cur); cur = []; n = 0
        cur.append(it); n += it[1]
    if cur: out.append(cur)
    return out
mc = []
for k in sorted(cases, key=lambda x: order.index(x) if x in order else 10**9):
    txt = [f"\n==================== CASE keeper {k} ====================\n"]
    kv = V.get(k, ["", "?", "", "", "", ""])
    txt.append(f"KEEPER verdict {kv[1]}: {kv[5]}\n" + block.get(k, f"(group {k} not in this tranche)\n"))
    seen = set()
    for g, rid, note in cases[k]:
        if rid is None: txt.append(f"\n>>> PROPOSED: WHOLE group {g} moves into {k}. Reader's note: {note}\n")
        else: txt.append(f"\n>>> PROPOSED: only row {rid} of group {g} moves into {k} (PART). Reader's note: {note}\n")
        if g not in seen: txt.append(block[g]); seen.add(g)
    s = "".join(txt); mc.append((s, s.count("\n")))
sn = []
for g in order:
    if g not in V: continue
    _, v, d, rr, src, note = V[g]
    if v == "NOISE" and SHORT.search(note):
        s = f"\n==================== CHECK group {g} (WHOLE group NOISE) ====================\nReader's note: {note}\n" + block[g]
        sn.append((s, s.count("\n")))
    elif v == "PART" and SHORT.search(note):
        nr = [t.split(":")[0] for t in rr.split() if t.endswith(":NOISE")]
        if nr:
            s = (f"\n==================== CHECK group {g} (PART: rows {' '.join(nr)} NOISE) ====================\n"
                 f"Reader's note: {note}\nRows: {rr}\n" + block[g])
            sn.append((s, s.count("\n")))
n = {"mc": 0, "sn": 0}
for name, items, size in (("mc", mc, 1300), ("sn", sn, 1300)):
    for i, ch in enumerate(chunks(items, size)):
        with open(os.path.join(D, f"{name}_{i}.txt"), "w", encoding="utf-8") as fh:
            fh.write(f"{name.upper()} CHECK {i}: {len(ch)} cases\n" + "".join(c[0] for c in ch)); n[name] += 1
with open(os.path.join(D, "fc.txt"), "w", encoding="utf-8") as fh:
    fh.write(f"FOLD CHECK: {len(FOLD)} cases\n")
    for k, others in FOLD:
        fh.write(f"\n==================== CASE keeper {k} ====================\nKEEPER note: {V.get(k,['']*6)[5]}\n" + block.get(k, "(missing)\n"))
        for g in others:
            if g not in V or g not in block: print("  fold candidate not in batch, skipped:", g); continue
            fh.write(f"\n>>> CANDIDATE: group {g} may be the SAME unit as {k}. First reader: {V[g][1]} {V[g][2]} {V[g][3]} -- {V[g][5]}\n" + block[g])
print(f"MOVE cases {len(mc)} ({sum(len(v) for v in cases.values())} proposals) in {n['mc']} files; "
      f"short-NOISE checks {len(sn)} in {n['sn']} files; fold cases {len(FOLD)}")
