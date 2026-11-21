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

## Version 3.5 selective semi-bluffs and fold equity — November 21, 2026

**Source:** Team-shared Codex CLI report screenshot, benchmark completed approximately 13:40 ET; numerical results have not been independently rerun here. **V3.5 remains local and uncommitted**, with both local and remote `feature/strategy` still pointing to **V3.4 `a5ea561ff5b70d5a17533579bfc6557b2979622b`**. Do not mistake the different seed-set totals for a historical regression in V3.4.

**Change:** On flop/turn when checking is free, V3.5 estimates opponent fold-to-bet frequency from observed replies to UO-Monte's own opening bets, distinguishes bet sizes, shrinks sparse observations to a conservative prior and requires sufficient samples. It compares check with approximately one-third and three-fifths pot bets, taking account of equity when called, position and effective stacks. Prior value betting, preflop, facing-bet flop/turn defense and river decisions are reported preserved.

**Validation:** Codex reports **43 unit tests** and all **four official validator scenarios passed** in Python 3.10.22. **800 standard matches** (V3.4 and V3.5 each played 400) plus **40 diagnostic matches** (20 per version) completed with zero errors/timeouts/restarts. Final sealed seeds **1001–1200 remained unused**.

| Opponent | Blinds | Development seeds 61–80 (both versions, wins / 40; pair W/D/L) | Holdout 81–100 (both versions, wins / 40; pair W/D/L) |
|---|---|---|---|
| Caller | Rising | 40; 20/0/0 | 40; 20/0/0 |
| Aggressive | Rising | 34; 14/6/0 | 31; 11/9/0 |
| Tight | Rising | 27; 9/9/2 | 31; 11/9/0 |
| Mixed | Rising | 23; 6/11/3 | 21; 4/13/3 |
| Floorfix | Flat 50/100 | 33; 13/7/0 | 30; 11/8/1 |
| **Total per 200** | Mixed formats | **157; 62/33/5** | **153; 57/39/4** |
| **Combined per 400** | Mixed formats | **310 wins, 119/72/9 pairs for each version** | |

**Critical result:** V3.5's new policy **did not trigger in any of these five standard-opponent benchmarks**. V3.4 and V3.5 produced **identical action sequences and exactly the same 310/400 wins** (77.5% team-defined pair score across 200 pairs). No evidence of strength improvement on this opponent pool. Slight added p95 latency from the new computations without benefit.

**Timing p95 / max (ms, local):**
- Development: V3.4 **3.075 / 23.903** → V3.5 **3.121 / 35.997**.
- Holdout: V3.4 **3.108 / 27.200** → V3.5 **3.152 / 24.699**.
- These are host timings; the restricted Docker sandbox is a separate release gate.

**Deliberately overfolding practice opponent (diagnostic only):** Across 20 matches per version, both bots won **18/20 matches**, representing **8 pair wins, 2 draws and zero pair losses**. Compared with V3.4, V3.5 made **18 additional flop/turn bets**, induced **15 immediate folds**, and realized **+7,333 net hand chips across those 18 hands**; however V3.5 also suffered **2,203 additional chips in all-in showdown losses**. These are observed path results and **not a matched counterfactual EV estimate**. Three immediate folds came from bets with estimated equity below 40%. The opponent was designed to overfold, so this does not establish broader tournament strength.

**Coordinator decision:** **Keep V3.4 as leading committed release candidate**. Preserve V3.5 locally as a labeled experimental patch/snapshot and tests, but **do not promote to `feature/strategy` or `main`** without new evidence on a diverse, independently tested opponent field. The next Codex direction can focus on unaddressed *preflop/short-stack* leaks, while partner Claude completes its separate benchmark-hardening and diverse practice-opponent task (TASK-CLAUDE-003). Preserve task isolation and seek human approval before any Git writes to strategy code.


## Version 3.6 preflop / effective-stack optimization — November 21, 2026

**Source:** user-shared Codex CLI screenshot; benchmark metrics and code behavior are reported by Codex, not independently replayed in this documentation update. **V3.6 remains an uncommitted, isolated Git worktree experiment**. Both local/remote `feature/strategy` remain committed V3.4 `a5ea561ff5b70d5a17533579bfc6557b2979622b`. Original V3.5 local bot/tests remain untouched; Codex reports a byte-for-byte reproducible V3.5 recovery patch.

**Diagnosis and change:** Prior holdout replay found that V3.4 missed the short-stack branch for **544 decisions**, evaluating only its own stack rather than **effective stack**. In one deal, it reraised pocket tens into fourth bets from Tight, Mixed and Floorfix, whereas V3.6 called when replayed with public action history. The V3.6 preflop-only experiment caps raises at effective stacks, includes antes/contestable chips when pricing calls, distinguishes opens versus repeated aggression, maintains position-aware opens and modifies shallow-stack sizing/shoves. V3.4 postflop policy remained unchanged. Reported savings are not proof those exact hand choices generalize to new opponents.

**Validation:** `43` unit tests and all four official validator cases passed under Python 3.10.22. Reported **968 matches** (800 comparison matches plus 168 ante/short-stack stress matches) with zero errors, timeouts or restarts. Final sealed seeds `1001–1200` unused.

| Opponent | Blinds | Dev seeds 201–220: V3.4 → V3.6 wins / 40 | Holdout seeds 221–240: V3.4 → V3.6 wins / 40 |
|---|---|---:|---:|
| Caller | Rising | 40 → 40 | 40 → 40 |
| Aggressive | Rising | 30 → 31 | 29 → 26 |
| Tight | Rising | 29 → 28 | 30 → 33 |
| Mixed | Rising | 23 → 24 | 29 → 28 |
| Floorfix | Flat 50/100 | 34 → 35 | 32 → 33 |
| **Raw wins per 200** | Mixed blind structures | **156 → 158** | **160 → 160** |
| **Duplicate pairs W/D/L per 100** | Mixed blind structures | **59/38/3 → 60/38/2** | **62/36/2 → 63/34/3** |

**Combined:** raw wins **316/400 → 318/400**. Duplicate pairs **121W/74D/5L → 123W/72D/5L** for V3.4 to V3.6 across both blocks. Marginal improvement; Aggressive **holdout regressed by three wins**, so V3.6 is *not yet an unqualified upgrade*.

**Additional short-stack/ante stress:** 168 matches, covering stacks at **3.5, 7.5 and 12 big blinds**, antes and forced blind all-ins, V3.4 won **56/84** and V3.6 **61/84**. Duplicate-pair results **17W/22D/3L → 20W/21D/1L**. Preflop all-in showdown chip losses decreased **177,783 → 89,663** (approximately **49.6%** reduction) in the standard benchmark, although the **number of losing preflop all-in showdowns rose from 70 → 91** and **gross losses across all showdowns rose 3,050,508 → 3,115,636**. These outcome measures have different denominators; don't interpret chip-loss improvements as an EV proof.

**Decision latency (local p95 / max):** development V3.4 **2.973 / 23.052 ms** → V3.6 **2.988 / 19.408 ms**; holdout **2.993 / 20.177 ms** → **3.021 / 21.414 ms**. Official restricted Docker sandbox still untested.

**Coordinator recommendation:** V3.4 remains the protected *release fallback*; V3.6 is a promising focused upgrade for shallow stacks, **pending aggressive-opponent regression analysis and independent holdout validation**, particularly against Claude's new independently designed opponents. Preserve isolated V3.6 code and the V3.5 recovery artifacts; **do not commit/push/merge** V3.6 without explicit human approval. Avoid modifying or overwriting partner branches. Public `main` must receive a human-approved tested release before **6:30 PM ET**.

## Multi-agent development — Claude TASK-CLAUDE-003 review (November 21, 2026)

**Source and provenance:** Human uploaded `TASK-003-package.zip` containing `paired_eval.py`, `README.md`, `tests/test_paired_eval.py`, `tests/test_benchmark_opponents.py`, `opponents/overfolder/bot.py`, `opponents/trapper/bot.py` and example CSV/JSON/summary artifacts. These are **local TASK-003 work, not yet committed/pushed** according to the supplied manifest (`git_status_short` contains untracked `benchmarks/` and opponent tests). TASK-002's earlier harness **was** committed to partner branch `alwaleed/exploit-and-testing` at `1bd9fa6629b50992f4861d4b061b42a8368dd570`, verified independently on GitHub.

**What Claude changed:** Hardened `benchmarks/paired_eval.py` with a typed, validated `--rescore` CSV loader, detection of nonzero process exits even when log output looks complete, and **pair-cluster bootstrap** uncertainty instead of independent-match Wilson intervals. Kept qualification pair W/D/L distinct from the team's arbitrary `W + 0.5D` comparison score. Added **two original deterministic test-only opponents** under `benchmarks/opponents/`: `overfolder` (excessively folds to medium postflop bets) and `trapper` (strong-hand slowplay/check-raise/large river betting); not submitted UO-Monte strategy files.

**Independent limited verification (uploaded files):** After placing the package into its documented repo-relative paths, I ran the provided standalone Python test scripts: **45 test cases, one skipped live-engine test**, in `test_paired_eval.py` and **17 passed** in `test_benchmark_opponents.py`, for **61 passed + 1 skipped** in total. The live-engine test could not run outside the official kit. Before arranging the files to the expected `benchmarks/` layout, direct execution from the ZIP root failed imports—this was a packaging/layout issue, not failing algorithm assertions.

**Example result verification:** Using the uploaded `example_matches.csv`, the new typed CSV loader and summary reproduced **3 completed pairs (2W/1D/0L)** and six complete matches, with **5/6 wins for overfolder against Caller**. The recalculated deterministic digest matched `example_manifest.json`: `bdd1fca3265d79b70eac58b5b65b9134612f4a53cbc6a6a8e2453f2a3d3adcf2`. These **three seeds (101–103)** are a harness/opponent sanity check, **not evidence about UO-Monte**. The manifest reports zero timeouts/errors/restarts. I have not independently rerun official `play.py`, validators or Docker due to the limited uploaded package.

**Quality and constraints:** Final sealed seeds **1001–1200** are refused by default, and the readme explicitly warns about small samples, lack of live Docker timing and unavailable p95 data. The opponent strategies are deliberately unrealistic caricatures; wider tournament claims require many opponents, matched seeds/seats, and the official restricted sandbox.

**Next phase:** Recommend Alwaleed approve pushing the reviewed TASK-003 files on `alwaleed/exploit-and-testing` (no merge into `main`), then have Claude run independent benchmark probes on the **committed V3.4** bot against both new opponents, report specific weaknesses and prepare actionable recommendations for Codex once its V3.6.1 task completes. Separate workstreams; no edits to `my_bots/uo_monte/bot.py` from Claude.


## Version 3.6.1 deep-button three-bet defense — November 21, 2026

**Report provenance:** Codex CLI screenshots supplied by human teammate; the coordinator has *not* independently rerun the 1,792 matches. **V3.6.1 remains uncommitted in the isolated strategy worktree.** Original V3.6 remains recoverable via verified snapshot/patch, and earlier V3.5 patch remains protected. Remote `feature/strategy` verified as V3.4 `a5ea561ff5b70d5a17533579bfc6557b2979622b`; no strategy commits/pushes in this task.

**Investigation:** The original Aggressive V3.6-vs-V3.4 match flips diverged at a *deep-stack button facing same-sized three-bets*. V3.6 defended **K7 offsuit** on seed 224 just below its threshold; V3.4 did not. For seeds 227/236, V3.6 called **87 offsuit** and **K5 offsuit** respectively and lost **744 / 110 chips** in those hands versus V3.4 folds. Those individual hand differences illustrate the trade-off; they do **not** establish sole causality for tournament match outcomes.

**Change:** V3.6.1 estimates opposing big blind's three-bet range from observed responses to UO-Monte button opens using a conservative sparse-data prior, discounts the equity of weak offsuit hands for postflop playability, and confines correction to deep-button defense versus three-bets. V3.6 short-stack decisions and V3.4 postflop code unchanged. Three-way raw-wins tables below are ordered **V3.4 / V3.6 / V3.6.1**. Every version tested in two seat assignments.

