#!/bin/bash
# TASK-CLAUDE-006 matrix. V3.4 = disposable copy of commit a5ea561 at /tmp/v34/uo_monte_v34 (sha256 e887f6a3...)
cd /home/claude/review/repo
PY=/home/claude/kit/.venv/bin/python
V34=/tmp/v34/uo_monte_v34
OUT=/tmp/t006/results
declare -A SEEDS=( [dev]="601-620" [hold]="621-640" )
declare -A ARGS=( [standard]="--blinds standard --stack 10000" [turbo]="--blinds turbo --stack 10000" [flat10bb]="--blinds 100/200/20 --stack 2000" )
for setting in standard turbo flat10bb; do
 for block in dev hold; do
  for opp in bluffer_low bluffer_mid bluffer_high pressure adaptive; do
      d=$OUT/${block}_${setting}_${opp}
      echo "=== $block $setting $opp $(date +%T)"
      $PY -W ignore benchmarks/paired_eval.py $V34 benchmarks/opponents/$opp --seeds ${SEEDS[$block]} ${ARGS[$setting]} --jobs 2 --keep-logs --out-dir $d > $d.out 2>/dev/null
      echo "exit $?"
  done
 done
done
echo ALLDONE
