#!/usr/bin/env bash
# Portable paired-seat suite: one hero bot folder against the practice opponents (benchmark-only).
#   benchmarks/run_suite.sh <hero_bot_dir> <out_dir> [seeds]
# Environment overrides: PY (python, default python3), OPPS (space-separated names), BLINDS (default standard),
#   STACK (default 10000), JOBS (default 2), KEEP_LOGS (default 1).
# Opponent names are looked up in benchmarks/opponents/ first, then bots/.
# Every seed is played twice with seats swapped. Sealed seeds 1001-1200 are refused by paired_eval.py.
set -u
if [ $# -lt 2 ]; then echo "usage: $0 <hero_bot_dir> <out_dir> [seeds]"; exit 2; fi
HERO=$1; OUT=$2; SEEDS=${3:-761-763}
PY=${PY:-python3}; BLINDS=${BLINDS:-standard}; STACK=${STACK:-10000}; JOBS=${JOBS:-2}; KEEP_LOGS=${KEEP_LOGS:-1}
OPPS=${OPPS:-"bluffer_high bluffer_mid pressure rangebot trapper overfolder bluffer_low adaptive caller"}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
case "$HERO" in /*) ;; *) HERO="$(pwd)/$HERO";; esac
case "$OUT" in /*) ;; *) OUT="$(pwd)/$OUT";; esac
cd "$ROOT" || exit 1
mkdir -p "$OUT"
KL=""; [ "$KEEP_LOGS" = "1" ] && KL="--keep-logs"
rc=0
for opp in $OPPS; do
  if [ -d "benchmarks/opponents/$opp" ]; then path="benchmarks/opponents/$opp"
  elif [ -d "bots/$opp" ]; then path="bots/$opp"
  else echo "skip $opp (not found)"; continue; fi
  echo "=== $opp seeds $SEEDS blinds $BLINDS"
  "$PY" -W ignore benchmarks/paired_eval.py "$HERO" "$path" --seeds "$SEEDS" --blinds "$BLINDS" --stack "$STACK" \
      --jobs "$JOBS" $KL --out-dir "$OUT/$opp" > "$OUT/$opp.out" 2>&1 || { echo "  FAILED (see $OUT/$opp.out)"; rc=1; }
  grep -E "^  A: |Runner-reported|Deterministic digest" "$OUT/$opp.out"
done
exit $rc
