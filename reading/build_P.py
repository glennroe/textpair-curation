#!/usr/bin/env python3
"""build_P.py -- Phase P batches: dump_<tag>.tsv -> p_<batch>.txt (one file per server batch), groups in front-file order.
  python3 build_P.py dump_t02.tsv                       full files (t01 format)
  python3 build_P.py dump_t02.tsv --compact [--out DIR] compact files (22 Oct streamlining test): within each group,
      every document occurring in more than one row is printed once (d1, d2 ...) and every passage that occurs in more than one row is
      printed once ([A], [B] ...); rows then cite them. A passage occurring in one row only is printed inline under
      its row, as in the full format. Every row is still listed with its own S and T. The 'row NNN |' lines keep the
      full format's shape, so cover_P.py, build_rc.py and compile_P.py read both formats.
  --batches a-b  only those batches."""
import argparse, csv, os, sys
from collections import Counter, defaultdict, OrderedDict
csv.field_size_limit(sys.maxsize)
ap = argparse.ArgumentParser()
ap.add_argument("dump"); ap.add_argument("--compact", action="store_true")
ap.add_argument("--out", default="."); ap.add_argument("--batches", default="")
a = ap.parse_args()
lo, hi = (map(int, a.batches.split("-")) if a.batches else (-1, 10**9))
os.makedirs(a.out, exist_ok=True)
B = defaultdict(OrderedDict)
for r in csv.DictReader(open(a.dump, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
    if lo <= int(r["batch"]) <= hi:
        B[int(r["batch"])].setdefault(r["group_id"], []).append(r)

def full(rows):
    out = []
    for i, r in enumerate(rows):
        mark = "FRONT " if i == 0 else ""
        out.append(f"  {mark}row {r['rowid']} | S {r['sy']} {r['sa']} | {r['st']}  ||  T {r['ty']} {r['ta']} | {r['tt']}\n"
                   f"     S: {r['sp']}\n     T: {r['tp']}\n")
    return out

def letters(i):
    s = ""
    while True:
        s = chr(65 + i % 26) + s; i = i // 26 - 1
        if i < 0: return s

def compact(rows):
    dc = Counter(k for r in rows for k in ((r["sy"], r["sa"], r["st"]), (r["ty"], r["ta"], r["tt"])))
    docs = OrderedDict()
    for r in rows:
        for k in ((r["sy"], r["sa"], r["st"]), (r["ty"], r["ta"], r["tt"])):
            if dc[k] > 1: docs.setdefault(k, f"d{len(docs) + 1}")
    cnt = Counter(p for r in rows for p in (r["sp"], r["tp"]))
    pas = OrderedDict()
    for r in rows:
        for p in (r["sp"], r["tp"]):
            if cnt[p] > 1 and p not in pas: pas[p] = letters(len(pas))
    out = []
    if docs: out += ["  documents in more than one row:\n"] + [f"    {k} = {y} {au} | {ti}\n" for (y, au, ti), k in docs.items()]
    if pas:
        out.append("  passages carried by more than one row:\n")
        out += [f"    [{k}] {p}\n" for p, k in pas.items()]
    for i, r in enumerate(rows):
        mark = "FRONT " if i == 0 else ""
        def lab(y, au, ti): return docs.get((y, au, ti)) or f"{y} {au} | {ti}"
        sref = f" [{pas[r['sp']]}]" if r["sp"] in pas else ""
        tref = f" [{pas[r['tp']]}]" if r["tp"] in pas else ""
        out.append(f"  {mark}row {r['rowid']} | S {lab(r['sy'], r['sa'], r['st'])}{sref}  ||  T {lab(r['ty'], r['ta'], r['tt'])}{tref}\n")
        if not sref: out.append(f"     S: {r['sp']}\n")
        if not tref: out.append(f"     T: {r['tp']}\n")
    return out

for b, groups in sorted(B.items()):
    nr = sum(len(v) for v in groups.values())
    out = [f"BATCH P{b:04d}: {len(groups)} groups, {nr} rows to read"
           + (" (COMPACT format: documents and repeated passages printed once per group)" if a.compact else "") + "\n"]
    for g, rows in groups.items():
        out.append(f"\n--- GROUP {g}  ({len(rows)} rows) ---\n")
        out += compact(rows) if a.compact else full(rows)
    open(os.path.join(a.out, f"p_{b:04d}.txt"), "w", encoding="utf-8").write("".join(out))
    print(b, len(groups), nr)
