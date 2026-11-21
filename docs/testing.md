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

## External Floorfix benchmark — November 21, 2026

**Source:** Local Codex CLI report supplied by team. Competitor: publicly released MIT-licensed Tanuj Kakumani `bots/floorfix/bot.py` from https://github.com/txnujk09/fullhouse-poker-bot, upstream commit `4fe154318949aa60430682416f148733c6f0d564`. Source used **unchanged** in an isolated local checkout; no changes to UO-Monte, `pokercore/`, or `main` for this exercise.

**Important format limitation:** The benchmark used **flat 50/100 blinds**, because Floorfix hard-codes a 100-chip big blind in multiple preflop decisions. Floorfix was created for **6-max** rather than this event's heads-up format. These are local adaptation results, **not the actual rising-blind tournament format**.

- IEEE engine and Python 3.10.22, 10,000 starting chips each, 2-second per-decision deadline
- 20 seeds with swapped seats: 40 matches, 4,078 hands, all ending by elimination
- **UO-Monte V2: 23 wins, 17 losses (57.5%)**; seat 0: 10–10, seat 1: 13–7
- **Floorfix: 17 wins, 23 losses**; validator passed and separate 92-hand smoke match completed
- UO-Monte: 6,523 decisions, p95 **4.635 ms**, max **7.630 ms**; Floorfix 6,808 decisions, p95 **3.003 ms**, max **5.961 ms**
- **Reported errors/timeouts: 0/0** for each bot
- A 23–17 win split over 40 games is **not** conclusive evidence of superiority, especially given fixed blinds and the format adaptation

**V3 diagnostic priorities from local hand histories:**
1. **Range-aware river defense:** 43 of 46 terminal river calls cost chips, totaling 50,509 chips relative to folding those same decisions according to the local report; avoid using random-hand equity as though it were equity against a selected betting range
2. **Don't stack off blindly with one pair:** seed 5, seat 1, hand 5 reportedly lost 9,830 chips by repeatedly reraising top pair into top set
3. **Reassess board texture and opponent line:** seed 16, seat 1, hand 56 reportedly reraised pocket kings on a river paired with an ace against trips

**Next checkpoint:** Develop independently implemented V3 opponent-aware calling and stack-commitment logic, keep V2 as rollback, test against Tight/Mixed/Aggressive/Caller and Floorfix where appropriate, and retest official rising-blind format separately. Freeze, validate and push tested submission to public `main` before the team-reported 6:30 PM ET deadline.

## Version 3.1 opponent-aware river defense — November 21, 2026

**Source:** User-supplied Codex CLI screenshots. V3.1 implemented and benchmarked locally on `feature/strategy` but **not yet committed or pushed** at report time. V2 remains preserved at `ef760ca5bf14b367feac9accb3f4b3fbeb478181`.

New logic, only when facing a river bet: enumerate the **990** legal opponent hole-card combinations given 7 known cards, then weight holdings using public street/bet-size/action history and conservative priors. Preserve preflop, flop, turn and free-check river decisions. Use contestable pot odds when determining calling vs folding and allow raises only with stronger evidence against an opponent's range.

Codex reports **20 unit tests**, all **4 validator scenarios**, and **400 head-to-head local matches** completed; zero errors, timeouts or restarts.

| Opponent | Blinds | V2 wins / 40 | V3.1 wins / 40 |
|---|---|---:|---:|
| Caller | Rising | 40 | 40 |
| Aggressive | Rising | 37 | 34 |
| Tight | Rising | 22 | 26 |
| Mixed | Rising | 20 | 22 |
| External Floorfix | Flat 50/100 | 23 | 26 |
| **Total** | Mixed by opponent | **142 / 200** | **148 / 200** |

Timing reported: V3.1 overall decision p95 **4.362 ms**, max **9.243 ms**. For river decisions facing a bet, p95 dropped from **4.918 ms** to **0.537 ms**. Official half-core Docker sandbox timing remains to be verified.

**River-specific results (V2 → V3.1):**
- Aggressive: losing terminal calls **24/62 → 16/45**; relative-to-folding net **+179,416 → +181,679** chips, but paired live changes folded too often in some high-pressure spots and cost 3 match wins.
- Tight: **20/20 → 2/2** losing calls, relative net **−36,645 → −4,770**.
- Mixed: **84/116 → 24/49** losing calls, relative net **+10,549 → +73,917**.
- Floorfix: **43/46 → 9/22** losing calls, relative net **−50,509 → +29,623**; replay of exact V2 decisions suggested **52,069** chips saved at those decisions, but live-match effects differ.

**Critical unresolved weakness:** one-pair escalation on flop/turn. Codex reports V3.1 still lost **9,830 chips** by repeatedly reraising top pair into Floorfix's top set. Next focused task: V3.2 stack-commitment and reraising policy, retaining improved V3.1 river decisions and legal action safety. Measure regressions against Aggressive and all other benchmark opponents; do not overfit to a single match.

**Evaluation caution:** 148/200 versus 142/200 is a modest observed gain across heterogeneous opponents and not a robust statistical claim. These are homemade opponents plus a 6-max-derived external opponent under flat blinds, not an actual tournament field. Do not merge onto public `main` before release freeze, official validator and sandbox tests.

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
