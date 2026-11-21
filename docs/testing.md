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

## Version 2 Monte Carlo benchmark — November 21, 2026

**Source:** report from local Codex CLI run in the user's WSL Ubuntu environment; the underlying match logs were not independently uploaded. V2 was subsequently committed to `feature/strategy` at `ef760ca5bf14b367feac9accb3f4b3fbeb478181`; the V1.1 reference was isolated from commit `26c0a93`.

Both versions played **seeds 1–20 in both seat orders** against `bots/caller`: 40 freezeout matches each, 10,000 starting chips, standard blind schedule.

| Metric | V1.1 | V2 |
|---|---:|---:|
| Seat 1 wins / losses | 11 / 9 | 20 / 0 |
| Seat 2 wins / losses | 12 / 8 | 20 / 0 |
| Total wins / matches | 23 / 40 | 40 / 40 |
| Observed win rate | 57.5% | 100% |
| Average hands per match | 140.2 | 47.3 |
| Average match wall time | 0.737 s | 0.786 s |
| Total benchmark wall time | 29.48 s | 31.43 s |
| Mean / p95 / max decision time | 0.012 / 0.043 / 0.649 ms | 2.118 / 3.719 / 7.519 ms |
| Reported errors / decision timeouts / match timeouts | 0 / 0 / 0 | 0 / 0 / 0 |

- **Validation:** 14 unit tests and all 4 organizer validator scenarios passed. V2 also won seed-7 smoke match after 46 hands.
- **Caveat:** Caller never bet postflop. These results confirm V2's value-betting effectiveness versus a passive caller; they **do not** test folding/calling/raising against postflop bets, or quantify its strength against competent agents.
- **Compute caveat:** The measured local maximum of 7.519 ms is far under the 2,000 ms deadline, but official sandbox (0.5 CPU, 768 MB) timing should still be verified.
- **Release decision:** Use V2 as the experimental development baseline. Retain V1.1 commit `26c0a93` and a stable `main` until V2 beats an opponent that bets and raises postflop and meets sandbox constraints.
- **Next:** Implement test-only postflop aggressive, tight and randomized benchmark opponents outside the collected `my_bots/uo_monte/` folder; evaluate repeated seeded matches with swapped seats, collect logs and inspect costly misplays. Do not modify `pokercore/` or merge into `main` prematurely.

## Aggressive / tight / mixed local benchmarks — November 21, 2026

**Source:** User-shared screenshots of the local Codex CLI final report. Tests used the official local engine for heads-up freezeouts, 10,000-chip starting stacks, seeds 1–20 in both seat orders, for each of three benchmark opponents and each strategy version (**240 matches total**).

| Practice opponent | V1.1 wins / 40 | V2 wins / 40 | V2 by first / second seat | V2 p95 / max |
|---|---:|---:|---|---|
| Aggressive | 2 (5%) | 37 (92.5%) | 20/20, 17/20 | 3.671 / 5.999 ms |
| Tight | 39 (97.5%) | 22 (55%) | 8/20, 14/20 | 3.634 / 5.345 ms |
| Mixed | 2 (5%) | 20 (50%) | 9/20, 11/20 | 3.701 / 7.278 ms |

Reported **V2 decision p95 ~3.682 ms and maximum ~7.278 ms across 9,126 decisions** in local execution. **Zero errors, timeouts or restarts** reported, and all three benchmark opponents passed the official validator. Sandbox timing remains unverified.

**Three diagnosed leaks:**
1. Calling too loosely against strong betting ranges. Report says all 20 terminal river calls against Tight lost chips, costing 36,645 compared with folding those decisions; equity against a random opponent hand is not equity against a selected bet range.
2. Excessive one-pair raises or stack commitments: report cites a loss of 9,790 chips versus top set after repeatedly raising top pair.
3. Thin river value bets can provoke costly check-raises: versus Mixed, 21 of 34 in-position river bets reportedly did worse than checking.

**Decision:** V2 is a credible development base (especially against caller/aggressive), but *not yet proven universally superior*: V1.1 is far stronger than V2 against this Tight practice opponent. Keep V1.1 saved, avoid merging V2 to `main`, and improve V3 via opponent-specific ranges and better check-back/value-bet/raise decisions. Do not overfit exclusively to these three home-built practice bots. Independent external-bot benchmarking is on hold pending organizer approval (see `docs/external-bot-benchmarking.md`).

**Git status at last check:** Version 2 was pushed to `feature/strategy` in commit `ef760ca5bf14b367feac9accb3f4b3fbeb478181`. `main` holds documentation and the original tournament template; user is collecting organizer approval before importing external bots.

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