| Opponent | Development seeds 241–260, each out of 40 | Fresh holdout 261–280, each out of 40 |
|---|---:|---:|
| Caller (rising blinds) | 40 / 40 / 40 | 40 / 40 / 40 |
| Aggressive (rising) | 30 / 30 / 30 | **30 / 29 / 28** |
| Tight (rising) | 31 / 30 / 32 | 29 / 28 / 29 |
| Mixed (rising) | 26 / 28 / 27 | **31 / 29 / 28** |
| Floorfix (flat 50/100) | 33 / 35 / 35 | 25 / 27 / 29 |
| **Raw wins per 200** | **160 / 163 / 164** | **155 / 153 / 154** |
| **Duplicate pair W/D/L per 100** | **63/34/3 · 65/33/2 · 66/32/2** | **59/37/4 · 57/39/4 · 59/36/5** |

**Fresh combined 400 matches/version:** V3.4 **315 wins**; V3.6 **316**; V3.6.1 **318**. Aggregate duplicate pairs V3.4 **122W/71D/7L**; V3.6 **122W/72D/6L**; V3.6.1 **125W/68D/7L**. In the *fresh holdout*, V3.4 won more raw matches than V3.6 and V3.6.1. These small changes are statistically fragile; don't declare V3.6.1 superior using aggregate wins alone.

**Previously tested regression seeds 201–240:** raw wins **316 / 318 / 323** out of 400; Aggressive specifically **59 / 57 / 59** out of 80. V3.6.1 recovered seeds 227 and 236 but seed 224 remained lost. Because these seeds informed diagnosis and refinement, they are **regression/development data**, not new holdout proof.

**New-seed all-in chip metric (V3.4 / V3.6 / V3.6.1):** preflop all-in *showdown losses* **266,635 / 93,723 / 113,757** chips. Overall *gross showdown losses* **2,846,140 / 2,909,979 / 2,901,683** chips. All-in loss reduction is encouraging but conditional on which hands reach showdown; do not equate this with overall profitability.

**Separate short-stack/ante stress, 3.5/7.5/12BB + forced blind all-ins:** raw wins **48/64 / 45/64 / 45/64**; duplicate pair W/D/L **19/10/3 · 17/11/4 · 17/11/4**. V3.6 and V3.6.1 made identical decisions throughout this stress sample. In contrast to the earlier, smaller V3.6 stress run **56/84 → 61/84**, this fresh set favored V3.4; the supposed stress advantage **did not replicate**.

**Local latency p95/max in milliseconds:** development **3.441/35.161 · 3.395/29.746 · 3.408/26.670**; fresh holdout **3.372/25.666 · 3.369/30.982 · 3.353/51.792**. V3.4 passed **37 tests**, V3.6 **43**, and V3.6.1 **47**, plus official validator on all three. Codex reported **1,792 newly run matches**, zero errors/timeouts/restarts, and matched deals/warmups/snapshots/replays. Restricted Docker sandbox remains unverified. Final **sealed seeds 1001–1200 unused**.

**Decision:** **Keep committed V3.4 as release candidate.** V3.6/V3.6.1 are research artifacts, not proven upgrades; avoid overfitting to Aggressive or short-stack toy tests. New strategy work should test **postflop decision quality against more varied opponents**, perform unbiased fresh paired comparisons and evaluate overall *match wins plus chip-risk metrics*. Before final submission promote an approved version to public `main` and test organizer submission.

## Claude TASK-CLAUDE-004 — independent stress benchmark of V3.4 (November 21, 2026)

**Source and scope:** Human uploaded `TASK-004-package (1).zip`, a full local research bundle containing `REPORT.md`, `results_table.json`, `aggregate.json`, 12 sets of `matches.csv`, `pairs.csv`, `summary.txt`, `manifest.json`, analysis scripts, selected reconstructed action traces and SHA-256 digests. Tested bot is committed V3.4 `a5ea561ff5b70d5a17533579bfc6557b2979622b`; reported `bot.py` SHA-256 `e887f6a38ef936300a0c2a556863d5da61b6fc6e1dcc4b23a036ff1ec5801040`. Used a disposable runner copy, **not** the active core strategy branch. Partner TASK-004 is local research; no changes to core bot or Git publications requested.

**Independent coordinator consistency check of the uploaded package:** Parsed all 12 `matches.csv` and `pairs.csv` tables: **480 complete match rows and 240 duplicate-pair rows**, all recorded matches `status=ok`, with **zero runner-reported timeouts, errors and restarts**, and all raw-win, pair W/D/L counts exactly reproduce `results_table.json`. All 12 per-run manifest digest strings match the published `results_table.json` fields. This **checks package internal consistency**, not a fresh re-execution of all 480 engine matches or the official restricted Docker sandbox.

**Benchmark design:** 20 development seeds **301–320** and 20 holdout seeds **321–340**, **both seats**, against two independent practice opponents (`overfolder`, `trapper`) under three structures: **standard blinds, 10,000 stack**, **turbo blinds, 10,000 stack**, and **flat 100/200 blinds + 20 ante, 2,000 stack (=10BB)**. This is **12 cells × 40 matches = 480 matches**. The opponents are deliberately exaggerated and **neither bluffs**, so weaknesses versus their bets should not be generalized to normal bluffing tournament opponents. Sealed final seeds `1001–1200` remain unused.

| Structure | Opponent | Development 301–320 pair W/D/L (wins/40) | Holdout 321–340 pair W/D/L (wins/40) |
|---|---|---:|---:|
| Standard 10k | Overfolder | 16/3/1 (35) | 15/4/1 (34) |
| Standard 10k | Trapper | 18/1/1 (37) | 13/7/0 (33) |
| Turbo 10k | Overfolder | 15/5/0 (35) | 15/5/0 (35) |
| Turbo 10k | Trapper | 13/7/0 (33) | 12/8/0 (32) |
| Flat 10BB + ante | Overfolder | 10/9/1 (29) | 14/6/0 (34) |
| Flat 10BB + ante | Trapper | 13/7/0 (33) | 16/4/0 (36) |
| **Total per opponent across six blocks** | **Overfolder** | **85W / 32D / 3L, 202 wins/240 matches** | **Combined dev + holdout** |
| **Total per opponent across six blocks** | **Trapper** | **85W / 34D / 1L, 204 wins/240 matches** | **Combined dev + holdout** |

Total hand net reported **+1,272,000 chips vs Overfolder** and **+1,216,000 chips vs Trapper**; these sums span different starting stacks and are not a single comparable EV measure. Local V3.4 decision p95 reported roughly **9–10 ms**, max ~**27 ms**. Four official validator scenarios passed on the disposable V3.4 copy (Claude report); Docker/0.5CPU sandbox not tested.

**Important action-level findings (observational, not counterfactual profit estimates):**

1. **Flop/turn weak float-calls:** `no pair, no draw` calls **426** against Overfolder and **196** against Trapper; **307/426** and **144/196** later folded. Those later-folded calls spent about **141,689** and **100,136** chips respectively. Strong hypothesis: V3.4 estimates generic postflop equity against a random hand rather than a hand selected for betting; however, folding later is not automatically a mistake because some calls may realize/improve equity. The opponent's bet-range assumptions must be statistically grounded.
2. **River call-downs vs value-only strategies:** Top-pair-or-weaker calls **0 wins in 77** against Overfolder and **1 in 34** against Trapper, with net hand results **-192,909** and **-114,139** respectively. This is **against toy opponents that never bluff**, not a general instruction to over-fold. Preserve bluff-catching against actual Aggressive opponents.
3. **Facing a raise of our own value bet:** Against Trapper's **41** flop/turn/river raises, V3.4 **called 38 and folded 0**; all 41 observed Trapper raising hands were trips or stronger, and aggregate net hand result was **-46,164**. These net figures include earlier-street losses; they are not the marginal EV of any one call. Potentially useful adaptive logic: distinguish raises by a value-only opponent from raises by a bluffer, with conservative Bayesian priors and adequate showdown evidence.

**Secondary flop/turn free-check evidence:** V3.4 checked ~80% of free flop opportunities and ~89% on turn against Overfolder; an overfolder could frequently be pressured, as V3.5's selective bluff experiment showed. But V3.4 already wins ~84% against this toy, so match-win headroom is limited and cannot justify indiscriminate bluffing.

**Actionable coordination:** Codex's ongoing V3.7 task explores **no-bet-owed flop/turn betting**, which is not the same as these more important **facing-bet call-range** issues. Do not overwrite V3.7 mid-run. Carry forward the fresh hypothesis for a later bounded **opponent betting-line conditioned equity / call-raise-fold EV** prototype and new stress opponents with *genuine bluffs*, not simply fold-to-every-value-only-raiser policies. Claude TASK-005 is **separate** independent open-source solver-license and data-table feasibility research; it does not alter the bot.

**Limitations:** all three structures use only toy opponent implementations; flat test is 10BB, not sub-5BB; scripted examples are derived from offline match logs with showdown cards that the live bot must never access prematurely; no live official Docker timing; the coordinator verified aggregate consistency, not reproduction from original `play.py` logs (the uploaded ZIP has summary tables, scripts and selected action traces, not all raw per-hand match logs). No strategy code is promoted or committed by this review.

## Version 3.7 scoped flop/turn bet-sizing experiment — November 21, 2026

**Report source:** user-provided Codex CLI screenshots on completion of TASK-CODEX-006; coordinator has **not independently rerun the benchmark** or inspected the uncommitted patch. **V3.7 remains an uncommitted isolated worktree snapshot and patch; protected V3.4 `a5ea561ff5b70d5a17533579bfc6557b2979622b` remains last remote `feature/strategy` commit.** V3.5, V3.6 and V3.6.1 recovery artifacts reportedly remain intact.

**Diagnosed opportunities:** In existing V3.4 logs, **9,182 free-to-check flop/turn decisions** were counted. Among actual responses to opening bets, Caller called **697/697**, Floorfix called **507/698**, and Aggressive raised or shoved over **53/113**. These denominators are specific responses to actual bets, not inferred opportunities to respond to nonexistent bets. None establishes how much a hypothetical alternative bet would have earned.

**Implementation:** Board texture, made-hand class, effective stack, position, initiative and sampled opponent responses shaped **smaller bet sizing** for selected medium-strength pairs. No preflop, river or postflop facing-bet changes; no semibluff expansion because response evidence was insufficient. **141 of 19,892 eligible decisions changed** across **69 matches**, **all changes were smaller bets**, no additional betting events and no larger bets. Example: holdout seed 424, Floorfix, seat 1 hand 117, pocket aces on `Q♠ J♣ 2♣` flop, bet size **264 → 167**, Floorfix called with pocket threes, and V3.7 reportedly won 851 net hand chips. One observed hand does not establish the counterfactual value of the sizing change.

| Opponent | Development seeds 401–420, V3.4 → V3.7 wins/40 | Holdout seeds 421–440, V3.4 → V3.7 wins/40 |
|---|---:|---:|
| Caller (rising blinds) | 40 → 40 | 40 → 40 |
| Aggressive (rising) | 31 → 31 | 30 → 30 |
| Tight (rising) | 27 → 27 | 32 → 32 |
| Mixed (rising) | 26 → 25 | 25 → 25 |
| Floorfix (flat 50/100) | 31 → 31 | 32 → 34 |
| **Raw wins/200** | **155 → 154** | **159 → 161** |
| **Duplicate pair W/D/L / 100** | **56/43/1 → 55/44/1** | **61/37/2 → 63/35/2** |

**Combined wins/400: V3.4 314, V3.7 315**; combined duplicate pairs **117W/80D/3L → 118W/79D/3L**. Difference is narrow, concentrated in Floorfix and not sufficient evidence of a superior strategy.

**Independent opponent diagnostic:** From separately published partner branch `alwaleed/exploit-and-testing` at `421b70e`, Overfolder and Trapper passed validator and ran on fresh diagnostic seeds 441–450 (20 matches each per opponent per version; **80 matches total**). **All decisions identical**: both versions won **16/20 vs Overfolder** and **14/20 vs Trapper**. These caricature bots do not bluff, and are no guarantee of generality.

**Overall impact and safety:** Gross showdown chip losses across development + holdout **2,726,684 → 2,773,319** (more losses under V3.7). Unit tests **42 passed**, all **four official validator scenarios passed**. Across reported **880 matches** zero errors/timeouts/restarts. Local decision latency development p95/max **3.253/20.824 → 3.233/23.181 ms**; holdout **3.196/28.474 → 3.214/20.765 ms**. Restricted Docker sandbox unavailable; final sealed seeds **1001–1200 unused**.

