#!/bin/bash
# agent/phaseP/run_readers.sh -- 27 Oct 2026. Phase P FIRST READERS, run headless on the server with Claude Code.
#
# Each batch p_NNNN.txt gets one Opus reader (`claude -p`), which writes
#   agent/phaseP/TAG/v/v_NNNN.tsv      the verdicts (one line per group, checked with cover_P.py)
#   agent/phaseP/TAG/v/notes_NNNN.txt  verdict counts, FOLD CANDIDATES, MOVEs on no shared text, FOR GLENN items
# Nothing here touches the database: readers may only Read/Write files and run cover_P.py.
# Rulings and everything after the first readers stay in the claude.ai session: pull v/ to the laptop when done.
#
# Usage (from cleaned/, after the dump and build_P):
#   bash agent/phaseP/run_readers.sh TAG [FIRST LAST] [PARALLEL]
#   bash agent/phaseP/run_readers.sh t10              # batches 0-24, 4 at a time
#   bash agent/phaseP/run_readers.sh t10 0 0 1        # one batch only (trial)
#   nohup bash agent/phaseP/run_readers.sh t10 > agent/phaseP/t10/readers.log 2>&1 &
# Re-running is safe: a batch whose v file already passes cover_P is skipped.
# Each reader's own log: agent/phaseP/TAG/v/log_NNNN.txt
set -uo pipefail
TAG="$1"; FIRST="${2:-0}"; LAST="${3:-24}"; PAR="${4:-4}"
D="agent/phaseP/$TAG"
[ -f "$D/INSTRUCTIONS_P.md" ] || { echo "no $D/INSTRUCTIONS_P.md (copy it from agent/phaseP/kit/)"; exit 1; }
[ -d "$D/compact" ] || { echo "no $D/compact (run build_P first)"; exit 1; }
mkdir -p "$D/v"
command -v claude >/dev/null || { echo "claude not on PATH"; exit 1; }

read_one() {
  local N; N=$(printf "%04d" "$1")
  local P="$D/compact/p_$N.txt" V="$D/v/v_$N.tsv" NT="$D/v/notes_$N.txt" L="$D/v/log_$N.txt"
  [ -f "$P" ] || { echo "[$N] no batch file, skipped"; return; }
  if [ -f "$V" ] && python3 agent/phaseP/kit/cover_P.py "$P" "$V" 2>&1 | grep -q "OK"; then
    echo "[$N] already done (cover_P OK), skipped"; return
  fi
  echo "[$N] reader started $(date +%H:%M:%S)"
  claude -p "You are a first reader in Phase P of the TextPAIR/ModERN text-reuse cleanup (French printed works 1500–1800). Read $D/INSTRUCTIONS_P.md in full first; it defines the verdicts, the scope rules, the chunk and length rules and the output format. Then read EVERY group and EVERY row (both S and T passages) of $P yourself, paging through it with Read offsets. No classifying scripts, no sampling, no default verdicts. Write one line per group to $V (header \`group	verdict	dest	rows	source	note\`), then run \`python3 agent/phaseP/kit/cover_P.py $P $V\` and fix anything it reports until it says OK. Finally write $NT with: verdict counts; FOLD CANDIDATES (groups you kept apart that may be one unit — one poem/scene/short letter or speech — with ids and a few words); any MOVE that rests on no shared text or visible run-on; and FOR GLENN items (doublons, wrong dates, bad author strings, dictionary-form volumes not already covered, unsure attributions), each with group ids, rowids, titles and years. Do not ask questions: anything you would ask goes into FOR GLENN in $NT. Do not touch any other file and do not run any command other than cover_P.py." \
    --model opus \
    --allowedTools "Read" "Write" "Edit" "Bash(python3 agent/phaseP/kit/cover_P.py:*)" \
    > "$L" 2>&1
  if [ -f "$V" ] && python3 agent/phaseP/kit/cover_P.py "$P" "$V" 2>&1 | grep -q "OK"; then
    echo "[$N] done $(date +%H:%M:%S)$( [ -f "$NT" ] || echo '  (no notes file!)')"
  else
    echo "[$N] FAILED: no verdict file or cover_P not OK (see $L); rerun the script to retry"
  fi
}
export -f read_one; export D

seq "$FIRST" "$LAST" | xargs -P "$PAR" -I{} bash -c 'read_one {}'

echo; echo "== summary $(date +%H:%M:%S)"
ok=0; bad=""
for i in $(seq "$FIRST" "$LAST"); do
  N=$(printf "%04d" "$i")
  if [ -f "$D/v/v_$N.tsv" ] && python3 agent/phaseP/kit/cover_P.py "$D/compact/p_$N.txt" "$D/v/v_$N.tsv" 2>&1 | grep -q "OK"; then ok=$((ok+1)); else bad="$bad $N"; fi
done
echo "cover_P OK: $ok of $((LAST-FIRST+1))${bad:+   missing/failing:$bad}"
cat "$D"/v/notes_*.txt > "$D/notes_all.txt" 2>/dev/null && echo "notes collected: $D/notes_all.txt"
echo "Next: pull $D/v/ and $D/notes_all.txt to the laptop and hand them to the claude.ai session."
