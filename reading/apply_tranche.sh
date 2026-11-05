#!/bin/bash
# agent/phaseP/apply_tranche.sh -- 27 Oct 2026. Apply one Phase P tranche plan, in the fixed order.
#   bash agent/phaseP/apply_tranche.sh TAG MD5            -> md5 check + CHECK phase only (read-only)
#   bash agent/phaseP/apply_tranche.sh TAG MD5 commit     -> md5 check, then setaside --commit, regroup --commit, ledger --commit
# Run from cleaned/. Stops at the first failure. The commit run is Glenn's to approve, after he has read the check output.
set -euo pipefail
TAG="$1"; WANT="$2"; MODE="${3:-check}"
PLAN="agent/phaseP/plan_${TAG}.tsv"
[ -f "$PLAN" ] || { echo "no plan $PLAN"; exit 1; }
HAVE=$(md5sum "$PLAN" | cut -c1-32)
case "$HAVE" in "$WANT"*) echo "md5 OK  $HAVE  $PLAN";; *) echo "md5 MISMATCH: have $HAVE, expected $WANT -- STOP"; exit 1;; esac
if [ "$MODE" != commit ]; then
  python3 -u agent/partB_apply_21oct.py --phase check --plan "$PLAN"
  echo; echo "Check only. Nothing written. Commit run: bash agent/phaseP/apply_tranche.sh $TAG $WANT commit"
  exit 0
fi
python3 -u agent/partB_apply_21oct.py --phase setaside --plan "$PLAN" --commit
python3 -u agent/partB_apply_21oct.py --phase regroup  --plan "$PLAN" --commit
python3 agent/reading_ledger.py --add "$PLAN" --campaign "phaseP_${TAG}" --group-col from_group --verdict-col action --commit
echo; echo "Applied $PLAN (setaside, regroup, ledger). Next: the rebuild chain (one at a time)."