**Coordinator decision:** Retain V3.4. Further marginal sizing rules are poor expected value for remaining hackathon time. The **higher-leverage hypothesis** from Claude TASK-004 is opponent-conditional bet defense: weak flop/turn float calls, overcalling large river value bets, and failing to recognize strong check-raises against value-heavy opponents. Future **calibrated opponent range and action-EV** work must include bluff-capable opponents and Bayesian shrinkage, not hardcoded folds to Overfolder/Trapper. Research into externally licensed CFR tables continues separately under Claude TASK-005 until rights and table applicability are confirmed. Do not edit public `main` strategy or promote any experimental version without human release authorization.

## Claude TASK-CLAUDE-005 — own-solver push/fold feasibility and licensing audit (November 21, 2026)

**Source:** Human uploaded `TASK-005-package.zip`, with seven files: `REPORT.md`, `nash_tables.json`, `short_analysis.json`, `equity_matrix.py`, `pushfold_solver.py`, `analyze_short.py`, `raise_outcome.py`. Claude reports **no UO-Monte bot code modifications or commits**, no `pokercore/` edits, and sealed seeds **1001–1200** unused. Report's V3.4 source baseline `a5ea561`.

### Result and recommendation

**NO-GO** for wholesale preflop solver-chart replacement as a large improvement. Claude's model is **heads-up SB push/fold versus BB call/fold**, not full no-limit preflop strategy with limps, min-raises, 3-bets and 4-bets. Its V3.4 mismatch figures apply **only to V3.4 jam/fold choices** (non-all-in raises omitted) against the model's Nash BB strategy. Reported approximate marginal loss ranges: **≤5BB 0.047 bb/eligible spot (578 spots, 201 disagreements)**, **5–8BB 0.014 (744 spots, 114 disagreements)**, **8–12BB 0.010 (625 spots, 65 disagreements)**, **12–15BB 0.005 (247 spots, 13 disagreements)**. Many disagreements were SB folding marginal combos where the restricted model would jam. This is **not** a measurement that replacing V3.4 with a chart yields those bb/match in the real tournament. Non-all-in raises make up a large part of V3.4's decisions and cannot be evaluated in a two-action model. Report recommends **larger potential** in opponent-range-conditioned equity and fold/call/raise EV, already underway in Codex TASK-CODEX-007 / V4. Research-only optional micro-experiment later: ≤~6BB SB push/fold lookup if spare time and separately justified.

### Independent checks actually performed on uploaded package

- `nash_tables.json` SHA-256 independently recalculated: `ab3f8721604e06d657e924b12eccec05257975af49c5b171e0625a57170b927e` (matches report prefix).
- Contains exactly **169 distinct preflop hand classes** and **18** depth/ante cells: effective stacks **3,4,5,6,7,8,10,12,15 BB × ante 0 or 0.1 BB**. Every cell has **169 jam** and **169 call** numeric probabilities, each within **[0,1]**. This validates table structure only, **not Nash accuracy**.
- Reviewed supplied `pushfold_solver.py` and `equity_matrix.py`; its intended zero-sum payoff tree and regret matching are plausible. The report claims **≤0.0095 milli-BB/hand calculated exploitability** on the internally modeled payoff matrix, but the **equity.npy**, **weights.npy**, **classes.json** and original TASK-004 **full raw match logs** were **not included** in TASK-005 ZIP. Thus the full solver/table generation, reported low model exploitability, 100k-iteration equity calculation, and replayed V3.4 EV estimates **cannot be independently reproduced from this package**. The `chirenonhive` CLI cross-check reportedly **timed out**.
- The report says the actual tournament blind schedule is unknown; **correction:** the organizers' published starter-kit lists it exactly (blinds every 20 hands, antes starting on hands 101–120). What is **not validated** is the solver's representation of the full strategy tree and chip accounting under all those transitions. Separate `flat10bb` results are **artificial stress tests**, not the entire tournament.
- Some TASK-004 hand/chip-loss figures are observational **net losses after a line**, not causal estimates of EV that a new fold/call rule could recover. Do **not** extrapolate a "two orders of magnitude" performance improvement from them.

### Independent source-license spot check

Using exact pinned upstream SHAs from the report, independently opened repository `LICENSE` files for **MIT**: `noambrown/poker_solver` `6a10442877ffc8fd28af93e16e279b9bbdd97b2a`, `cRITlamb/poker_solver` `f78f1b2bc338dd8cbb5226ecb8398bbdb3635676`, `chirenonhive/poker-solver` `6d54d3725c50d5e74c8971723a616eb52d664f3c`, and `matteo-psnt/poker-solver` `3e1bcd10ca9113f0350a3a2aa49ebd0cdacf6ce4`. `bupticybee/TexasSolver` at `00f4f16d1c11af53d3b32d04f27432616d50cdde` contains **AGPL-3.0**. `jensbaagaard/poker-practice` `LICENSE` not present at pinned `449993f78d995c77b72d0bcac418a8507dd6f783`; treat as unlicensed/unverified, no code/chart copy. License of an upstream code repository does **not** alone establish rights to every separately sourced chart or pretrained artifact; independent provenance still needed. No code or charts from upstream were put in the submitted bot. User-reported organizer permission to adapt properly licensed code is **verbal**; uncertain third-party incorporation requires direct confirmation.

**No promotion, no publication approval.** Keep V3.4 protected until V4 from Codex is reviewed on fresh, bluff-diverse holdouts. Claude TASK-CLAUDE-006 should independently create realistic bluff/value, preflop pressure, and adaptive stress opponents on its benchmark branch, testing only with public game observations; no edits to Codex's active V4 or the tournament submission.


## Version 4 opponent tracker and range-conditioned action-EV — November 21, 2026

**Source:** user-supplied Codex CLI screenshots of completed TASK-CODEX-007. This is a reported local experiment; coordinator has **not independently rerun or inspected its uncommitted code**. V4 remains uncommitted in isolated worktree and previous V3.5/V3.6/V3.6.1/V3.7 recovery artifacts remain intact. Remote `feature/strategy` is still committed V3.4 `a5ea561ff5b70d5a17533579bfc6557b2979622b`; **no release or Git publication occurred**.

**Implementation and validation:** V4 keeps cumulative **match-local** betting, raising, calling, folding-opportunity statistics beyond the official rolling **200-entry `match_action_log`**, with deduplicated completed public hands, handling truncated prefixes and resetting at warmup. It uses showdown hand evidence only once those cards are revealed and relevant board cards have been seen. On a **453-hand official-log replay** the tracker exactly matched **all 355** recorded postflop opportunity counts, per Codex. Defensive policy weights plausible opponent combos by blockers, preflop aggression, street, position, bet sizing and stack pressure, then approximates **fold/call/raise EV**, falling back to V3.4 when evidence is sparse or the modeled EV difference small. V3.4 preflop and check-is-free logic preserved.

**Matched-seat benchmark (wins/40), V3.4 → V4:**

| Opponent | Dev seeds 481–500 | Frozen holdout seeds 501–520 |
|---|---:|---:|
| Caller, rising blinds | 40 → 40 | 39 → 39 |
| Aggressive, rising | 28 → 28 | 37 → 37 |
| Tight, rising | 30 → 31 | 35 → 35 |
| Mixed, rising | 24 → 23 | 23 → 24 |
| Floorfix, flat 50/100 | 33 → 31 | 32 → 31 |
| **Raw wins/200** | **155 → 153** | **166 → 166** |
| **Duplicate pair W/D/L/100** | **57/41/2 → 56/41/3** | **68/30/2 → 68/30/2** |

**Combined** raw match wins **321/400 V3.4 vs 319/400 V4**, duplicate pair outcomes **125W/71D/4L vs 124W/71D/5L**. V4 **changed 74/8,192** defensive decisions (approximately 0.90%): **30 calls → folds**, **25 folds → calls**, **19 calls → raises**. It retained the baseline action in **3,430** low-evidence spots. The changes clustered late in the match (**1 hands 1–20; 13 hands 21–60; 60 after hand 60**). Across dev+holdout gross showdown losses increased **3,029,896 → 3,064,370 chips**. These are realized outcomes; not a direct unbiased estimate of marginal EV.

**Representative opposite raise outcomes:** On holdout seed **513** vs Mixed, V4 raised top pair **AK** and reportedly won **6,026** net chips; on seed **518** vs Floorfix, V4 raised **QJ** on **K-Q-T** and lost **5,307**, whereas V3.4 would have called. Because the candidate raise-EV calculation accounts for fold/call outcomes but incompletely models *subsequent reraises*, this is a targeted audit priority; two cases cannot establish the best general strategy.

**Independent toy diagnostics:** Overfolder and Trapper seeds **521–530**, both versions won **15/20** against Overfolder and **16/20** against Trapper, with pair-level **11W/9D/0L** as reported. Three defensive actions differed. Both toy opponents are nonbluffing; strong improvements cannot be inferred from their matching win rates.

**Runtime/integration:** Python **3.10.22**; **45 unit tests** passed and all **four official validator scenarios** passed. Codex reported **880 paired comparison matches plus 24 standalone baseline diagnostic matches**, zero errors/timeouts/restarts. Local development p95/max latency **3.001/23.699ms → 3.385/27.958ms**; holdout **3.029/23.977ms → 3.386/32.279ms**. **Official Docker restricted 0.5CPU/768MB sandbox still unavailable locally**; cannot infer sandbox compliance from laptop timing alone. Final sealed seeds **1001–1200** unused.

**Coordinator decision:** **Keep committed V3.4 as protected release candidate.** V4 showed technically sound match-local memory and legally obtained public-game observations, but its action policy **did not improve frozen holdout wins** and worsened two other metrics. Preserve V4 memory tracker and EV code as a recoverable experiment, **not** as automatically deployable bot strategy. Next priority is a narrow **counterfactual EV calibration / ablation** across V3.4, V4 and V4-with-raises-disabled, testing delayed adaptation and rejecting uncalibrated raise decisions, followed by truly independent bluff-capable opponents from Claude TASK-006. Verify competitor legality and prevent an unapproved release. At **5:30 PM ET**, prioritize approved public `main` deployment of the best validated candidate; hard cutoff reported **6:30 PM ET**.


## TASK-CODEX-008 — V4 no-extra-raises ablation and V3.4 release dry-run (November 21, 2026)

**Evidence/provenance:** user-supplied screenshot of Codex CLI completion report. Coordinator has **not independently rerun** the 1,200 matches or inspected the local source/patch. **V3.4 remains the recommended release candidate**; V4 and V4-no-extra-raises are local uncommitted worktree experiments. Protected remote strategy checkpoint `feature/strategy` is `a5ea561ff5b70d5a17533579bfc6557b2979622b`.

**Raise-EV fault analysis:** On the original V4 audit, the **74 defensive changes** included **19 calls converted to raises**. Opponents **called 14 and reraised five**; V4 called **all five reraises**, whose effective call price was missing from its raise-EV branch model (it combined all non-folds). **18 of those 19 raises** occurred against Floorfix, with only **zero–three previous comparable opponent responses** informing each decision. The offline correction models opponent fold/call/reraise separately, caps the contested pot/contestable chips and checks minimum total-street raise legality. Against Floorfix seed 495, an additional raise of **1,755** induced a reraise costing **2,916** additional chips to call; the hand eventually lost **9,882 net chips**. These are observed outcomes, not a comparison of what a counterfactual baseline call would have earned. **No new V4.1 policy was shipped**: calibration of live reraises was too sparse. Instead Codex tested an isolated V4-no-extra-raises ablation, which retains the cumulative match-local tracker and fold/call changes but disables its new call→raise overrides.

**Fresh matched-seat results (V3.4 / V4 / V4-no-extra-raises), each row wins out of 40:**

