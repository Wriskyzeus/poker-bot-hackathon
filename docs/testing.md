# Testing and benchmarking

Use **organizer's own** `play.py`, not other Fullhouse implementations.

```bash
make install
python3 play.py my_bots/uo_monte bots/caller --seed 7
python3 play.py my_bots/uo_monte bots/caller --seed 7 --show
python3 play.py my_bots/uo_monte bots/caller --seed 7 --log match.jsonl
make validate BOT=my_bots/uo_monte
make sandbox
python3 play.py my_bots/uo_monte bots/caller --docker
```

`make sandbox` / `--docker` require Docker; `make validate` does not.

## First local baseline result — November 21, 2026

**Status:** Organizer's unchanged starter bot executed a complete local freezeout match, and **passed the official validator** on November 21, 2026.

```bash
python3 play.py my_bots/uo_monte bots/caller --seed 7
```

- Official core fingerprint reported: `2687febda342c653`
- Result: `caller` won, `uo_monte` lost after **134 hands** (one player left)
- Final stacks: `caller` **20,000**, `uo_monte` **0**
- Reported average think time: 0 ms (display rounded)
- No errors/timeouts were shown in the terminal summary
- **Interpretation:** setup and game integration work; this is **one seed**, not a statistically meaningful performance benchmark. The bot still uses the unmodified starter strategy.

**Validator result:** `make validate BOT=my_bots/uo_monte` returned **PASSED**. Four provided scenarios passed: `preflop_call_or_fold` (fold), `postflop_can_check` (check), `river_facing_large_bet` (fold), and `short_stack_all_in_decision` (raise to 300). These are legality/contract tests; passing them does not establish tournament competitiveness or sandbox runtime performance.

**Next gate:** Implement the first heads-up strategy enhancement on a feature branch, test it across repeated matched seeds and both seats, and re-run the validator before considering a merge to `main`.

## First upgraded preflop result — November 21, 2026

A locally developed `feature/strategy` version of UO-Monte passed the organizer's validator (four supplied cases) and then won a seed-7 freezeout match against `bots/caller`.

```bash
make validate BOT=my_bots/uo_monte
python3 play.py my_bots/uo_monte bots/caller --seed 7
```

- **Validator:** PASSED (the provided preflop, postflop, river and short-stack scenarios).
- **Match result:** `uo_monte` 20,000 chips; `caller` 0; **148 hands**; no errors/timeouts shown.
- **Prior organizer-template baseline:** same seed 7 vs caller lost after 134 hands.
- **Evidence limitation:** one seed is not a meaningful performance estimate, and Version 1 was later committed and pushed to `feature/strategy`, and the subsequent all-in safety fix also reached that branch. `main` still holds the original template.
- **Next test:** multiple seeds with seat orders swapped. Check win rate, invalid actions, errors, timeouts and average decision time. Review the diff before committing.

## Five-seed paired benchmark — November 21, 2026

**Version 1 heads-up preflop strategy (later committed on `feature/strategy`)** versus the official `bots/caller`. User ran both bot orderings for seeds 1–5:

```bash
for seed in 1 2 3 4 5; do
  python3 play.py my_bots/uo_monte bots/caller --seed "$seed" | tail -n 4
  python3 play.py bots/caller my_bots/uo_monte --seed "$seed" | tail -n 4
done
```

| Seed | UO-Monte first seat | UO-Monte second seat | Qualification pairing |
|---|---|---|---|
| 1 | Loss (122 hands) | Loss (168 hands) | Lost |
| 2 | Loss (113 hands) | Loss (177 hands) | Lost |
| 3 | Loss (144 hands) | Win (141 hands) | Draw |
| 4 | Win (153 hands) | Win (123 hands) | Won |
| 5 | Win (132 hands) | Loss (140 hands) | Draw |

- **Overall:** 4 wins, 6 losses (40% observed freezeout match win rate).
- **Duplicate-pair score:** 1 pairing won, 2 drawn, 2 lost.
- **Execution:** no crash/timeout reports visible in the displayed match summaries; the organizer's four validator scenarios also passed.
- **Interpretation:** promising that the bot can win, but this is *not* evidence of competitiveness or an improvement over the original template, which has not been evaluated on the same ten matches yet.
- **Next gate:** preserve Version 1 in `feature/strategy`, compare the unchanged `bots/template` on the same seeds/seat orders, review the Version 1 code, then tune weaknesses before considering Monte Carlo additions. Do **not** merge unbenchmarked upgrades into `main`.

## Version 1.1 saved — November 21, 2026

- **Commit:** `26c0a935eea310dbe7c64527d202f02a30431a53` on `feature/strategy`.
- **Files:** `my_bots/uo_monte/bot.py` and `tests/test_uo_monte_bot.py`.
- **Safety:** A planned fold is no longer accidentally converted to an all-in call when a bet covers the stack; targeted regression tests added.
- **Verification reported by teammate:** local `make validate BOT=my_bots/uo_monte` passed; seed-7 local freezeout against caller still won after 148 hands. Additional multi-seed benchmarks have **not** been rerun after the safety fix.
- **Next:** Develop a bounded postflop Monte Carlo equity policy on `feature/strategy`, without rewriting the validated preflop policy. Re-run complete tests before merging.

## Checklist

- [ ] Warmup returns safely.
- [ ] Valid actions and total-street raise amounts; never checks when it owes money.
- [ ] Handles short stacks, all-ins, empty preflop board and final street.
- [ ] No non-allowlisted modules or forbidden behavior.
- [ ] Under 2 seconds on half a CPU core, not just your laptop.
- [x] Initial local freezeout completed without reported errors/timeouts (seed 7; official validator and sandbox still pending).
- [ ] Reproducible matched seeds and swapped seats.
- [x] Official validator passed on `my_bots/uo_monte` (four provided scenarios, November 21, 2026).

Record match seeds, commit SHA, opponent, seat, outcomes, errors/timeouts, and average think time. Qualification is based on duplicate pairing wins/draws, not fixed-hand bb/100. Keep a known-good bot on `main`.
