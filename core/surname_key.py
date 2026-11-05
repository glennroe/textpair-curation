#!/usr/bin/env python3
"""
surname_key.py
ONE definition of the surname key that `attributed_surname` stores and that
the representative tie-break (representative.py) matches as an unanchored,
case-insensitive substring of `source_author`. Import it; do not re-derive it.

WHY THIS EXISTS — 23 Sep 2026
-----------------------------
On 24 Aug `one-concept-seven-surname-parsers` counted seven copies of
surname() and predicted the regnal fault. By 23 Sep there were SIXTEEN, three
families of behaviour, and the fault had fired twice:

  22 Sep  the BARE parser in record_attribution.py stored 'I', 'IV', 'XVI'
          for François I, Henri IV, Louis XVI. Repaired by hand: the rulers
          NULL, Justinien Ier's 214 rows 'Justinien'.
  23 Sep  add_attributed_surname.py --commit, run as the "normalisation pass
          after every attribution write", RE-DERIVED EVERY ROW with the
          STRICT parser and reverted that repair: 'Ier' x214 (a substring of
          Cartier, Olivier, premier), 'Henri' x3, 'François', 'Louis'.

The bare parser returns a numeral; the strict parser drops the numeral and
returns a FORENAME. Both are wrong for a ruler, in opposite directions, and a
normalisation pass that cannot see a hand repair will undo every one of them.

THE KEY — what surname() returns
--------------------------------
  author_NNNNN                  the whole id (a legitimate authority key)
  'Nom, Prénom (dates)'         'Nom'   -- text before the first comma
  'Prénom Nom (dates)'          'Nom'   -- the last token
  'Louis XVI (1754-1793 ; ...)' 'Louis XVI'     REGNAL: name + numeral
  'Justinien Ier (...)'         'Justinien Ier' REGNAL, French ordinal
  'Unknown', 'Anonyme', ...     ''      -- a placeholder is not a name

A REGNAL NAME KEYS ON THE NAME AND ITS NUMERAL TOGETHER. 'Louis XVI' as a
substring matches the rows that name him (and, bounded, 'Louis XVIII'); 'XVI'
matches every sixteenth-anything and 'Louis' matches half the corpus. A
numeral counts as regnal only when it is written in CAPITALS (or is a French
ordinal: Ier, Ire, Iᵉʳ, 1er), so a surname that happens to spell a numeral in
ordinary case ('Dix', 'Mill') is left alone.

'' means NULL: the tie-break declines rather than guesses, which is the same
outcome as having no attribution.

KNOWN CRUDE CASES, unchanged from the strict parser and recorded rather than
fixed: 'Charles de Sainte-Maure, duc de Montausier' -> 'Sainte-Maure' (first
comma); 'France. Assemblée nationale constituante (1789-1791).' ->
'constituante' (a corporate body). Where the automatic key is wrong, PIN it.

PINNED KEYS — the other half of the fix
---------------------------------------
`combined_align_groups_provenance.surname_pinned` (boolean, default false).
A pinned row's `attributed_surname` was set by hand and is AUTHORITATIVE:
every writer that goes through this module leaves it alone.

    pinned_groups(cur, prov)  -> set of group_ids whose key is pinned
    has_pin_column(cur, prov) -> bool

Writers call pinned_groups() once and skip those ids. Where the column does
not exist yet, nothing is pinned and the writers behave as before -- loudly,
via has_pin_column(), so an unpinned run is never mistaken for a pinned one.

Self-test:  python3 surname_key.py
"""

import re

NOT_A_NAME = {
    "unknown", "anonymous", "anonyme", "anon", "inconnu", "inconnue",
    "n/a", "na", "none", "null", "?", "-", "--", "sn", "s.n.",
    "not_known", "not known", "unknown]", "[unknown]",
}

ROMAN = re.compile(
    r"^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")
FRENCH_ORDINAL = re.compile(r"^(1er|1re|ier|ire|iᵉʳ|ie)$", re.IGNORECASE)

PIN_COLUMN = "surname_pinned"


def _is_regnal(tok):
    t = tok.strip(".,;")
    if not t:
        return False
    if FRENCH_ORDINAL.match(t):
        return True
    return t.isupper() and bool(ROMAN.match(t))


EPITHET_ONE = {"l'ancien", "l'ancienne", "l'aîné", "l'aînée", "l'africain",
               "l’ancien", "l’aîné", "l’africain"}
EPITHET_TWO = {"jeune", "père", "fils", "grand", "vieux", "cadet", "rhéteur"}


