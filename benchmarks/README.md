# Paired-seat benchmark harness (`paired_eval.py`)

Compares two bots fairly by playing every seed **twice with the seats swapped**,
using the official `play.py` runner. It does not touch any strategy code.

## Why this beats a single total win rate

A match is decided partly by luck of the deal. In a duplicate pair both bots get
the same cards, once in each seat, so a lucky deal helps each bot equally and
cancels out. Seat 0/seat 1 effects (button, first action) are also reported
separately instead of hidden inside one number. The report also gives
uncertainty ranges, so "6 wins out of 10" is not mistaken for proof of strength.
Every match is saved with its seed and exact command, so anyone can reproduce it.

## Quick start (from the repo root, venv active)

```bash
# Tiny sanity run (seeds 41-43, practice bots only, ~5 seconds)
python benchmarks/paired_eval.py bots/caller bots/template --seeds 41-43

# Compare two versions of your bot (A is the one reported on)
python benchmarks/paired_eval.py my_bots/uo_monte bots/caller --seeds 1-50 --jobs 2

# See the commands without running anything
python benchmarks/paired_eval.py bots/caller bots/template --seeds 41-43 --dry-run

# Re-score an archived matches.csv without playing anything (typed and validated)
python benchmarks/paired_eval.py --rescore benchmarks/results/caller_vs_template/matches.csv

# Self-tests
python tests/test_paired_eval.py -v
python tests/test_benchmark_opponents.py -v
```

Options: `--seeds 41-43,50`, `--blinds` (default `standard`), `--stack` (default
10000), `--hands-cap N`, `--out-dir DIR`, `--jobs N`, `--match-timeout SEC`,
`--keep-logs`, `--docker`, `--python`, `--play-py`, `--allow-sealed`.
Exit code 0 = all matches complete, 2 = some were incomplete, 1 = bad arguments.

**Sealed seeds 1001-1200 are refused** unless `--allow-sealed` is given. Only use
that flag for the final run the humans approve.

## Output files (default folder `benchmarks/results/<A>_vs_<B>/`)

| File | Contents |
|---|---|
| `matches.csv` | One row per match (two per seed): seed, `a_seat`, bot paths, blinds, starting stack, status, winner (A/B), stop reason, hands, final stacks, decisions, timeouts, errors, restarts, avg and max think ms per bot, duration, exit code, core hash, the exact command |
| `pairs.csv` | One row per seed: W / D / L for bot A |
| `manifest.json` | Git commit and branch, `git status`, SHA-256 of each `bot.py`, core hashes, Python and OS versions, assumptions, unavailable fields, deterministic digest |
| `summary.txt` | The human-readable report |

Rows are sorted by seed and seat and written with fixed formatting, so the same
inputs give byte-identical files. The **deterministic digest** hashes only the
results (not timings or wall-clock fields), so two runs can be compared with one
string. Timing columns will differ slightly between runs; that is normal.

Example `matches.csv` row (shortened):

```
41,0,bots/caller,bots/template,standard,10000,ok,B,one_player_left,73,0,20000,...
```

## How pairs are scored

For one seed, A plays seat 0 in match 1 and seat 1 in match 2.

- A wins both: pair **W**. A wins one each: pair **D**. A wins neither: pair **L**.
- If either match is not `ok` (timeout, hand limit, **nonzero runner exit code**,
  missing or inconsistent log), the pair is **incomplete** and is excluded, never guessed.
- Match status is `ok`, `incomplete:<reason>` or `error:exit_code=N`. A match is `ok` only
  if `play.py` exited 0 and its log is self-consistent (seed matches, both seats present,
  places are 1 and 2, the two final stacks add up to twice the starting stack, loser has 0).
  Any `error:` or `incomplete:` match is listed in the report and excluded from win rates.
- "Pair score" = (W + 0.5 D) / complete pairs. This is **our summary
  convention**; the organizer's rules define win/draw per pairing but the
  source does not say how draws are weighted in the final ranking.

