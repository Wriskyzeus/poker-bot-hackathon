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

## Version 3.2 effective-stack and reraise defense — November 21, 2026

**Source:** User-shared Codex CLI benchmark report, local WSL Python 3.10.22. **V3.1 was committed on `feature/strategy` at `c12396ea372be6be86930e360c17d1e7998582e0`. V3.2 was subsequently committed and pushed to `feature/strategy` at `cfab27c26222423b46b7293c6416785c7115369e`.** `main` does not yet contain V3.

V3.2 changed flop/turn response to bets using effective stacks, stack-to-pot ratio, hand class, public betting history and opponent-weighted equity estimates. It restrains repeated one-pair reraises against value-heavy ranges while preserving raises with strong hands or justified short-stack situations. Preflop and V3.1 river-defense behavior were left unchanged.

**Testing:** 29 unit tests and the official validator passed. Local paired seeds 1–20 in both seats for V3.1 and V3.2 across five opponents (**400 matches total**). No errors/timeouts/restarts were reported.

| Opponent | Blinds | V3.1 wins / 40 | V3.2 wins / 40 | Flop/turn all-in showdown losses, V3.1 → V3.2 (chips) |
|---|---|---:|---:|---:|
| Caller | Rising | 40 | 40 | 759 → 759 |
| Aggressive | Rising | 34 | 31 | 17,906 → 29,282 |
| Tight | Rising | 26 | 33 | 141,891 → 44,878 |
| Mixed | Rising | 22 | 24 | 132,305 → 69,350 |
| External Floorfix | Flat 50/100 | 26 | 34 | 153,481 → 16,819 |
| **Total** | Mixed | **148 / 200** | **162 / 200** | **446,342 → 161,088 (~64% reduction)** |

The 'losses' column sums losses in all-in showdowns where the final commitment occurred on the flop or turn; it is **not** a total EV or win-rate measure. Reported overall local decision p95/max: V3.1 **3.656 / 10.088 ms** vs V3.2 **3.647 / 7.465 ms**. Facing flop or turn bets, p95/max improved from **2.896 / 10.088** to **1.867 / 2.748 ms**.

**Hand-history examples:**
- Floorfix seed 5 / seat 1 / hand 5: V3.2 called a flop check-raise with top pair instead of repeatedly reraising into top set, reducing the lost chips from **9,830 to 5,664**. Both versions ultimately lost that match.
- Aggressive seed 4 / seat 0 / hand 1: V3.2 called the flop with pocket tens rather than raising; later river price induced a fold. V3.1 won **10,000** chips on the hand while V3.2 lost **5,801**, illustrating the cost of overly passive lines against bluffs.

**Recommended release policy:** Keep V3.2 as the *candidate development baseline*, now preserved on `feature/strategy` after verification (29 unit tests + official validator passed); retain the earlier V3.1 (`c12396e`) and V2 (`ef760ca`) as rollback points. Do not promote to tournament `main` based only on one opponent pool; test the true half-core Docker sandbox and fix regressions against aggressive players without giving back strong-range discipline. Freeze and push the final tested bot well before 6:30 PM ET.


**Verified GitHub checkpoint:** `cfab27c26222423b46b7293c6416785c7115369e`, message "Implement UO-Monte V3.2 stack commitment intelligence"; exactly `my_bots/uo_monte/bot.py` and `tests/test_uo_monte_bot.py` changed. Codex reported tracked working tree clean and local `benchmarks/` directory untracked. No `main` or teammate-branch modification.

## Version 3.3 adaptive aggression — November 21, 2026

**Source:** Team-supplied local Codex CLI screenshots. **V3.3 is local and uncommitted as reported.** Current verified saved fallback is **V3.2** on `feature/strategy` at `cfab27c26222423b46b7293c6416785c7115369e`. No claim that V3.3 was pushed or is on the tournament `main`.

**Design change:** Preserve V3.2's protection against value-heavy ranges, but identify repeat aggressive behavior across *multiple prior hands* (preflop and postflop) before loosening first-bet calls or allowing a minimum value raise with top pair/overpair at moderate stack-to-pot ratios. Keep conservative behavior without sufficient prior observations; reraises remain under V3.2 safeguards. Preflop policy unchanged; river change narrowly reweights the range against a first bet.

**Testing reported:** **32 unit tests**, all four official validator scenarios, and **800 completed local matches** (V3.2 and V3.3 each: five opponents × 40 matches on development seeds 1–20 and five opponents × 40 matches on holdout seeds 21–40, swapping both seats). No reported errors, timeouts or restarts. These results are from practice opponents, not the tournament field.