def _epithet_len(parts):
    """Number of trailing tokens that form an epithet (0, 1 or 2)."""
    if not parts:
        return 0
    t = parts[-1].strip(".,;").lower()
    if t in EPITHET_ONE:
        return 1
    if (len(parts) >= 2 and t in EPITHET_TWO
            and parts[-2].lower() in ("le", "la")):
        return 2
    return 0


def surname(author):
    """The tie-break key for an author string, or '' for none."""
    if not author:
        return ""
    s = str(author).strip()
    if re.match(r"^author_\d+$", s):
        return s
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"\[[^\]]*\]", "", s).strip()
    if "," in s:
        s = s.split(",", 1)[0].strip()
    parts = s.split()
    if not parts:
        return ""
    numerals = []
    while parts and _is_regnal(parts[-1]):
        numerals.insert(0, parts.pop().strip(".,;"))
    if numerals:
        if not parts:
            return ""                      # a numeral alone is not a name
        return " ".join([parts[-1]] + numerals)
    # EPITHETS, 24 Sep 2026. 'Pline l'Ancien' keyed on "l'Ancien" and 'Pline
    # le Jeune' on 'Jeune' -- substrings of Caton l'Ancien, Sénèque le Jeune
    # and any 'jeune' in a title-like author string. Like a regnal numeral,
    # an epithet keys TOGETHER with the name it qualifies.
    ep = _epithet_len(parts)
    if ep and len(parts) > ep:
        return " ".join(parts[-(ep + 1):])
    if ep == 2 and len(parts) == 2:
        return " ".join(parts)             # the family name Le Jeune
    last = parts[-1].strip(",;")
    if last.lower().strip(".") in NOT_A_NAME:
        return ""
    return last


def has_pin_column(cur, prov="combined_align_groups_provenance"):
    cur.execute("""SELECT 1 FROM information_schema.columns
                    WHERE table_name = %s AND column_name = %s""",
                (prov.split(".")[-1], PIN_COLUMN))
    return cur.fetchone() is not None


def pinned_groups(cur, prov="combined_align_groups_provenance"):
    if not has_pin_column(cur, prov):
        return set()
    cur.execute(f"SELECT group_id FROM {prov} WHERE {PIN_COLUMN}")
    return {r[0] for r in cur.fetchall()}


if __name__ == "__main__":
    CASES = [
        ("Rouget de Lisle, Claude Joseph, 1760-1836. Marseillaise.", "Lisle"),
        ("Claude Joseph Rouget de Lisle (1760-1836)", "Lisle"),
        ("Louis XVI (1754-1793 ; roi de France)", "Louis XVI"),
        ("Louis XVI (1754-1793)", "Louis XVI"),
        ("Henri IV (1553-1610)", "Henri IV"),
        ("Henri IV", "Henri IV"),
        ("François I (1494-1547)", "François I"),
        ("Charles IX", "Charles IX"),
        ("Justinien Ier (empereur de Byzance, 0482-0565)", "Justinien Ier"),
        ("Voltaire (1694-1778)", "Voltaire"),
        ("Voltaire [François Marie Arouet]", "Voltaire"),
        ("Diderot, Denis, (1713.0-1784.0)", "Diderot"),
        ("Jean-Jacques Rousseau (1712-1778)", "Rousseau"),
        ("Marie de Rabutin-Chantal marquise de Sévigné (1626-1696)", "Sévigné"),
        ("Horace (0065-0008 av. J.-C.)", "Horace"),
        ("Gilles Ménage (1613-1692)", "Ménage"),
        ("Ménage, Gilles (1613-1692)", "Ménage"),
        ("Pline l'Ancien (0023-0079)", "Pline l'Ancien"),
        ("Pline le Jeune (0061?-0114?)", "Pline le Jeune"),
        ("Sénèque le Père", "Sénèque le Père"),
        ("Caton l'Ancien", "Caton l'Ancien"),
        ("Scipion l'Africain", "Scipion l'Africain"),
        ("Le Jeune", "Le Jeune"),
        ("Pierre Lejeune", "Lejeune"),
        ("Otto Dix", "Dix"),
        ("John Stuart Mill", "Mill"),
        ("author_03337", "author_03337"),
        ("Unknown", ""),
        ("not_known", ""),
        ("IX", ""),
        ("", ""),
        (None, ""),
    ]
    bad = 0
    for a, want in CASES:
        got = surname(a)
        ok = got == want
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {str(a)!r:<62} -> {got!r}"
              + ("" if ok else f"   (wanted {want!r})"))
    print(f"\n  {len(CASES) - bad}/{len(CASES)} passed")
    raise SystemExit(1 if bad else 0)