| Opponent | Development 681–700 | Frozen holdout 701–720 |
|---|---:|---:|
| Caller (rising) | 40 / 40 / 40 | 40 / 40 / 40 |
| Aggressive (rising) | 29 / 29 / 29 | 32 / 32 / 32 |
| Tight (rising) | 29 / 29 / 29 | 30 / 30 / 30 |
| Mixed (rising) | 22 / 23 / 23 | 21 / 22 / 22 |
| Floorfix (flat 50/100) | 33 / 33 / 33 | 28 / 29 / 29 |
| **Raw match wins/200** | **153 / 154 / 154** | **151 / 153 / 153** |
| **Duplicate-pair W/D/L per 100** | **56/41/3 · 56/42/2 · 56/42/2** | **56/39/5 · 57/39/4 · 57/39/4** |

**Combined 400 matches/version:** V3.4 **304**, V4 **307**, V4-no-extra-raises **307** wins; pair outcomes V3.4 **112W/80D/8L**, both V4 variants **113W/81D/6L**. **Full V4 and no-extra-raises made identical match outcomes and duplicate-pair records**, despite different actions; this is too small to show reliable strategy superiority. Cumulative gross showdown losses: **2,937,312 / 2,910,626 / 2,907,396 chips** (observed gross losses not necessarily EV). Full V4 changed **85 defensive actions** in the fresh data (**73 after hand 60**); no-extra-raises changed **63** (**51 after hand 60**), adding **zero new raises**.

**Validation:** All **1,200 matches** reported completed without errors, timeouts or restarts. Python tests: **37 V3.4**, **45 V4**, **45 V4-no-extra-raises** passing. Offline EV audit **7** passing tests. All three passed official validator. Local p95/max latency, in ms, development **2.982/32.082 · 3.395/25.225 · 3.386/25.720**; holdout **2.984/30.903 · 3.354/25.184 · 3.328/33.940**. Restricted Docker sandbox not tested (WSL lacks Docker); sealed seeds **1001–1200** unused. Newest results do not overrule older V4 poor performance; V3.4 remains the best validated fallback.

**Release dry-run, still NOT deployed:** Codex prepared a minimal patch to public `main` consisting of `my_bots/uo_monte/bot.py` plus `tests/test_uo_monte_bot.py` copied exactly from `a5ea561`. It reports 37 passing tests, official validator passed, and a **44-hand standard Caller smoke match** won without errors. The committed V3.4 tournament `bot.py` Git blob SHA is **`27acb669ee3ac35172a88293c198182b56db0f78`**. Public repo status reported public, default branch main. Exact team folder `uo_monte`. Registration form completion **unverified**. Docker unavailable, so constrained sandbox safety **not verified**. No Git strategy release or commit/push performed. **Coordinator independently checked public `main:my_bots/uo_monte/bot.py` is still the 3,055-byte organizer starter template (blob SHA `05ddd291004fac5800d9e0bcba240629c18cd5be`) at review.**

**Important release gate:** Human teammates should **explicitly authorize** promotion of verified committed V3.4 to public `main` now or before the 5:30 PM readiness gate, verify the new public blob SHA/commit, `uo_monte` identity and submission form by the 6:30 PM ET deadline. This is independent of ongoing experiments. **Do not automatically publish without human approval.** Claude TASK-006 is separately building bluff-capable adversarial practice opponents. Future experimentation should be targeted to **stronger opponent diversity** and genuinely high-leverage changes, not simply another small generic threshold shift.

## V3.4 public main baseline release — November 21, 2026

**Publication authorized by primary human teammate:** "If you want to push version 3.4 to main, do so so we can have something in main." Only the validated V3.4 strategy files were copied to public `main`, leaving `feature/strategy` and the experimental worktrees unchanged:

1. `my_bots/uo_monte/bot.py` — source commit `a5ea561ff5b70d5a17533579bfc6557b2979622b`; Git blob SHA **`27acb669ee3ac35172a88293c198182b56db0f78`**, exact match independently verified after publication. File replacement commit **`61e4fcd3b98f381ebaff8811e6557fba858d8422`**.
2. `tests/test_uo_monte_bot.py` — exact source blob SHA **`a2c33fe0279f0ba63d803d1f6533f915086889c7`**. Newly created on `main` in commit **`d2a074659f015d2349cd229777ab979699c99176`**; GitHub `main` tip independently verified to be that commit after both writes.

**GitHub verification:** repository public, default branch `main`, `main` now serves V3.4 (not the organizer starter) and tests are byte-identical to protected V3.4. `feature/strategy` SHA remains `a5ea561`. **Test provenance:** prior Codex local release dry-run reports **37 unit tests passed**, official validator passed, 44-hand Caller smoke won with no errors; the coordinator did **not** rerun tests after direct GitHub copy. The strategy contents were verified exact, so this is a publication/byte-identical verification, **not new sandbox validation**. The Docker 0.5 CPU/768 MB sandbox remains **unverified** locally.

**Form status:** Human was completing organizer's submission form with GitHub repository and strategy description; **clicking Submit and actual form acceptance are not verified by coordinator**. Confirm team name exactly `uo_monte`, public URL, form's required checkbox (the repo is public and V3.4 passed local validator), then **submit form and retain confirmation**. The official code collection uses public `main` at 6:30 PM ET; subsequent enhancements must be tested and human-approved before replacing this baseline. **No additional source changes should be made automatically**.

## Claude TASK-CLAUDE-006 — bluff-pressure adversarial benchmark (November 21, 2026)

**Report provenance:** Human supplied `TASK-006-package.zip` (unpublished local Claude QA work on partner branch `alwaleed/exploit-and-testing`). I inspected `REPORT.md`, code-generation layout, official-validator/test transcripts, analyses, manifests, match CSVs, pairs CSVs and SHA-256 manifest. These are results on original committed **V3.4 `a5ea561ff5b70d5a17533579bfc6557b2979622b`**, not on V4 or V4-no-extra-raises. No submission-bot or core-engine edits. Five benchmark-only original practice opponents: `bluffer_low`, `bluffer_mid`, `bluffer_high` (bluff levels), `pressure` (opening/3-bet/4-bet and short-stack jam pressure), `adaptive` (medium bluffer + simple public-action fold-frequency adaptation). They **share substantial underlying source code**, not five independent strategies and not actual tournament finalist bots.

**Independent uploaded-package integrity check:** All **188 SHA-256 manifest entries** match their corresponding supplied files. There are **30 completed opponent × blind structure × seed block cells**, each with **40 matches/20 same-deal seat-swapped pairs**, totaling **1,200 matches and 600 duplicate pairs**; I cross-checked rows and pair W/D/L calculations. All 1,200 CSV records have `status=ok`, exit code 0, **no reported errors, timeouts, restarts**, and both orientations represented. Tests/validator status comes from **supplied transcripts**, not a fresh local run with the official engine: five opponent validators reported passed; `tests/test_adversary_opponents.py` **20 tests** and repo suite **111 tests** reportedly passed. Reported timing V3.4 max **56.5ms**, opponents max **8.2ms** in local Python 3.10.20; official 0.5CPU Docker sandbox still not tested. The uploaded ZIP excludes raw per-hand event logs (~150MB), so I have not independently replayed every hand-action trace or the reported conditional poker analyses; manifest integrity is not proof of the engine's actual execution.

**Primary official-format structure: standard rising blinds, seeds 601–620 (development) and 621–640 (nominal holdout), both seats.** Overall V3.4 raw wins **74/200 dev**, **87/200 holdout**, totaling **161/400**. Pair results **6W/62D/32L dev** and **13W/61D/26L holdout** (combined **19W/123D/58L**). Key breakdown across both blocks:

| Opponent | V3.4 wins out of 80 standard matches | Duplicate pairs W/D/L out of 40 |
|---|---:|---:|
| bluffer_low | 34 | 4/26/10 |
| bluffer_mid | 35 | 5/25/10 |
| bluffer_high | 30 | 2/26/12 |
| **pressure** | **29** | **4/21/15** |
| adaptive | 33 | 4/25/11 |

**Extra stress structures:** 10BB initial stack, flat **100/200 blinds + 20 ante**, dev **18W/63D/19L** and holdout **20W/70D/10L** across five opponents; **turbo blinds**, dev **12W/55D/33L** and holdout **17W/60D/23L**. Performance is markedly better in flat 10BB stress than under standard increasing blinds. However, nonstandard blind options are diagnostics, not tournament proxies.

**Important holdout contamination:** Claude originally generated a weaker-v1 opponent set, inspected its `621–640` holdout results, then recalibrated the bluff gates and reran with v2. Thus 621–640 are **lightly contaminated development data**, not pristine acceptance tests for V5. Use truly fresh **641–660** or other unused seeds for independent confirmation. Actual air-bluff share of observed river bets remains only about **4% low, 10% mid, 13% high** (reported sample). This is a deliberately simplified, often value-heavy field; the report's "neutral strength" label should not be interpreted as tournament-representative.

### Reported action-level leak hypotheses — check before implementation

1. **Flop float-and-fold:** V3.4 reportedly calls about **90% of medium** and **97% of small** flop bets in these matchups, then folds after a flop call on **54–57%** of hands against bluffers. Reported total net losses on hands that included a flop call are substantial, but **a later fold or gross chip loss does not prove the earlier call was −EV**; compare ranges, price, future barrel probability, position, actual hand equity and credible counterfactuals. V3.4's `_stack_commitment` appears a high-impact inspection target.
2. **Positional preflop defense:** V3.4 reportedly folds **56% of BB responses to 2.2BB opens** from `pressure` (defends 44%) and **62%** of SB opens facing its 3-bet. The committed `_preflop` indeed uses scalar score cutoffs and one generic raise-response bucket. The report's asserted **~73% minimum defense against 2.2BB opens is not a correct universal MDF**: e.g., if SB has posted 0.5BB and raises to 2.2BB, it risks **1.7BB additional** to win 1.5BB pre-existing pot; a zero-equity bluff would need folds ~53.1%, corresponding to a simplified MDF ~**46.9%**, before equity/position/rake/other assumptions. Actual optimal BB defense **cannot** be chosen from an MDF alone. Likewise report's "67% vs 3× 3-bet" is not a generic fact without a specified action tree and pot. **Do not hardcode artificial minimum defend frequencies or force broad calls**. Research hand-specific + position-specific pot odds/equity realization and identify which calls are +EV.
3. **River opponent conditioning:** V3.4 reportedly folds about **74%** of medium and **82–88%** of overbet river bets. Hindsight analysis of *actual complete river deals* suggests calls vs `bluffer_high` overbets would have won **45.6%** vs pot-odds **36.1%** (n=79), while calls against value-only `pressure` would have won **6%** vs ~27% break-even. This is an opponent-specific retrospective observation, **not a legal live clairvoyant classifier**, and small samples + showdown selection matter. Future live model can use only public actions and revealed past showdowns. Avoid blanket over-calling.
4. **Short-stack:** Report alleges **53 missed call-jam opportunities** against `pressure` when TASK-005 restricted self-generated push/fold tables indicate a call, at ~**0.94BB** model EV opportunity each. That solver model omitted non-all-in trees and has incomplete independent verification, so treat as **diagnostic oracle only**, not definitive Nash truth or deployment authority. Normal tournament blind ramps, 3–15BB, antes and actual effective stacks should be evaluated together.
5. **Timing:** Reported V3.4 net +0.04BB/hand early (0–39) vs some opponents but −0.2–0.3BB/hand around hands 40–99, when rising blinds matter. Match survivors and conditions create selection bias, so stratified analysis is required before causal claims.

**Strategic decision:** This is the first strong evidence that existing practice Caller/Tight/Mixed bots may be misleading about **V3.4's vulnerability to competent positional-pressure and sustained barrel strategies**. A higher-impact, staged experiment from committed V3.4 is justified. **Codex TASK-CODEX-009** should implement testable **preflop BB/3-bet defense** and **flop/turn continuation/float discipline** as separate ablations, then only combine if each improves fresh and opponent-diverse results. Claude TASK-CLAUDE-007 should independently harden the new opponents, check MDF/math and produce **new, genuinely distinct** QA threats and fresh paired holdouts. Any release remains gated by legal actions/imports, official validator, fresh results, and explicit human approval. Keep released public `main` V3.4 unchanged. No sharing of opponent hidden cards or match log hindsight inside the live bot.


## Claude TASK-CLAUDE-007 — independent new-range opponent QA (November 21, 2026)