| Opponent | Blind format | Dev V3.2 → V3.3 wins / 40 | Unseen V3.2 → V3.3 wins / 40 |
|---|---|---:|---:|
| Caller | Rising | 40 → 40 | 40 → 40 |
| Aggressive | Rising | 31 → 32 | 31 → 32 |
| Tight | Rising | 33 → 33 | 27 → 27 |
| Mixed | Rising | 24 → 24 | 26 → 26 |
| Floorfix | Flat 50/100 | 34 → 34 | 30 → 30 |
| **Total per 200** | Mixed formats | **162 → 163** | **154 → 155** |
| **Combined per 400** | Mixed formats | **316 → 318** |  |

**Interpretation:** V3.3 wins 318/400 (79.5%) vs V3.2 316/400 (79.0%) across development plus holdout samples—only **2 additional wins overall**. This is a modest observed gain, **not conclusive evidence of superiority**. The holdout seeds were separate from development seeds, but repeated use of the same five test opponents limits generalizability.

**Decision timings (local runner only):**
- Dev: V3.2 p95 / max **3.746 / 31.459 ms**; V3.3 **3.757 / 25.352 ms**.
- Holdout: V3.2 **3.729 / 29.661 ms**; V3.3 **3.746 / 28.639 ms**.
- Both well under the stated 2,000 ms deadline locally; official restricted **0.5 CPU core / 768 MB** sandbox execution remains a separate release gate.

**Behavioral evidence and regressions:**
- Aggressive: replay of identical river decisions found **21 new calls** (15 profitable, 6 losing) worth **+67,237 chips relative to folding** on those decisions.
- Aggressive flop/turn stack-off losses increased **64,696 → 68,788 chips** across both benchmark sets, despite the additional two match wins.
- Floorfix: two extra losing terminal river calls on holdout seeds, costing **2,117 chips relative to folding**; match win totals unchanged.
- Caller, Tight, Mixed: reported win totals, stack-off losses and river-call results unchanged on both seed sets.
- Seed 4 / seat 0 / hand 1 versus Aggressive still suffers the earlier no-history passive-line issue; the V3.3 behavior remains conservative before evidence accumulates.

**Provisional decision:** V3.3 is a *freeze candidate* because it modestly improves aggressive-opponent results without an observed win-rate regression elsewhere. Preserve committed V3.2 as the known-good fallback. **Do not commit, merge, push, begin V3.4, or authorize further strategy development until the human reviews and approves**. Prioritize shared AI handoff coordination next, per user instruction. Final release requires real sandbox validation and human approval to promote the selected bot to public `main` before **6:30 PM ET**.

## Version 3.4 free-river value-betting review — November 21, 2026

**Source:** User-shared Codex CLI screenshots, local WSL Python 3.10.22, not independently rerun in this review. **V3.3 and V3.4 remain local/uncommitted** at report time; Codex reports V3.3 preserved as a local snapshot and patch, while the last confirmed pushed bot checkpoint remains **V3.2 `cfab27c26222423b46b7293c6416785c7115369e`**. No change to public `main` in this work.

**Change:** When UO-Monte can check for free on the river, V3.4 compares checking with bets of approximately **32%** and **70% of pot**, using public betting history, plausible worse callers, board texture, effective stacks, and risk of a check-raise. Other street logic and V3.3's river facing-bet defense reportedly remain unchanged.

**Validation reported:** V3.3 passed **32 unit tests** and the official validator prior to its local snapshot; V3.4 passed **37 unit tests** and all **4 official validator scenarios**. Codex reports **800 match runs** in the V3.3–V3.4 comparison (400 per version), with 20 seeds × two seat assignments × five opponents for each of development seeds 1–20 and fresh holdout seeds 41–60; zero errors/timeouts/restarts. Label the Floorfix results separately because it uses fixed 50/100 blinds; others used rising blinds.

| Opponent | Blinds | Dev seeds 1–20 V3.3 → V3.4 / 40 | Fresh holdout 41–60 V3.3 → V3.4 / 40 |
|---|---|---:|---:|
| Caller | Rising | 40 → 40 | 40 → 40 |
| Aggressive | Rising | 32 → 33 | 28 → 27 |
| Tight | Rising | 33 → 33 | 30 → 30 |
| Mixed | Rising | 24 → 26 | 27 → 29 |
| Floorfix | Flat 50/100 | 34 → 33 | 32 → 32 |
| **Total per 200** | Mixed format | **163 → 165** | **157 → 158** |
| **Combined per 400** | Mixed format | **320 → 323** | |

