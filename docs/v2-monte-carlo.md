# Version 2 engineering brief — Monte Carlo postflop equity

**Branch:** `feature/strategy`. Do not merge to `main` or overwrite the validated preflop policy until tests support it.

## Goal

Replace the original fixed postflop `check/call/fold` heuristic with meaningful showdown equity calculations and conservative value-betting decisions for **heads-up No-Limit Texas Hold'em**.

## Equity simulation

- Use the tournament-approved `eval7` library for hand evaluation.
- Convert known hero cards and community cards into `eval7.Card` objects.
- For each trial, shuffle/simulate from the **remaining cards only**, drawing **2 opponent hole cards** and enough community cards to reach **5 board cards**. Never sample a known card twice.
- Evaluate both seven-card hands and count **win = 1, tie = 0.5, loss = 0**; equity is average payoff.
- Explicitly label initial estimates as **against a uniformly random opponent hand**. Never treat this as equity versus a player who has raised unless a range adjustment is actually implemented.
- Use a finite, configurable simulation count; avoid unbounded loops or expensive repeated deck construction. Use seeded tournament `random` rather than system clock reseeding. Don't cache a result across different boards or known cards incorrectly.
- Warmup and preflop must still work without a Monte Carlo call.

## Action policy

- When facing a bet, compare pot odds `amount_owed / (pot + amount_owed)` to *estimated equity*, allowing a conservative margin when the opponent's range is likely stronger than random.
- When checking is free, allow **value bets** with high equity and valid total-street raise amounts rather than blindly checking every strong hand. Do not default to bluffing with no fold-equity estimate.
- Keep fold versus stack-covering bet available. Handle all-ins, zero-owed calls, and under-minimum raises correctly; preserve tested Version 1.1 safety behavior.
- Be explicit that a naive equity threshold is not a GTO or fully optimal strategy. Do not conflate positive call EV with optimal raising EV.

## Engine and safety

- Contest input: `decide(game_state: dict) -> dict` in `my_bots/uo_monte/bot.py`.
- Only the bot folder ships. Keep required runtime functions inside `bot.py` or permitted `data/`.
- No network, subprocesses, file writes, dynamic imports or background work.
- Python 3.10, `eval7` allowed; decision cutoff **2,000 ms** under **0.5 CPU core** and **768 MB RAM**.
- Give the Monte Carlo computation a substantial time budget margin. Run sandbox benchmarks if Docker is available. Average runtime alone is insufficient—inspect worst case and p95.

## Required tests

1. Strong hand on a safe board yields high equity; weak hand or dominated draws appropriately lower.
2. Known cards and simulated opponent/runout cards never overlap; deterministic tests with fixed random seed.
3. Equity includes **ties as 0.5**, including a board that forces a split pot.
4. Flop (3 board cards), turn (4), and river (5) all evaluate correctly.
5. Postflop no-cost check, faced bet, legal value bet, short-stack fold and call/all-in cases.
6. `python3 -m unittest discover -s tests -v`
7. `make validate BOT=my_bots/uo_monte`.
8. Full `play.py` match vs caller, both seats, multiple seeded matches. Compare Version 1.1 by checking out the old commit in a separate temporary worktree or safely using a copy.
9. Docker sandbox match if available.

## Release policy

Do not claim competitive improvements from a single result. If the new postflop policy is slower, unstable, or loses consistently to baselines, revert or retain Version 1.1 as a fallback. Never automatically push new bot code to `main`.