**Source and integrity:** Human uploaded `TASK-007-package.zip` (~140KB, 125 archive entries / 101 files). I read `pkg/REPORT.md`, source `opponents/rangebot/bot.py`, original tests/scripts, 16 per-cell result directories, summary/math files, the embedded TASK-006 patch and captured validation transcripts. I **independently verified 100/100 SHA-256 entries** in `pkg/SHA256SUMS.txt` against the actual supplied ZIP members (the report and checksum list themselves are not self-hashed). Recomputed groupings, winner outcomes, seat swaps, duplicate-pair W/D/L for **640/640 CSV match records and 320/320 paired seeds**; **all match rows `status=ok`, `exit_code=0` and zero errors/timeouts/restarts**. This is package/internal consistency verification, **not** independent replay of the official tournament engine. The package's raw per-hand logs were intentionally omitted. The supplied validator transcript reports `make validate` passed for rangebot; dedicated rangebot tests **9** and full repo suite **120** passing. These reported test runs have **not been rerun locally** due unavailable engine dependencies. Rangebot source is an original-looking independent style, `eval7` equity-vs-estimated-range simulator with mixed preflop sizes, 3bets/4bets, short-stack shoves and postflop bluff/value pressure. The differing structure is supported by code inspection; true strategic independence cannot be guaranteed by a mere text comparison. No source was integrated into submission.

**New opponent stress benchmark:** `rangebot` shares no apparent implementation with the prior five TASK-006 generated bots. 16 blocks × 40 matches = **640 matches**, **320 duplicate pairs**, seeds **761–780 dev / 781–800 frozen holdout**. `V3.4` against all six opponents on standard rising blinds:

| Opponent | Dev paired W/D/L /20 | Hold paired W/D/L /20 | All 80 V3.4 wins | All 40 paired W/D/L |
|---|---:|---:|---:|---:|
| **rangebot** | 2/15/3 | 5/10/5 | **39/80** | **7/25/8** |
| **pressure** | 1/13/6 | 2/7/11 | **26/80** | **3/20/17** |
| bluffer_high | 2/13/5 | 1/11/8 | **30/80** | 3/24/13 |
| bluffer_mid | 2/13/5 | 2/10/8 | **31/80** | 4/23/13 |
| adaptive | 4/10/6 | 2/11/7 | **33/80** | 6/21/13 |
| bluffer_low | 2/14/4 | 2/14/4 | **36/80** | 4/28/8 |

Aggregates standard vs the **five TASK-006 generated bots:** **156/400** match wins, duplicate-pair **20W/116D/64L**. Across all six including independent rangebot **195/480 match wins** (40.625%). The tougher 5-opponent finding is replicated in a new seed range. `rangebot` was approximately even under standard rising blinds (V3.4 **39/80**) and harder under turbo (V3.4 **32/80**, duplicate **6W/20D/14L**); flat 10BB + ante gave **37/80**, **7W/23D/10L**. These are independent from previous seeds but practice-opponent results, **not forecast tournament win rates**.

**Major corrections to TASK-006 interpretation:**

1. **The alleged categorical preflop overfold was overstated.** Correct zero-equity bluff minimum-defense frequency for BB vs a 2.2BB SB open with no ante is **46.875%** (call price 1.2BB, required immediate equity **27.27%**, original opener adds 1.7BB to contest 1.5BB); with 0.1BB antes each, MDF **50%**. SB after opening to 2.2BB vs BB 3bet to 6.6BB, no ante, MDF **36.36%**. The TASK-006 reported ~44% BB and ~38% SB continuation vs pressure are **near** those illustrative MDFs, so a broad “fold less preflop” patch is not justified by that evidence alone. Further, MDF is not a universal optimal preflop defending frequency; range, equity realization, sizing, rake/antes and value pressure matter. The report's math audit is also reproduced in `analysis/mdf_exact.json`.
2. **Flop-call then fold evidence is a weaker causal story than thought.** On TASK-006-standard logs, Claude's retrospective analysis reports **2,360 flop calls**, hindsight equity vs actual villain hole cards **39.3%** against average immediate price **25.2%**, but naive final-stack-relative-to-before-call outcome **−1.07BB per call**, 95% bootstrap CI **[−1.80, −0.22]**. This statistic includes downstream strategy and selection effects and is **not** proof of counterfactual negative call EV or that all early calls should be removed. It warrants targeted turn-plan analysis, not blanket tighter calling.
3. **Strongest specific observed potential leak: opponent-dependent river OVERBET folding.** The uploaded `river_cf_t007.txt` uses offline villain-hole-card information after the matches (NOT legal in the live bot). V3.4 folded **106** river >0.9pot bets against `bluffer_high`; an offline hypothetical *call* would have won **42.0%** vs mean price **36.1%**, predicted average net **+6.56BB per folded spot** [bootstrap **2.0,11.6**]. Against the value-heavy `rangebot`, V3.4's **104** overbet folds would have won only **3.8%** and hypothetically calling loses about **20.58BB** per spot. Against value-heavy `pressure` the reported comparable river folds would win only ~**5.2%**. Thus **do not blanket call more**: investigate public-observable *opponent conditional* river bluff evidence, with prior shrinkage and explicit ambiguity. Hindsight outcomes are an **oracle diagnostic**, not deployable strategy, and opponent type labels are not legitimate tournament identifiers.
4. **Pressure leak likely involves passivity, not simply folding.** `pressure` now beat V3.4 on **17 of 40** duplicate pairings, V3.4 won only **3/40** (20 drawn). TASK-006 revealed V3.4 reraises about **152/2,421 = 6.3%** of `pressure` opens and rarely 4bets. This is **only a hypothesis** of exploitable 3bet/4bet passivity; the logs do not establish which individual reraises are positive-EV. V3.4 defends **~49–52%** vs rangebot 2x/2.5x/3x opens regardless of size, an additional exploitable *size blindness* against value-correlated bets. Need correct range-/size-/position-aware EV tests.
5. **Selective fold-to-reraise risk:** Report indicates V3.4 folds only **4/221 = 1.8%** facing a raise after its own postflop bet on these fresh tests. Its continuing strategy made money on average vs the sampled balanced-ish raises, but lost heavily against earlier `Trapper` value-only check-raises. Target robust selective defense without automatic folding to all raises.

**Publishing caveat / cross-team dependencies:** Claude obtained Alwaleed's permission for a **TASK-006 benchmark-only commit** on `alwaleed/exploit-and-testing` but failed to push due GitHub authentication; local commit **`8f7e61a`** and its **14-file format-patch** are supplied in ZIP as `pkg/0001-Add-TASK-CLAUDE-006-adversarial-practice-opponents-a.patch` (patch SHA-256 `ab0e94bbc2d2a7ce3251c13bf6e635e02065d0bdeb614a6acbc3058450de131b`). The public partner branch remained `421b70e` upon coordinator check. **TASK-007 source** (rangebot + tests) is **not committed or published** and needs separate partner authorization. Because source is in the upload rather than on GitHub, Codex **cannot yet fetch these opponents from the remote branch**. Partner should review and apply approved patch to his own branch, then push using authorized credentials; for TASK-007 original files, seek separate approval and scoped commit/push. Alternatively provide package via local files without repository mutation. Do not merge whole branch into V3.4 or touch `main` bot. Be mindful of `scripts/run_all.sh` **hardcoded Claude-only absolute paths**; adapt to local workspace before running. Also the TASK-006 patch may require an existing complete harness on partner branch.

**NEXT guidance for TASK-CODEX-009 / V5:** Claude's corrected priority order is (A) *conservative opponent-conditional river overbet defense* using only observable match-local histories and no hidden-card oracle, (B) *selective preflop 3bet/4bet value/semi-bluffs* / sizing sensitivity against pressure with an explicit range-risk model, (C) selective responses to value-only checkraises. Earlier hypothesis “fold less preflop” and “all flop floats are bad” is superseded. Have Codex finish its current ablations if already underway; **do not interrupt work or discard research**, but evaluate these corrections before freezing/releasing any candidate. Test vs pressure, bluffer_high and **rangebot**, plus old Caller/Aggressive/Tight/Mixed and value-only Trapper. **No V5 test has yet been performed by Claude** (frozen V5 unavailable). No official Docker sandbox proof. No performance guarantee on actual opponent field, and no release without separate human approval. Public `main` remains validated V3.4 at exact Git blob `27acb669ee3ac35172a88293c198182b56db0f78`.


## TASK-CODEX-009 — V5-P and V5-F matched-seat assessment (November 21, 2026)

**Source:** Human screenshots of Codex CLI TASK-CODEX-009 completion (worked 19m34s, timestamp roughly 15:42 EST). **Coordinator has not received or independently replayed** the underlying local match logs, patch files, SHA-256 manifest, or individual action traces. Data below faithfully reflects the screenshots; no claimed verification beyond GitHub/public bot state.

**Recommendation:** **DO NOT PROMOTE V5-P OR V5-F**. Public `main` remains byte-identical to previously validated V3.4 `a5ea561` (blob `27acb669ee3ac35172a88293c198182b56db0f78`). No Git commit, push, merge, release was performed by Codex. Previous experiments/snapshots remain preserved. No V5-PF combination or change to river policy was justified.

**Matched seat / exact-deal comparison:** Ten-opponent field, rising blinds except Floorfix (flat 50/100). Each block = **400 matches per version**, **200 duplicate seat-swapped pairs**.

| Seed block | V3.4 (wins / pair W-D-L) | V5-P (wins / pair W-D-L) | V5-F (wins / pair W-D-L) |
|---|---|---|---|
| Dev 721–740 | **250/400 · 72/106/22** | **250/400 · 71/108/21** | **248/400 · 69/110/21** |
| Frozen holdout 741–760 | **233/400 · 67/99/34** | **228/400 · 64/100/36** | **235/400 · 71/93/36** |
| **Combined 800/version** | **483/800** | **478/800** | **483/800** |

Against **established holdout** opponents only (200 matches): V3.4 **145**, V5-P **141**, V5-F **148**. Against **five TASK-006 stress opponents** (200): V3.4 **88**, V5-P **87**, V5-F **87**. V5-F gained two each vs Tight and Floorfix, lost one vs Mixed, and tied vs Aggressive and Caller; mixed results. **Caution:** Overall V5-F holdout +2 wins is far too weak and inconsistent to justify release or claim statistical superiority.

**Preflop V5-P:** Position-specific opponent ranges, pot odds, effective stack and contestable-pot calculations changed actions. TASK-006 pressure holdout: BB fold to **2.2BB open** reduced from **660/1,241** to **366/1,225**, fold vs 3bet reduced **187/300** to **157/297**, and pressure match wins **16/40 to 18/40**. Yet holdout full field fell five wins and established opponents lost four. This suggests better 2.2BB defense against one generated threat does **not** generalize; focus future investigations on **short-stack and covered-all-in price/coverage vs deep-stack indiscriminate range widening**, and selective positional reraises, not blanket lowering of fold thresholds.

**Postflop V5-F:** Re-evaluates flop/turn calls using range-conditioned equity, board texture, draws, position and future betting. TASK-006 holdout had **101 flop calls** and **164 turn calls** changed to folds; **turn-call investment reduced 764,387 → 617,869 chips**; proportion of flop-called hands ending in a later fold changed **52.2% → 52.9%** (no realized improvement in the intended causal metric). Against Aggressive one first-divergence fold saved **7,836 chips**, another cost **6,541** compared with V3.4's winning line. No demonstrated generalizable continuation improvement; more folds alone are not a goal.

**Important benchmark protocol correction:** TASK-006 generated opponents hash hand IDs, and the earlier benchmark runner embedded the **hero's version name in the hand ID**, which changed opponent actions and violated exact-match paired-deal comparison across versions. Codex **preserved the flawed original results but EXCLUDED them**, then reran both frozen variants using **V3.4's exact hand IDs**. Corrected logs reportedly passed public-state replay and matched-deal checks. Whenever reusing TASK-006 generated opponents, **require stable canonical hand identifiers independent of hero version**; same seed and seat alone are insufficient to establish equivalent stochastic opponent action paths. Candidate differences may still influence action history legitimately.

