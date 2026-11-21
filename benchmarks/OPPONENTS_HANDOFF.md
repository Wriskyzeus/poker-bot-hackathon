# Practice opponents: handoff notes (benchmark-only)

Nothing here is part of the tournament submission. Never copy these files into `my_bots/`.
All commands run from the repository root with the project's Python 3.10 (`PY=.venv/bin/python` or `python3`).

## Opponents (`benchmarks/opponents/<name>/bot.py`)
| Name | Source | Style |
|---|---|---|
| overfolder, trapper | hand-written (TASK-003) | folds too much / value-only slowplayer |
| bluffer_low, bluffer_mid, bluffer_high | rendered from `_adversary_src.py` | value + bluffs at 0.5x / 1.0x / 1.6x frequency |
| pressure | rendered from `_adversary_src.py` | wide opens, 3-bets, 4-bets, push/fold at 15 bb or less |
| adaptive | rendered from `_adversary_src.py` | bluffer_mid plus match-local fold-rate tracker |
| rangebot | independent code (TASK-007) | eval7 equity versus an estimated range, MDF-based defence |

Edit `_adversary_src.py`, then run `python3 benchmarks/opponents/build_adversaries.py`; a test fails if the
rendered folders drift from the source. All are designed stress tests, not predictions of real entrants.

## Canonical hand ids (important when comparing two hero versions)
The opponents' pseudo-random choices are a hash of the **hand number**, their own cards and the board.
They do not depend on the runner's match id, on `hand_id` prefixes, or on either bot's name or folder, so two
hero versions meet identical opponent choices in identical spots. Deals depend only on `--seed`.
`tests/test_adversary_opponents.py::TestCanonicalHandIds` and `tests/test_rangebot.py` enforce this.
A custom runner must still pass the engine's real `hand_num` and the same `--seed`.

## Check the install
    $PY -m unittest discover -s tests -p "test_*.py"
    for b in overfolder trapper bluffer_low bluffer_mid bluffer_high pressure adaptive rangebot; do
      make validate BOT=benchmarks/opponents/$b PYTHON=$PY; done

## Paired-seat benchmark of one bot folder
    benchmarks/run_suite.sh <hero_bot_dir> <out_dir> <seeds>
    # example: PY=.venv/bin/python benchmarks/run_suite.sh /tmp/frozen/uo_monte_v34 /tmp/out/v34 861-880
Options by environment variable: `OPPS="bluffer_high rangebot"`, `BLINDS=turbo`, `BLINDS=100/200/20 STACK=2000`,
`JOBS=2`, `KEEP_LOGS=0`. Each seed is played twice with seats swapped. Outputs per opponent: `matches.csv`,
`pairs.csv`, `manifest.json`, `summary.txt`, `logs/` and `<opp>.out` (with a deterministic digest).

## Compare a candidate with the baseline on the same seeds
    benchmarks/run_suite.sh /tmp/frozen/uo_monte_v34 /tmp/out/v34 861-880
    benchmarks/run_suite.sh /tmp/frozen/candidate    /tmp/out/cand 861-880
    $PY benchmarks/compare_candidates.py /tmp/out/v34 /tmp/out/cand
The comparison prints match wins, duplicate-pair W/D/L, hero problems, changed pairs, and verifies from the
logs that both runs saw the same deals and hand ids for every hand number (exit code 1 on any mismatch).
Use disposable copies of the bots; the hero folder may have any name.

## Seed hygiene
Used so far: 301-340, 601-640, 721-760, 761-800, 801-840. Reserved for independent V5-R acceptance: 861-880.
Sealed, never iterate on: 1001-1200 (`paired_eval.py` refuses them without `--allow-sealed`).

## Archival scripts
`benchmarks/task006/*` reproduce the TASK-006 report inside the original sandbox (they contain `/tmp/...`
paths and expect the hero to be named `uo_monte_v34`). Use `run_suite.sh` and `compare_candidates.py` instead.

## Requirements
Python 3.10 and `eval7` (rangebot and the hero need it); nothing else beyond the starter kit.