**Interpretation:** V3.4 recorded **323/400 (80.75%)** wins versus **320/400 (80%)** for V3.3 on these two seed blocks. The +3 match improvement is small, the practice opponents are reused, and this is *not* proof of superior tournament strength. Combined per-opponent differences: Caller 0, Aggressive 0 (development +1, holdout −1), Tight 0, Mixed +4, Floorfix −1. With Caller excluded, totals are V3.3 **240/320** vs V3.4 **243/320**, still a small observed gain.

**River economics/trade-offs reported:**
- In-position river value bets decreased **1,005 → 836**. Gross realized chips above checking back decreased **473,756 → 440,457** (−33,299), even though mean per bet increased **471 → 527** chips; the lower gross return could reflect different opportunity frequencies and downstream decisions, so do not interpret it alone as net EV.
- Check-raise losses relative to checking back decreased **13,004 → 7,884 chips** combined (about **39.4%**), comprising development **11,375 → 5,841** and holdout **1,629 → 2,043** (a regression on the holdout block).
- Gross losses in all-in showdowns decreased **965,133 → 921,045 chips**, though these are gross showdown-loss sums rather than matched-hand total returns.
- Against Floorfix, V3.4 earned **33,366 fewer chips** relative to checking back across both sets, consistent with missing some thin value.

**Decision timing (local runner):**
- Development V3.3 p95/max **3.783/21.040 ms** → V3.4 **2.919/20.667 ms**.
- Fresh holdout V3.3 **3.765/25.720 ms** → V3.4 **2.909/18.694 ms**.
- Free-river p95 reportedly below **0.61 ms** in both sets. Real 0.5-core/768-MB Docker sandbox limits remain untested as a separate release gate.

**Coordinator decision:** *provisionally retain V3.4 as a release candidate to compare in the true restricted sandbox and independent paired-seat scoring harness*, but do not discard V3.3 or committed V3.2. A small win gain and one holdout check-raise regression do not justify claiming proven dominance. No new strategy version should start before release risk is addressed and the human approves Git write operations. Crucially, the public `main` still holds the template bot as of this review; it must receive a validated, human-approved candidate before the **6:30 PM ET** deadline.


## V3.3 / V3.4 reconstructed checkpoints, local readiness, and qualification pairing — November 21, 2026

**Source:** Team-supplied Codex CLI screenshot of the local readiness report, timestamp approximately 13:26 ET. **Neither V3.3 nor V3.4 was committed, staged or pushed** according to the report: `feature/strategy` remains at **V3.2 `cfab27c`**, with V3.4 bot and tests in the local working tree. Codex independently reconstructed V3.3 and V3.4 from V3.2 and also reconstructed V3.4 by applying sequential patches; bot and test snapshots matched byte for byte.

**Reconstruction and validation:** The reconstructed V3.3 suite passed **32 tests**; V3.4 passed **37 tests**. The current V3.4 also passed all **four official validator scenarios**. Two chronological Git checkpoints are prepared but **need human approval** before any commit or push.

**Local runtime readiness:** Official local match runner completed **72 freezeouts** with **5,949 UO-Monte decisions**, covering standard rising blinds, antes, **198 decisions with stacks at eight big blinds or less**, and forced blind all-ins. The report states **zero errors, timeouts or restarts**. The import audit found only `bisect`, `itertools`, `random` and `eval7`. Local decision latency p95 **2.836 ms**, max **4.369 ms**, both below the **2,000 ms** action limit in the tested environment.

**Unresolved sandbox risk:** `make sandbox` stopped with **exit 127** because Docker was unavailable in the local WSL environment. Official restricted **0.5 CPU, 768 MB RAM, read-only filesystem and network isolation remain untested**. Local runtime and static validator do **not** substitute for sandbox verification.

**Duplicate-pair qualification testing:** The reported rule scores two swapped-seat matches as one pair: two wins = pair win; 1–1 split = pair draw; two losses = pair loss. Codex verified swapped hole cards and identical board prefixes on **1,051 shared hands** from **24 new local pairings**, reporting **V3.4 17 pair wins, 5 draws, 2 losses**. Re-scoring the earlier development and holdout practice matches, including fixed-blind Floorfix, reportedly gives **V3.3: 124 wins, 72 draws, 4 losses** and **V3.4: 128 wins, 67 draws, 5 losses** across 200 pairs. V3.4's improvement in pair wins is offset by one extra pair loss; the sample is not enough to prove a meaningful advantage.