**Validation:** Python **3.10.22** with `eval7`. V5-P **42/42 tests** and V5-F **43/43 tests**, and official `make validate` passed for V3.4, both candidates and five TASK-006 opponent bots. Codex reported **2,616 valid matches**, **zero errors/timeouts/restarts**. Local p95/max decision times: V3.4 **3.405 / 56.391 ms**, V5-P **6.435 / 58.609 ms**, V5-F **5.978 / 60.113 ms**. Different parallel-worker concurrency means pooled latency isn't a strict A/B benchmark. **Docker restricted CPU/memory sandbox not tested** (unavailable). Source and tests for V5-P/F reconstructed byte for byte from patches per Codex; manifest SHA list exists locally but not yet uploaded.

**TASK-CLAUDE-007-informed follow-up:** The leading *testable* opportunity is conservative **opponent-conditional river overbet defense** using only public match actions, not oracle opponent hole cards or fixed adversary-name rules. Versus a highly bluff-heavy bot, V3.4 folded 106 overbets that an offline oracle estimated would have been profitable calls; vs value-heavy rangebot, folding comparable 104 spots was strongly correct. Identifying these cases online is hard and should be backed by calibrated observable evidence, Bayesian shrinkage and a safe default, especially if public history has only sparse villain showdowns. Second possible independent lane: **selective 3bet/4bet pressure** based on credible range/sizing/stack EV, not automatic extra aggression. Preserve previous V4 opponent tracker as research; it lost on prior holdouts and its raise-EV model mishandled reraises. Do not casually integrate it wholesale.

**Release condition:** After legal-action/validator/latency and materially diverse matched-seat improvements on frozen holdouts, human explicitly approves any publication. Keep `main` V3.4. Registration form completion remains unverified unless human confirms. Deadline **6:30 PM Eastern**. Preserve sealed seeds **1001–1200**.


## Claude release-gate audit and opponent delivery patch (November 21, 2026)

**Uploaded provenance:** Human shared `RELEASE-GATE-REPORT.md`, `release-gate-package.zip`, and `uo-monte-practice-opponents.patch` prepared by partner's Claude (report describes work as ~5 PM ET, but upload/local timing is separate; do not use timestamp as a release version identifier). Coordinator opened all three files and recomputed consistency of the supplied **180 match rows / 90 duplicated seat pairs across 12 matchup×blind groups**. All pairs have two distinct seats, W/D/L matches match their CSV winner rows, every match is `status=ok` with exit code zero and zero recorded bot errors/timeouts/restarts. This is **internal log validation, not replay of the actual tournament engine**. Supplied `validate_main.txt` indicates organizer's validator **passed 4/4** on a clean export of published V3.4; included `edge.txt` reports **20,000 randomized decision states**, zero exceptions/illegal actions/over-owed-checks/when-free-folds and max **70.8 ms**; more extreme *invalid empty state* raises ValueError, not part of normal match. The organizer's restricted 0.5CPU/768MB Docker sandbox is **still not tested**. Reported 21,284 decisions across 180 matches, max **45ms** in normal bench; coordinator has not independently recomputed decision totals from raw logs because ZIP contains summaries rather than raw action logs.

**Baseline release:** The report's `origin/main` at run time was `21a77691aaa94d2b87b7aab36517ae8fe78bda2b`; subsequent docs-only commits changed main tip, but coordinator checked the **live `main:my_bots/uo_monte/bot.py` Git blob remains `27acb669ee3ac35172a88293c198182b56db0f78`**, identical to protected V3.4 source commit `a5ea561`. Report says only bot.py (29,397 bytes) is under submission folder; imports restricted to `bisect`, `itertools`, `random`, `eval7`; prohibited behaviours not found in static audit. Human has explicitly confirmed organizer registration form **submitted** (receipt/screenshots not separately audited). **GO for keeping V3.4 as submitted baseline**, not evidence that a changed version should be pushed without fresh release checks.

**Important 801–810 seed overlap:** This gate used standard seeds **801–810** and turbo/flat10bb **801–805**. Codex TASK-CODEX-010 previously designated **801–820 dev / 821–840 frozen holdout**; the first ten dev seeds have now been used for V3.4 baseline gate and should **not be called wholly fresh or untouched**. Claude report's proposed `811–850` acceptance range would **overlap Codex's 821–840 holdout**, so it is **not an independent frozen acceptance block**. Allocate untouched **861–880** to Claude TASK-008, both seats, and preserve sealed **1001–1200**.

**Poker findings retested:** Zero-equity-bluff MDF/price interpretation corrected: versus 2.2BB SB opens, BB non-all-in defenses with >=20BB effective stack **48.2%** (fold 51.8, call42, reraise6.2; n=4,725), close to illustrative no-ante MDF **46.9%**. Preflop pressure opponent remains difficult (pooled duplicate 10W/45D/35L, but newest 801–810 **3W/4D/3L**), so cause remains unproven. Full three-block offline hole-card hindsight says V3.4's 218 river folds to >0.9pot bluffer_high overbets would win **42.9%** vs average **36%** pot price; adjusted seed-cluster CI for counterfactual mean **+3.1 to +11.2 BB**, but the same folds against all other supplied opponents would be overwhelmingly correct to fold (3–9% wins). The `bluffer_high` instance was specifically designed to exploit overbet defense; offline opponent hole cards **cannot be legal online policy features**. V3.4 nearly never folds to a raise after its own postflop bet (9/456), but measured realized continuation from decision won chips on average, so harm is *not* established. Sizing insensitivity to BB 2x vs 3x raises is a plausible risk, not an established better action.

**Opponent patch inspected:** The uploaded mbox `uo-monte-practice-opponents.patch` SHA-256 **`d7a1a54d4bda481beed69c64b18ae58ce3bd59031bfb4b7a8ffc624b5e1dbfdf`** contains **two git format-patch commits**: `8f7e61a` with **14 benchmark-only** TASK-006 source/test files (five generated adversaries, scripts, tests), and `c524e2c` with **two benchmark-only** TASK-007 files (`benchmarks/opponents/rangebot/bot.py`, `tests/test_rangebot.py`). File lists show **no `my_bots/` or `pokercore/` modifications**. The patch is a transfer mechanism—not evidence these files were pushed to GitHub. As of coordinator's direct branch check, remote `alwaleed/exploit-and-testing` remained `421b70e68d6e3c698d557fcf53359f93129d3c21`, **without published TASK-006/007 opponent files**. The local partner branch already includes first commit `8f7e61a`; **don't blindly `git am` the full two-patch mbox on it** or blindly reapply untracked rangebot files. For user transfer to Codex, pass patch and apply to a **disposable checkout based on the correct parent** with reviewed paths, or have partner publish scoped files after explicit approval. The included release gate `pkg/run_gate.sh` has absolute Claude-only paths (`/home/claude/review/repo`, `/home/claude/kit/.venv/bin/python`, `/tmp/gate/main`); adapt to independent environment before running. Do not merge partner's whole branch into tournament bot.

**TASK-CLAUDE-008 next:** time-limited handoff/publishing QA, then independent frozen acceptance of an explicitly supplied V5-R snapshot only if Codex finishes it in time. Acceptance seeds **861–880**, same deals and both seats, standard tournament blinds across genuinely different bluffer/value-heavy/rangebot/pressure and old-established bots; QA for correct stable hand IDs, rules/validator/latency, logs and per-opponent/paired W/D/L. If V5-R is not ready before 5:30 PM ET readiness freeze, do not block entry or invent a V5 result: preserve V3.4 and return baseline GO. Any new main release requires distinct human approval. User says registration form submitted.


## TASK-CODEX-010 — V5-R adaptive river-overbet experiment (November 21, 2026)

**Source:** User screenshot of final Codex CLI report; coordinator has **not independently replayed local CSV logs, patch, or standalone manifest**. Outcome: **NO-GO / keep V3.4 `a5ea561` on public `main`**. V5-R was built and preserved as a local experimental patch, no Git commit/push/merge/release. No merged prior V5-P or V5-F logic.

**Design:** Public-history-only opponent tracker (public betting opportunities, position, earlier barrels, and revealed river-overbet hands) with conservative, contestable-pot EV threshold and evidence requirement; V5-R allowed to change only `fold↔call` facing a **first river bet >0.9 pot**, never speculative raises. An unmodified `tracker-only` variant was also compared. Official history is finite and revealed showdowns rare. Codex action audit found **409 baseline overbet folds**, with **34** having any prior overbet showdown and **only three** with even one clear-air opponent reveal. **None had the minimum two required**; V5-R **changed zero decisions**. The tracker replayed opportunity counts matching independent official engine checks in all 409 spots.

**Fresh corrected exact-hand-ID matched-seat benchmark:** Ten opponents (including independent `rangebot`), standard rising blinds except flat 50/100 Floorfix. Same deals, seat swaps, and **exact canonical hand IDs** across variants. Each 20-seed block covers 400 matches per version (200 pairs).

| Block | V3.4 matches · pair W/D/L | Tracker-only | V5-R |
|---|---|---|---|
| Development **801–820** | **259/400 · 84/91/25** | **259/400 · 84/91/25** | **259/400 · 84/91/25** |
| Holdout **821–840** | **251/400 · 79/93/28** | **251/400 · 79/93/28** | **251/400 · 79/93/28** |
| Combined | **510/800** | **510/800** | **510/800** |

All three had **identical action traces and results**. No measure of performance improvement exists; the absence of regressions is explained by policy never firing.

**Offline hindsight opportunity vs live-identification limitation:** Against `bluffer_high` on holdout, V3.4's folded overbets had **41.7% true hindsight showdown equity vs average 36.0% call price**, 48 spots. Against value-heavy `rangebot`, only **3.7%** true equity vs **36.8%** price on 41 folded spots. These are **offline retrospective hidden-card oracle labels only**; neither true villain hole cards nor adversary ID nor future showdowns may be used in live strategy. The report also notes `rangebot` overbet **more often than bluffer_high on dev**, so raw overbet frequency fails to reliably distinguish bluffs vs value.

**Validation:** V5-R **43/43 unit tests** (baseline 37), official validator passed for baseline, tracker-only, V5-R and rangebot; rangebot **9** bundled tests also passed. **2,400 matches completed, zero bot errors/timeouts/restarts**. Holdout local p95/max decision time (ms) V3.4 **17.802/104.111**, tracker-only **17.837/131.040**, V5-R **18.003/112.352**; V5-R aggregate maximum **168.676ms**. Note these are host/local measurements, *not* the restricted Docker 0.5-CPU sandbox. SHA-256 manifest, reconstructable local patch, logs and commands reported available locally, not uploaded here. `main` exact V3.4 bot blob still `27acb669ee3ac35172a88293c198182b56db0f78` at coordinator check; no strategy changes.

**Strategic conclusion:** Evidenced negative/zero experiment. **Do not weaken the showdown-reliability safeguard simply to force V5-R to fire.** The primary win opportunity may instead be **targeted, appropriately priced preflop 3-bet/4-bet aggression against very wide openers**, *not* blanket looser calls as disproved in V5-P. Keep that hypothesis distinct and test conservatively versus independent rangebot/pressure/bluffers and established opponents. Avoid hardcoding particular opponent identities, importing unlicensed external charts, or assuming illustrative minimum-defense frequencies imply optimal play. Partner TASK-CLAUDE-008 is coordinating independent benchmark handoff; reserve its planned **861–880** untouched acceptance block and sealed **1001–1200**.


## Claude TASK-008 — published portable adversarial benchmark handoff (November 21, 2026)

**Uploaded artifacts:** `practice-opponents-overlay.zip` (171,478 bytes, SHA256 `0749e56e1e3cbbce2581275f26a77ba758c2804e1fd0c48949fa7a5b5d9073b1`) and `uo-monte-practice-opponents-v2 (1).patch` (317,656 bytes, SHA256 `dc2c7b412ea73353ac44dfa5fcf8d1e9a9161552e72fc86384609cf8b2949240`). Coordinator inspected **39 ZIP entries** (including directory entries), no path traversal, **21 Python source files compiled without syntax errors**, and cleanly applied the three Git format-patches in a disposable empty scratch repository. Comparing patch-created sources against the ZIP: **20/20 overlap files byte-identical**, plus six older files in ZIP from preexisting partner branch (paired harness, overfolder/trapper, README and tests); no mismatching files. Neither patch touches `my_bots/` or `pokercore/`. The overlay has `benchmarks/OPPONENTS_HANDOFF.md` plus `benchmarks/run_suite.sh` and `benchmarks/compare_candidates.py` with canonical-hand-ID control and opponent source/tests. This is **handoff/source-level verification**, not a fresh run of its unit tests or official validator. Rangebot and five adversaries remain designed practice opponents, **not tournament-strength proxies**.

