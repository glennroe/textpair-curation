#!/usr/bin/env python3
"""cover_P.py p_NNNN.txt v_NNNN.tsv -- checks a Phase P verdict file against its batch."""
import csv, re, sys
csv.field_size_limit(sys.maxsize)
b, v = sys.argv[1], sys.argv[2]
G = {}; cur = None
for l in open(b, encoding="utf-8"):
    m = re.match(r"--- GROUP (\d+)", l)
    if m: cur = m.group(1); G[cur] = []; continue
    m = re.match(r"\s+(?:FRONT )?row (\d+) \|", l)
    if m and cur: G[cur].append(m.group(1))
err = []; seen = {}
V = {"KEEP", "MOVE", "NOISE", "EDITION", "LATIN", "PART"}
for r in csv.reader(open(v, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
    if not r or r[0] == "group": continue
    r += [""] * (6 - len(r)); g, vd, d, rows = r[0].strip(), r[1].strip(), r[2].strip(), r[3].strip()
    if g not in G: err.append(f"line for unknown group {g}"); continue
    if g in seen: err.append(f"group {g} twice"); continue
    seen[g] = vd
    if vd not in V: err.append(f"{g}: bad verdict {vd!r}")
    if vd == "MOVE" and (d not in G or d == g): err.append(f"{g}: MOVE dest {d!r} not a group of the batch")
    if vd == "PART":
        m = {}
        for t in rows.split():
            if ":" not in t: err.append(f"{g}: bad token {t!r}"); continue
            k, w = t.split(":", 1); m[k] = w
            if not (w in ("KEEP", "NOISE", "EDITION", "LATIN") or w.startswith("NEW:") or (w in G and w != g)):
                err.append(f"{g}: bad WHERE {w!r} for row {k}")
        if set(m) != set(G[g]): err.append(f"{g}: PART rows {len(m)} v group rows {len(G[g])}; missing {sorted(set(G[g])-set(m))[:5]} extra {sorted(set(m)-set(G[g]))[:5]}")
miss = [g for g in G if g not in seen]
if miss: err.append(f"{len(miss)} group(s) without a line: {miss[:8]}")
print(f"{b}: {len(G)} groups, {len(seen)} lines -- " + ("OK" if not err else f"{len(err)} problem(s)"))
for e in err[:30]: print("  " + e)