**Release assessment:** Codex prefers V3.4 **conditional on an official Docker smoke run**. V3.3 is the next fallback only after a verified chronological checkpoint; V3.2 (`cfab27c`) is the current *committed* fallback. **Public `main` still holds the original starter bot**, so a human-approved tested release must be promoted there before **6:30 PM ET November 21, 2026**, independent of whether Docker can be installed locally.

## V3.3 and V3.4 Git checkpoints verified — November 21, 2026

**Source:** Confirmed directly via GitHub after the teammate authorized Codex's checkpoint push.

- **V3.2 fallback:** `cfab27c26222423b46b7293c6416785c7115369e` on `feature/strategy`.
- **V3.3:** `8fe259052f13bc4a096be132b57cea1c6473a7dd`, parent V3.2; message `Checkpoint UO-Monte V3.3 adaptive aggression`.
- **V3.4:** `a5ea561ff5b70d5a17533579bfc6557b2979622b`, parent V3.3; message `Checkpoint UO-Monte V3.4 river value betting`.
- **Verified remote tip:** `origin/feature/strategy` points to V3.4. Both commits change only `my_bots/uo_monte/bot.py` and `tests/test_uo_monte_bot.py`.
- **Submission:** Public `main` still contains the original template bot, not V3.4. Strategy branch commits alone are **not a tournament submission**.
- **Independent verification limit:** GitHub confirms branch ancestry and file changes; the 32/37 unit tests, official validator, freezeouts and benchmark metrics were reported by Codex and have not been rerun through GitHub.

## Multi-agent development — Claude TASK-CLAUDE-002 benchmark harness (November 21, 2026)

**Status:** Claude/Alwaleed reports local completion of TASK-CLAUDE-002 on `alwaleed/exploit-and-testing` but **not yet committed or pushed**. The primary teammate uploaded `paired_eval.py`, its `README.md`, `test_paired_eval.py`, example match/pair CSVs, example manifest, and example summary for independent coordinator review. These artifacts are **not yet claimed to exist on GitHub**.

**What Claude built (development/testing only, no UO-Monte strategy edits):**
- `benchmarks/paired_eval.py`: runs each seed in both seat orders using official `play.py`; records raw match outcomes, duplicate-pair W/D/L, per-seat results, timeouts/errors/restarts, command provenance, core and bot fingerprints, deterministic results digest, and uncertainty estimates.
- `tests/test_paired_eval.py`: pair-seat mapping, scoring, incomplete/error cases, deterministic output, seed guard, statistics and a real-match smoke test.
- `benchmarks/README.md`: commands, scoring convention, output formats, Docker instructions and limitations.
- **Sealed seeds 1001–1200 blocked by default**, with an explicit override reserved for the human-approved final evaluation.

**Claude-reported verification:** 25/25 self-tests on its own machine and sandbox; seeds 41–43 of Caller versus Template, two seats each, produced **six completed matches, three duplicate pair losses for Caller, zero reported errors/timeouts/restarts**. This is a harness sanity test, **not evidence that UO-Monte is stronger**. The same deterministic result digest was reported on both machines: `aec473398f4afab7a569d8bcda43d4d659ddda19f0a311bd26059ceca10cc034`.

**Independent source inspection and limited local replay:** The uploaded sample `matches.csv` produced the same deterministic SHA-256 digest; after parsing `seed` and `a_seat` as integers, its three pair losses and published `pairs.csv` agree with the example manifest. The isolated Python test suite ran **25 tests with 24 passing and one live match skipped** because `play.py` was unavailable here. This does **not** independently confirm the six live matches or Docker behavior.

**Review findings for TASK-CLAUDE-003:** 
1. Rescoring archived CSV rows without converting the `a_seat` column from string to integer can silently overwrite a pair's seat entry and output the wrong result. Add a typed CSV loader and regression test.
2. A nonzero `play.py` process exit should be explicitly recorded as a problem or incomplete even if a `match_end` event happened to be written.
3. The claim that Wilson match-rate intervals are necessarily conservative under paired seats is unsupported; pair-cluster inference (bootstrap at seed/pair level) is preferable. The tool's 0.5 draw weighting is correctly labelled a **team summary convention**, not confirmed tournament ranking policy.

**Division of labor:** Codex continues **V3.5 selective semi-bluffs and fold equity** on `feature/strategy`; Claude's next assignment is separate benchmark quality and independent practice opponents. The two AIs coordinate by reading `main/HANDOFF.md` and exchanging reports through the humans. Neither agent may merge to `main` or publish code without human authorization.

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