**GitHub publication now verified (earlier auth problem resolved):** Remote `alwaleed/exploit-and-testing` now at commit **`6b2e7d534415fddf4da7679cbe0a68d2b8b6caf7`** (`Make practice opponents portable for cross-version benchmarks`), with earlier benchmark-only commits `d8b048c7a8130b2dacfd89f389e3914d437dfa45` (TASK-006) and `308ea7ed7b414b01f5a0455aa38391d59c0c7dd5` (TASK-007), parent of `6b2e7d`. Coordinator independently fetched GitHub blobs for `bluffer_high`, `rangebot`, `OPPONENTS_HANDOFF.md`, `run_suite.sh`, `compare_candidates.py` and associated tests, and confirmed exact Git blob hashes **match the ZIP**. This supersedes earlier 'not yet on GitHub' notes; **Codex may now fetch the benchmark-only suite from the remote**. Must use separate disposable benchmark copy/worktree and select only scoped files, NEVER merge partner's entire branch into V3.4 or published main. Public `main` tournament bot remains V3.4 and independently validated; form submission confirmed by user.

**How to use (for agent, not a user command to run blindly):** In a clean disposable test worktree based on official baseline, fetch `origin/alwaleed/exploit-and-testing` and copy only `benchmarks/` plus `tests/test_adversary_opponents.py`, `tests/test_rangebot.py` and appropriate preexisting benchmark tests/fixture; run `python3 -m unittest discover -s tests -p 'test_*.py'`, individual official validators, then `benchmarks/run_suite.sh` with frozen V3.4 and candidate bot snapshots in different directories. `compare_candidates.py` reports per-opponent wins and paired results, checks deal consistency when kept JSONL logs exist. **Limitations:** Comparison currently checks intersecting archived hands and may report zero checked deals if `KEEP_LOGS=0` or if candidate/baseline log files are missing; a zero-mismatch printout **does not itself prove matching games unless the verified deal count is nonzero and expected logs are present**. Require `KEEP_LOGS=1`, verify each seed/seat and no unexpected incomplete runs, and ensure canonical hand IDs independent of hero version. `benchmarks/task006/run_all.sh` has Claude-local absolute paths, so prefer portable `run_suite.sh`. Official Docker sandbox still unavailable in previous reports.

**Next Claude assignment:** TASK-CLAUDE-009 independent *frozen candidate* verification against newly available opponents after Codex TASK-011; until a frozen version is given and read-only publication approved, use existing 006/007 cached logs to develop a **short, reproducible audit of high-impact preflop pressure leaks** (size-aware 2x/2.2x/3x defense, selective 3bet/4bet, value-only 4bet punishment, stack/ante context). Do not run its independent untouched acceptance seeds **861–880** before freezing candidate, nor use sealed **1001–1200**. If TASK-011 shows no convincing changes, return source-level diagnostic recommendations instead of gratuitous full simulation. No automatic main code change; no Git push without explicit approval.


## TASK-CODEX-011 — V5-S size-aware and V5-A reraise experiments (November 21, 2026)

**Source:** User screenshot of Codex CLI final TASK-CODEX-011 report. Coordinator independently reviewed published V3.4 code in GitHub, but **has not inspected local V5-S/A patch files, per-hand logs or SHA-256 manifest**. Codex recommended **NO-GO for both**, preserving validated V3.4 `a5ea561` as released `main` (bot blob SHA `27acb669ee3ac35172a88293c198182b56db0f78`). No commit/push/merge/release by Codex.

**Exact matched seat/hand-ID comparison:** 10 practice opponents, standard rising blinds except Floorfix flat 50/100, 400 matches per version per block (200 paired seeds):

| Seed block | V3.4: match wins · pair W/D/L | V5-S | V5-A |
|---|---|---|---|
| Development 841–860 | **272/400 · 92/88/20** | **270/400 · 92/86/22** | **272/400 · 92/88/20** |
| Frozen holdout 901–920 | **260/400 · 92/76/32** | **258/400 · 89/80/31** | **260/400 · 92/76/32** |
| Combined | **532/800** | **528/800** | **532/800** |

V5-S changed **134 preflop calls→folds in each block**; holdout gained 1 win each vs Tight and `bluffer_high`, lost 2 each vs `rangebot` and Floorfix. The first changed hand outcome improved in 54/72 affected matches, but total net chips across those specific comparisons favored V3.4 by **841 chips**. Example: V5-S vs rangebot's Q♠8♠ fold had **9,877 fewer chips** than V3.4 realized; vs Floorfix Q♥5♠ fold saved **6,663**. These are selected realized results—not causal expected value. Holdout paired bootstrap 95% interval for match win difference **−7 to +3 wins /400**, so the small aggregate difference provides no evidence of superiority.

V5-A estimated a price for **136 potential extra 3bets** but **changed zero live actions**. No 4bet satisfied conservative evidence + stack-risk criteria. Closest situation: pressure opponent had opened **23 of 32** BTN opportunities but only **three** comparable prior reraise responses; 3bet risked **1,164 additional chips**, model EV raise **+87** vs call **+192**, so model chose call. Hence identical match actions and results; not evidence that a broadly aggressive strategy would fail, just no tested positive alteration from this proposal. Avoid relaxing evidence safeguards merely to produce action changes.

**QA:** Codex reports 37 tests passing for V3.4, 41 for V5-S and 42 for V5-A, all official validators passed. **2,490 matches** including independent turbo test, with **zero errors, timeouts or restarts**. Holdout local p95/max latency (ms): V3.4 **18.082/105.371**, V5-S **18.487/124.715**, V5-A **18.268/109.327**. Docker unavailable, so restricted 0.5-CPU/768MB sandbox still unverified. Both experiment patches reconstruct independently from V3.4 and are preserved locally, source SHA manifest verified by Codex per report, not reverified by coordinator.

**Decision and next architectural opportunity:** Released V3.4 `_preflop` currently computes a **single heuristic `_hand_features` score** followed by fixed `value_3bet` / `call_cutoff` and a small `_opponent_history` score offset. It does *not* compute action-specific equity realization or expected value for a credible opponent response distribution on most preflop decisions. Repeated minor score and size changes have not consistently improved against diverse opponents. A **bounded original range/position/stack-aware preflop policy experiment** could address this structural limitation, but must demonstrate meaningful new action changes and real paired improvements without overfitting to `pressure`. Priority: factual diagnosis of preflop money lost by line/position/stack/sizing before implementing a new 169-class preflop lookup/policy; action-specific EV and opponent response risk cannot be asserted from static equity alone. Build new candidate in separate worktree only, maintain strong safeguards, verify rule constraints and use fresh, unused matched seed blocks; do not use 861–880 reserved for Claude acceptance or sealed 1001–1200.


## Claude TASK-CLAUDE-009 Phase A — pressure leak and checked-to stab audit (November 21, 2026)

**Evidence:** User-uploaded `TASK-009-PHASE-A.md` and `TASK-009-phase-A.zip` (5 files: report, `pressure_diag.py`, `stab.py`, `diag_pressure.txt`, `stab.txt`). Coordinator inspected both scripts and read the generated output; raw original JSONL match logs from `/tmp/t006`, `/tmp/t007`, and `/tmp/gate` were **not** included in the ZIP, and were **not independently replayed** here. These were retrospective *public-action* analyses of existing logs, **not additional matches or a tested new policy**. Claude reports 123 tests and 8 opponent validators passing, stable hand IDs under hero renaming. Baseline `a5ea561` V3.4, standard rising blinds, 180 matches / 14,899 hands, net **−2,415 BB / −0.162 BB per hand**, duplicate pairs **10W/45D/35L**. Research seed blocks 601–640, 761–800, 801–810; reserve 861–880 for untouched independent acceptance and 1001–1200 sealed.

**Where chips are lost by position/effective stack:** BB 15–30BB **−0.60 BB/hand** (n=1,104), BB 30–60BB **−0.34** (n=1,852), SB 30–60BB **−0.41** (n=1,881), vs SB >60BB **+0.18** (n=3,559). Larger loss concentrations tend to fall in the middle of the match; realized whole-hand grouping is descriptive, **not action-specific causal EV**.

**Major new high-upside testable hypothesis: postflop checked-to stabs.** Among V3.4 opportunities after `pressure` checked, V3.4 bet on the **flop 22.0% (n=1,838), turn 13.6% (n=1,393), river 5.0% (n=954)**. In the **643** cases it did bet, the pressure bot subsequently **folded 641** times (**99.7%**); per-street reported flop 405/405, turn 190/190, river 46/48. V3.4 instead checked back the **first such opportunity in 1,539 hands**, average pot **6.4BB**, and realized about **+3.45BB** afterward. Claude's offline heuristic assumes a hypothetical half-pot bet would take the pot at the **observed** fold rate, while losing the entire bet when called; under that *untested stationary-response/selection* assumption, estimated counterfactual incremental advantage **+2.89BB per unchecked spot, +4,444BB total / +0.298BB per hand played**, bootstrap **+3,793 to +5,043BB**. The confidence interval describes resampling of the retrospective modeled rows and **does not account for changed opponent response frequencies, selection on V3.4's original bet hands, future strategy adaptations, or the single toy opponent's rigid checking logic**. It is not verified as an actual tournament improvement. The practice `pressure` bot's reviewed source explicitly uses `if kind == 'pressure'`: with `amount_owed>0`, most sub-pair hands **fold to >0.4pot bets**, and when unbet it usually bets with strength >= 2 but checks weaker hands (with some flop air bluffing). Thus a 0.5pot checked-to stab can exploit a structural weakness in **this synthetic opponent**, but **must not be blindly generalized**.

**Cross-opponent crucial caveat:** Same offline half-pot stab extrapolation reports, per hand, `rangebot` **−0.164BB** (opponent checked-to bet fold frequency ~51%), `bluffer_mid` **−0.121BB** (~52%), `bluffer_high` **−0.096BB** (~54%); value-heavy `Trapper` +0.119BB (~92.5%, but only 40 tested bet responses). Selected historical bet samples were made with a V3.4 value-heavy policy and are *not representative* of newly attempted bluffs. Counting actual **check→facing bet→fold opportunities by distinct prior hands** is required. Legal public signals can support an opponent-conditional, board-/equity-/position-/SPR- and street-aware exploit with conservative priors, but **average observations were only ~3.6 per match** in this baseline. New first-probe bets could be limited and controlled; no opponent-name heuristics. Include value-heavy traps, raises, check-raises, bet sizing legal semantics and early-match cold starts. Test separate ablation `V6-Stab` from exact V3.4 first, rather than immediately blending with hypothetical 169-class preflop redesign. Compare paired outcomes and *measured* first-divergence EV on genuinely fresh development and frozen holdout opponents, especially pressure vs rangebot/bluffers/Trapper.

**Secondary preflop leak:** V3.4 opens ~74% of buttons with effective >=20BB; `pressure` 3bets ~23% of opens; V3.4 folds 62% (call 35%, 4bet 3%). `open→3bet→fold` lost **−1,529BB across 694 hands**, but 62% folding is near simplified 63.6% break-even bluff threshold and is not proof of wrong response. Cautious opponent-observable high-3bet reduction in weakest opens might be preferable to forcing more 4bets (sample only 28, rejam 5). BB vs 2.2BB pressure opens: fold52/call42/3bet6 percent (n=4,812), near illustrative MDF 46.9% defense. A pure bluff 3bet faces 48% folds / 38% calls / 14% 4bets, far from 63.6% folds needed for riskless bluff; more bluff 3bets are **not** well-supported. Original preflop structural score simplification still exists, but the newly identified postflop checked-to opportunity is stronger hypothesis to **test first**, without pretending it explains the loss causally.

**TASK-CLAUDE-009 Phase B status:** Not run because Codex V5-S/A was already NO-GO and frozen candidate was not delivered to Claude; **independent seeds 861–880 remain unspent**. Partner report recommended retaining published V3.4. Continuing work is appropriate on independent audit/acceptance after Codex freezes a distinct V6-Stab candidate. No partner publication/commit/merge happened in Phase A. User confirmed form submitted; public V3.4 Git blob `27acb669ee3ac35172a88293c198182b56db0f78` remains protected.


