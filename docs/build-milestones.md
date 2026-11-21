# UO-Monte: competition-day build milestones

**Goal:** build a strong, reliable heads-up poker agent before the organizers' submission cutoff. The attendee reports the event runs **9:30 AM–10 PM**, but the code deadline may be earlier; ask organizers for the **exact submission cutoff** immediately.

The team will not spend the entire event on a single ambitious model. We work in short release gates so that a validated submission is always available.

## Release 0 — launchable baseline (as soon as dependencies work)

- Run `python3 play.py my_bots/uo_monte bots/caller --seed 7`.
- Run `make validate BOT=my_bots/uo_monte`.
- Save the last passing bot on `main`.
- Check match logs for errors, unsafe checks, and timeout/illegal raises.
- Set up Docker sandbox if available, but don't allow Docker troubleshooting to block a valid baseline.

## Release 1 — strong heads-up preflop

- Position-aware opening, defense, 3-bet and short-stack ranges.
- Effective stacks divided by current big blind; blinds rise every 20 hands.
- Prefer a coherent simple policy over dozens of special cases.

## Release 2 — fast equity and EV

- Use approved `eval7` for board/hand evaluation and Monte Carlo equity.
- Measure wall-time in sandbox; cap sampling to leave a substantial safety margin inside the 2-second decision budget on 0.5 CPU.
- Calls compare equity with pot odds; raises also consider fold equity, bet size, and realized equity.

## Release 3 — exploit adaptation

- Analyze `match_action_log` by opponent `bot_id`, not seat.
- Track fold-to-raise, calling frequency, aggression, and showdown tendencies.
- Adjust only after enough observations; otherwise fall back to sensible heads-up strategy.

## Release 4 — competitive testing and freeze

- Benchmark against the organizer's caller plus contrasting tight, aggressive, and random baselines.
- Use repeated seeds and seat swaps, not a single match.
- Record wins/losses, timeouts and average decision time. Revert regressions.
- Stop experimenting with enough time to validate and submit **public `main`** before the actual cutoff.

## Parallel work for two teammates

**Teammate A — integration and reliability:** Python/WSL setup, match runner, validator, benchmark scripts, and action-safety checks.

**Teammate B — strategy:** preflop ranges, equity, betting policy, opponent model.

Both review changes. To avoid conflicts, only one teammate directly modifies `my_bots/uo_monte/bot.py` at a time; split work into independent functions or pair on the submission entry.

## Constraints we do not compromise

- Official engine and API from `FreddyyAndrews/poker-hackathon-kit`.
- Python 3.10; only approved packages.
- Two-second action deadline, 768 MB, 0.5 CPU.
- No network, file writes or background work in the tournament sandbox.
- All runtime logic inside the collected bot folder (other directories are not submitted).
- Registered identifier `uo_monte` must match the submission form exactly.
