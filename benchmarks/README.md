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

# Self-tests
python tests/test_paired_eval.py -v
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
- If either match is incomplete (timeout, hand limit, crash, missing result),
  the pair is **incomplete** and is excluded, never guessed.
- "Pair score" = (W + 0.5 D) / complete pairs. This is **our summary
  convention**; the organizer's rules define win/draw per pairing but the
  source does not say how draws are weighted in the final ranking.

## Uncertainty

- Single-match win rates: 95% Wilson interval.
- Pair score: 95% percentile bootstrap over pairs (2000 resamples, fixed RNG seed).
- Assumptions: seeds are independent and identically distributed; the Wilson
  interval treats the two matches of a seed as independent, which is
  conservative. With few seeds the intervals are very wide. Roughly 330 matches
  per version are needed to tell 65% from 75%.

## Limitations

- **Not a strength claim.** The sanity run uses practice bots only, on seeds
  41-43.
- The runner reports only average and maximum think time per bot. Per-decision
  p95 is **not available**; those fields are marked unavailable in the manifest.
- Winner is taken from the engine's `place` field when a match ends with
  `one_player_left`. Matches stopped any other way are marked incomplete.
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