## Uncertainty

- The two matches of a seed share the same cards, so they are **not independent**.
  Every interval therefore resamples **whole seeds** (pairs) with replacement.
- Match win rates (overall and per seat): percentile **cluster bootstrap over seeds**,
  2000 resamples, fixed RNG seed. Pair score: percentile bootstrap over pairs.
- Wilson intervals assume independent trials, so they are not used for match rates.
  They are not "conservative" in general: if every seed splits one win each, the cluster
  interval is narrower than Wilson; if both matches of a seed always agree, it is wider
  (both cases are tested).
- With fewer than 20 complete pairs, or when every pair has the same result, the report
  prints a WARNING: a 0%-0% interval from 3 seeds is not certainty. Roughly 330 matches
  per version are needed to tell 65% from 75%.
- **Team pair score** = (W + 0.5 D) / pairs is our own comparison convention. The
  organiser's rule only defines a win/draw/loss per pairing; how draws are weighted in the
  final ranking is not stated in the source. Do not quote it as the organiser's score.

## Limitations

- **Not a strength claim.** The sanity run uses practice bots only, on seeds
  41-43.
- The runner reports only average and maximum think time per bot. Per-decision
  p95 is **not available**; those fields are marked unavailable in the manifest.
- Winner is taken from the engine's `place` field when a match ends with
  `one_player_left`. Matches stopped any other way are marked incomplete.
- A nonzero exit code excludes a match even if its log finished. `play.py` exits 1 when a
  bot raised an error (the bot just folded that hand), so a bot with a harmless caught
  exception shows up as `error:exit_code=1`. That is deliberate: errors must be seen and
  fixed, and the count is printed in every report.
- The rescore checks types and consistency of the CSV, not that the matches really happened.
- Matches run through the host Python by default, not the competition container.
- Bots that use their own randomness may not replay identically, even with the
  same seed. The engine seeds each bot, but time-based behavior can vary.
- Timing under load (`--jobs` above 1) is not comparable to a single-job run.

## Docker timing (documented, not run)

The official limits (2 s per decision, 0.5 CPU, 768 MB) are only enforced in the
container. To check timing under those limits: build the sandbox with
`make sandbox`, then add `--docker` (e.g. `--seeds 41-43 --docker`). Use
`--jobs 1` so timings are not distorted. This path has **not** been run here.

## Comparing two versions of your bot

Copy the older bot folder (e.g. `my_bots/uo_monte_v32/`), then run the harness
with A = new, B = old on the same seeds. The pair score and W/D/L answer "is the
new version better on identical deals?", which a total win rate cannot do.

## Practice opponents (benchmark-only, `benchmarks/opponents/`)

Two original, deterministic toy bots for testing exploitation logic. They live outside
`my_bots/uo_monte/`, use only public state and legal actions, have no randomness, and
pass `python pokercore/validator.py <folder>`. All tunable numbers are in each file's
`PARAMS` dictionary. Each folder is self-contained.

| Bot | Behaviour | Tests |
|---|---|---|
| `overfolder` | Opens only decent hands; postflop folds everything below two pair to any bet of 25% pot or more, calls small bets with any pair, bets only top pair or better. | Fold-equity gains, and whether a bluff-happy bot wastes chips against a caller-like range. |
| `trapper` | Never bluffs. Limps premium hands, checks and calls strong hands on the flop, then check-raises 3x on the turn and bets 90% pot on the river; re-raises preflop raises. | Whether semi-bluffs and thin value bets are punished, and check-raise losses. |

They are **toys**. Real opponents do not fold or slowplay this uniformly, so results against
them say nothing about tournament win probability. Keep tuning data and holdout data apart.

```bash
python benchmarks/paired_eval.py my_bots/uo_monte benchmarks/opponents/overfolder --seeds 101-120
python benchmarks/paired_eval.py my_bots/uo_monte benchmarks/opponents/trapper --seeds 101-120
```