## Claude TASK-CLAUDE-010 Phase A — replay-tested checked-to stab opportunity (November 21, 2026)

**Source/provenance:** User-uploaded `TASK-010-PHASE-A.md` and `TASK-010-package.zip`; uploaded ZIP SHA256 **`0b858720b3082c6b6be87c190bf4b3fc44e933dc155ecb3ba36577b6a6c5c516`**. Coordinator read report, `analysis/replay_probe.py`, `online_counter.py`, `check_value.py`, saved replay/QA outputs, `benchmarks/opponents/_stabtest_src.py`, rendered four opponent bots, `tests/test_stabtest_opponents.py`, `benchmarks/stab_audit.py` and four official-validator captured transcripts. The ZIP has **22 entries**, no unsafe paths or corruption, and **all 11 Python files parse**. I did **not independently re-execute full official match simulator, opponent response replay, 135 tests or 24 smoke matches** because their original raw logs, tournament environment and dependencies are not supplied. Validation logs report four opponents official validator PASSED, targeted 12 tests, whole suite 135 tests, 24 smoke matches with zero errors/timeouts/restarts.

**New finding: sample selection tested via offline opponent-response replay.** Earlier TASK-009 observed pressure folds **641/643** after V3.4 bets following checks, but original V3.4 bet only made hands (57% single pair, 43% two pair+, zero air). Claude enumerated **all 4,185 existing checked-to V3.4 opportunities** vs pressure from baseline match logs, including **3,542 check-backs**, rebuilt synthetic opponent-facing `action_request` states at proposed betting sizes and called the practice opponent's own `decide()` with *its own* hole cards. Under those replay assumptions, pressure folded to a half-pot bet **~99.9%** of the time, including **~99.9% when V3.4 held no pair**. At **0.33pot**, however, pressure folded only **73.7%** (value of bet size is critical); at 0.5/0.75/1.0pot ~99.9%. The published pressure bot source confirms a simplified pattern of checking weak hands and often folding when faced with a >0.4pot bet. This isolates the toy opponent's response to the historical public state and removes the most obvious made-hand-only selection problem, **but does not simulate the full altered multi-street game or learning/adaptation** and does not yield an observed head-to-head EV improvement.

| Opponent | Historical checked-to states replayed | Opponent fold to 0.5pot | Opponent raise to 0.5pot | Fold to 0.5pot when V3.4 held no pair |
|---|---:|---:|---:|---:|
| `pressure` | 4,185 | **99.9%** | 0% | 99.9% |
| `trapper` | 252 | 91.3% | 0% | 94.9% |
| `bluffer_mid` | 4,051 | 62.6% | 3.6% | 58.3% |
| `bluffer_high` | 4,216 | 62.1% | 5.0% | 57.0% |
| `rangebot` | 1,537 | 49.9% | 7.0% | 44.6% (raise 8.5%) |

**Crucial EV check:** Checking with unpaired flop hands in historical spots realized **39–44% of pot** for V3.4 across sampled opponents. For a half-pot bluff with worst-case full loss when called, to outperform checking's ~0.42 pot value the required fold fraction is `f > (0.42+0.5)/1.5 ≈ 61.3%`, **not** the often-quoted 33% fold-only break-even when checking is assumed worthless. Example exact QA data: vs pressure on flop no-pair **n=906, checking realized 44% pot**, required >~63%; vs rangebot **n=317, 39%**, required >~60%. Very few naturally occurring no-pair turn/river checkbacks, so those estimates are noisy and highly selected; the model assumes zero winnings after an unsuccessful bluff and ignores altered downstream lines/raise response and future opponent adjustment. Realized hand value cannot be directly interpreted as a counterfactual guarantee.

**Public-history counter:** The `match_action_log` is the last **200 public action entries** (posts/actions including folds, showdowns). QA `online_counter.py` processes previous completed hands in order and skips truncated hands to prevent double-counting; cached simulation across **120 matches** reports **2,535 checked-to spots, 435 stabs, 299 fold/124 call/12 raise replies**, **exact agreement** with same-prefix full-log counts, no truncated complete hands skipped. Important: `match_action_log` alone truncates old hands; production implementation needs match-local volatile memory (reset per match) or correctly deduplicated incremental history, never cross-match persistent files/identity. Typical V3.4 only gets ~4 comparable stab replies per match. At a true ~62% fold frequency, ≥5 of 6 folds occurs **~26%** of the time, so simplistic evidence gates will misclassify bluffers as pressure; use Beta/prior shrinkage, recent reactions, public check-raise evidence and conservative stop rules. Do **not** hardcode practice opponent names, replay their private hole cards in submitted policy or treat offline peek as legal observation.

**Four new benchmark-only adversaries (not yet published, user must authorize scoped push):** original `_stabtest_src.py` + builder renders `checkfold90` (~90% folds when checked then facing bet), `checkcall50` (~50% folds), `checktrap` (checks strong hands, value and bluff check-raises), `shifter` (switches checkfold90→checktrap after four recorded stabs). Partner report: four validators passed, 12 test cases, whole 135 tests, 24 V3.4 smoke matches zero error. Uploaded files include `benchmarks/stab_audit.py` that summarizes observed opportunities, bet-response frequencies and decision-point chip outcomes. These are simplified synthetic QA bots, not representative tournament opponents. **`alwaleed/exploit-and-testing` remote currently remains `6b2e7d5` and DOES NOT yet include these TASK-010 files**; do not claim Codex can fetch the new checkfold/checkcall/checktrap/shifter bots until human-approved benchmark-only publication or local transfer.

**Acceptance status:** **Phase B NOT RUN** because a frozen V6-Stab candidate is unavailable. Independent **861–880** remains untouched per Claude. Once human authorizes access to an exact frozen candidate, compare both starting seats and canonical matched deals vs V3.4 using standard blinds, **pressure, checkfold90, checkcall50, checktrap, shifter, rangebot, bluffer_mid/high, trapper and established opponents**, preserving JSONL and match-action diagnostics. Verify **zero match/deal mismatches on a positive number of matched hands**. Against new stabs, demand robust gains vs exploitable checkfolders and no meaningful losses vs adaptive/trapping/value-heavy + general opponents; no rigid '1 match lost = fail' without sample-aware paired uncertainty. Stop if cold-start probes or check-raise losses erase benefits. Preserve sealed 1001–1200. Public `main` still has exact V3.4 Git blob `27acb669ee3ac35172a88293c198182b56db0f78`; user confirmed registration form submitted. Actual deadline **6:30 PM ET**.


## TASK-CLAUDE-010 benchmark-only opponent publication (November 21, 2026)

**Completed:** User forwarded `uo-monte-stabtest-opponents.patch`. Coordinator read the exact mbox, safely applied it in an empty disposable Git repository and parsed **8/8 Python files** successfully; source patch SHA256 **`aed4e8451fc5cb7655a8661ea5cb758dac9066656e33b65436ee99754af44651`**. The patch contains one commit adding eight **benchmark-only** files (4 opponents, original generator/builder, unit test and stab audit); **no `my_bots/` or `pokercore/` changes**. GitHub's `alwaleed/exploit-and-testing` branch was independently verified to have advanced to **`e766d680f5ad6d0b9350ced201e559b2a78eec66`** (`Add TASK-CLAUDE-010 stab-regression opponents and audit tool (benchmark-only)`). Exact Git blobs of `checkfold90`, `checkcall50`, `checktrap`, `shifter`, `tests/test_stabtest_opponents.py`, `benchmarks/stab_audit.py` **match the patched file blobs**, demonstrating that the published files match delivered source. Unlike an earlier status note, the files **are NOW fetchable from GitHub**. No new runtime unit tests or official validator run by the coordinator this turn; prior partner report asserts four validators passed and full test suite passed.

**Portable use:** On a **new disposable benchmark-only worktree**, fetch pinned `origin/alwaleed/exploit-and-testing` branch and run appropriate unit/validator cases; do not execute `git checkout origin/alwaleed/exploit-and-testing -- benchmarks ...` blindly in Codex's active strategy worktree, since it may overwrite experimental files. Human need not apply patch or run emailed Git commands manually. Codex can incorporate this new independent QA suite into frozen candidate matched-seat testing after its ongoing TASK-012 work, without modifying tournament code. Partner TASK-010 Phase B remains **NOT RUN** and requires an exact frozen V6-Stab source snapshot and human consent; reserve untouched **861–880** until then and sealed **1001–1200**. Public `main` still holds protected V3.4. Registration form was submitted per human.


## TASK-CODEX-012 — V6-P and V6-Stab completed, no release (November 21, 2026)

**Source provenance:** user screenshot of Codex CLI completion report (GPT-6.2 Astra Extra High, worked 18m30s after earlier limit interruptions). Coordinator **did not receive local patches or complete match logs** to rerun; all figures are as reported by Codex and require source-level verification before any deployment. **Release decision: KEEP V3.4** `a5ea561`; public main bot verified still blob SHA `27acb669ee3ac35172a88293c198182b56db0f78`. No experiment commit/push/merge/release. Registration form submitted according to the user.

**V6-Stab adaptive checked-to opponent-exploitation experiment:** Ten standard practice opponents, development seeds **1201–1220**: V3.4 **255/400** wins, V6-Stab **255/400**. Frozen holdout **1221–1240**: V3.4 **253/400**, V6-Stab **257/400**. Separate four new Claude QA adversaries: development V3.4 **72/160** vs V6-Stab **79/160**; holdout V3.4 **96/160** vs V6-Stab **95/160**. Pressure folded to **172/172** added bets where V3.4 would have checked. Paired same-deal bet-vs-check replay estimated actual *new-bet chip* gains **+212.92 BB on dev** and **+270.53 BB holdout**, averaging **+0.027 and +0.068 BB per hand** on those benchmark samples. However complete tournament matches vs Pressure failed to translate to consistent wins (**30/80 each version**) and rangebot wins **decreased 34/80→31/80**; Mixed improved **44/80→48/80**. **Exploration cost flagged:** Among ten standard opponents, **620/672** additional bets were exploratory and **52** followed established evidence (50 against pressure). The new `checktrap` bot raised **27/71** extra bets, and **54 added holdout bets vs adaptive `shifter` happened before first change of mode**, leaving adaptation after shift unverified. This is a genuinely different code policy with some promising chip effects, **but not a convincing generalizing freezeout-win improvement**; do not promote on +4/400 alone or on an opponent-specific fold exploit.

**V6-P 169-class preflop policy experiment (separate seeds/bench):** Ten standard opponents, dev V3.4 **271/400** vs candidate **269/400**, holdout V3.4 **242/400** vs candidate **245/400**. Changed **944 preflop decisions**. Pressure holdout tied V3.4, Mixed lost two matches per block. Isolated 8BB ante stress **worsened from 48/80 to 44/80 wins**; increased preflop all-in showdown losses **102→136** on holdout. Not an accepted replacement.

**Validation:** V3.4 **37** tests, V6-P **43**, V6-Stab **45**, all official validator passed. Four new QA opponents passed their validator and partner's **135-test** suite as reported. **4,000** comparison and stress matches zero reported errors/timeouts/restarts. V6-Stab reported single-hand p95 **14.184 ms**, max **99.752 ms** under local 2,000ms, but restricted 0.5CPU/768MB Docker still unavailable. Both candidate worktrees/patches and SHA manifests locally recoverable. Reserved independent Claude acceptance seeds **861–880**, sealed **1001–1200** unused per report.

**Current coordination:** User expressed frustration at excessive costly Astra Extra High usage for negative large experiments and wants wrapping up rather than endless tasks. Do **not** assign unnecessary new long projects to partner. Any optional final experimental refinement should be **short/stop-early** and focus solely on reducing costly V6-Stab exploratory bets while maintaining positive responses to observed check-fold behavior, only if low-compute diagnostic shows evidence; use narrower early-stage matched-seat trials and stop immediately if no real change/win benefit. Do not assume this will outperform V3.4. The safe tournament submission already on public `main` is valid according to prior validation; no new strategy publication without explicit user approval, source hash verification and official validator before 6:30 PM ET.


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
