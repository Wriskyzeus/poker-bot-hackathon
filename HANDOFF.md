# HANDOFF.md — UO-Monte

**Single shared coordination file, maintained on `main`.** Last coordinator review: November 21, 2026.
**Read the latest `origin/main:HANDOFF.md` at the start of every assignment.** This file carries task instructions, status, integration contracts, and unanswered questions. It is *not* permission to execute Git write operations.

## Authority and collaboration
- **Human leads:** The two teammates approve major decisions, changes to project scope, agent code integration, and all commits/pushes/merges/releases.
- **Technical coordination:** ChatGPT reviews recommendations, tracks results and assigns bounded tasks in this shared file. It does not override human approvals.
- **Claude (Alwaleed):** Independent QA/research and, only after approval, benchmark infrastructure and opponent-tracker prototypes on `alwaleed/exploit-and-testing`. **No core bot edits.**
- **Codex CLI (primary teammate):** Owns the core bot, integration, regression tests and full local benchmarks on `feature/strategy`. **Only one agent should change the core bot at a time.**
- Claude and ChatGPT do not automatically converse: each reads latest `main` from GitHub; Claude reports findings to Alwaleed; the human forwards those findings or posts a human-approved update for coordinator review.

## Current branches and safe checkpoints
- `main`: public submission branch. **The final validated strategy has not yet been promoted to main.** Shared documentation updates here are NOT a final submission.
- `feature/strategy`: last verified committed bot **V3.2** at `cfab27c26222423b46b7293c6416785c7115369e` (`my_bots/uo_monte/bot.py`, `tests/test_uo_monte_bot.py`). Earlier baselines **V3.1** `c12396e` and **V2** `ef760ca` remain in history.
- `alwaleed/exploit-and-testing`: partner's independent branch; its shared notes were incorporated into `main` for coordination. Do not merge it wholesale or overwrite teammate work.
- **V3.3 adaptive aggression:** tested locally, **32 unit tests** and official validator passed; currently uncommitted, with Codex reporting a local snapshot/patch. 
- **V3.4 free-river value bets:** committed and pushed as `a5ea561` on `feature/strategy`; baseline for subsequent work.
- **V3.5 fold equity:** Codex reports **43 passing unit tests**, official validator, and 800 standard-opponent matches with identical decisions and **310/400 wins** for both V3.4 and V3.5 on new seeds 61–100. Against an artificial overfolder, V3.5 made 18 extra bets and induced 15 folds but did not gain match wins. **Local uncommitted experimental patch; not adopted.**

## Recent benchmark evidence
Local matched-seed comparisons, 20 seeds × two starting seats per opponent (40 matches per version per opponent). Floorfix used **fixed 50/100 blinds**, and the custom opponents used **rising blinds**; the benchmark pool is not a representation of the true finalist field.

| Opponent | V2 wins / 40 | V3.1 wins / 40 | V3.2 wins / 40 |
|---|---:|---:|---:|
| Caller | 40 | 40 | 40 |
| Aggressive | 37 | 34 | 31 |
| Tight | 22 | 26 | 33 |
| Mixed | 20 | 22 | 24 |
| Fullhouse Floorfix | 23 | 26 | 34 |
| **Total / 200** | **142** | **148** | **162** |

V3.2 passed **29 unit tests** and the official validator at its saved checkpoint. V3.3 subsequently passed **32 tests** and the official validator locally. Across two 200-match blocks with development and unseen seeds, V3.3 recorded **318/400 wins** vs **316/400** for V3.2, with only the Aggressive opponent improving (by one match in each block). All other wins were unchanged. That small gain does **not** prove superiority. Full logs and version-by-version notes: `docs/testing.md` on `main`.

## Ownership
| Area | Owner | Working branch |
|---|---|---|
| Core `my_bots/uo_monte/bot.py`: policies, equity, legal actions, final integration | Primary teammate / Codex CLI | `feature/strategy` |
| Testing audit, test harness, test opponents, tracker proposals | Alwaleed / Claude | `alwaleed/exploit-and-testing` |
| Shared project decisions and documentation task queue | ChatGPT coordinator, subject to human approval | `main`, documentation only |
| Tournament submission and release authorization | Human teammates | Public `main` after tests |

## Verified interfaces in committed V3.2
These reflect the current *committed* `feature/strategy` bot, not proposed code:
- `decide(game_state: dict) -> dict`: engine contract. Returns `{"action":"fold"|"check"|"call"|"all_in"}` or `{"action":"raise","amount":total_street_bet}`.
- `_hand_features(cards)`: six-tuple `(score, pair, suited, connected, high, low)`; score is a heuristic preflop bucket, not equity.
- `_respond(action, state)`: translates intended policy action or total-street raise target into legal response.
- `_preflop(state)`: existing preflop policy.
- `_opponent_history(state)`: small preflop adjustment `-3`, `0`, or `+2` from observed preflop actions.
- `estimate_equity(hole_cards, community_cards, simulations=320, seed=0) -> float`: bounded Monte Carlo showdown equity versus a *uniformly random* hand, with ties counting 0.5; requires 3–5 community cards.
- `_river_aggression(state, opponent)`, `_river_range_equity(state)`, `_river_defense(state)`: existing V3.1 range-aware river behavior.
- `_stack_commitment(state, owed, pot)`: V3.2 flop/turn stack-commitment and raising response.
- `_postflop(state)`: postflop dispatcher; called by `decide`.

**Do not add a competing `_equity` or independently overwrite these functions.** Any proposed opponent stats interface must be backward compatible until Codex reviews and integrates it.

## Task queue — ChatGPT technical coordination

### TASK-CLAUDE-001 — Independent opponent-model / benchmark QA audit
**Assigned to:** Alwaleed's Claude. **Status:** Ready to read. **Permission:** READ-ONLY; no file edits, commits, pushes, merges or branch changes without human approval. Do not start parallel editing with Codex.

**Objective:** Determine what valuable, non-overlapping tasks Claude can perform to strengthen UO-Monte and improve the reliability of our evaluation. V3.3 has now been tested locally and is awaiting human release decision; **do not begin new strategy development**.

**Instructions:**
1. Read `origin/main:AGENTS.md`, this `HANDOFF.md`, `docs/testing.md`, and the latest **committed** `feature/strategy/my_bots/uo_monte/bot.py`. V3.3 has been reported tested locally but remains uncommitted; treat committed V3.2 as the stable reference.
2. Audit the methodology of paired-seed / seat-swap benchmarks. Identify evaluation gaps: sample size, seed reuse, independence, opponent strength, fixed versus rising blinds, failure logging, or decision-time measurement. Recommend a concise **holdout test plan** that has not already been used to tune V3.
3. Review only permitted public game-state interfaces (`action_log`, `match_action_log`, showdown information legally revealed). Propose robust opponent statistics with correct denominators (opportunities), sample sizes, street distinctions, and shrinkage for sparse data. Flag misleading measures such as action frequencies where a player had no opportunity to act.
4. Review interactions with existing `_opponent_history`, `_river_aggression`, `_river_range_equity`, `_stack_commitment` and current `estimate_equity`. Recommend an **optional, additive** proposed tracker API, e.g. `_opponent_stats(state: dict) -> dict`; an exploit adjustment may be proposed but must not replace existing logic without tests.
5. Identify three highest-value *independent* tasks Claude could own after approval (for example more diverse test opponents, holdout benchmark harness validation, or preflop statistical tests), explicitly avoiding core bot edits.
6. Report **specific findings, proposed signatures, test cases, risks and recommendation priorities** to Alwaleed in plain English. Do not claim that any new code or validation has been run if it has not.

**Required report format:**
- Current files/commits reviewed
- Top three findings with examples
- Proposed interfaces (not implemented)
- Test/benchmark plan including unseen seeds and both seats
- Scope-separated future task proposals for Claude
- Questions requiring human or coordinator approval

**No source modifications or Git writes for this task.** Partner should share Claude's report with ChatGPT for review; subsequent tasks will be assigned in this file only after human approval.

### TASK-CODEX-002 — Parallel development: V3.4 river value-betting / check-raise resilience
**Assigned to:** Primary teammate's local Codex CLI. **Status:** Authorized for *local development and testing* while Claude completes TASK-CLAUDE-001. **Git writes:** Require human approval before any commit or push. **Branch:** `feature/strategy`.

**Scope:**
1. Inspect V3.3 local changes and current Git status. Recheck 32 unit tests + official validator. Keep V3.2 (`cfab27c`) as saved fallback. Request explicit human approval for a V3.3 checkpoint commit/push to `feature/strategy`; no `main` changes.
2. Develop **V3.4** around an independent remaining leak: *river value bets when checking is free*. Review the previous Mixed opponent loss analysis (thin river value-bets and costly check-raises) and the Floorfix holdout. Add board-texture / showdown-value considerations and bet-sizing / check-back discipline without disturbing V3.3's *facing river bet*, preflop, or flop/turn defenses except where indispensable and documented. Do not hardcode to named bots/seeds.
3. Benchmark against saved V3.3 with development and unused holdout seeds, both seats, Caller/Aggressive/Tight/Mixed and Floorfix (label Floorfix's flat blinds). Inspect value-bet EV versus checking, check-raise loss, all-in volatility, errors and p95/max timing.
4. Run full unit tests and official validator. Optionally run the official Docker sandbox after confirming installation. **Do not commit/push V3.4, merge into `main`, modify `pokercore/`, or touch Claude files until the human reviews the results.**
5. Report exact file changes, V3.4 benchmark evidence and regressions. Stop at that checkpoint. If the strategy regression is worse than V3.3, recommend keeping V3.3.

**Concurrency:** Claude independently performs TASK-CLAUDE-001 as **read-only research/QA** on Alwaleed's branch, not edits to `bot.py`. The two tasks are intentionally separate. A new Claude coding assignment requires human approval after Claude's report.

### TASK-CLAUDE-001 — Report review (coordinator, November 21, 2026)
**Status: completed by Claude, reviewed by ChatGPT.** Source: human-provided four-page `TASK-CLAUDE-001-report.md.docx`, not yet published as a GitHub report file. Claude states this was a **read-only** review of committed V3.2 at `cfab27c` and main documentation at `f454b2b`; it **did not run poker matches, tests or benchmarks**, nor review local uncommitted V3.3/V3.4.

**Useful findings:**
1. **Benchmark precision/reproducibility:** V3.3's 318/400 vs V3.2's 316/400 is too small a change to support a confident ranking; unseen seeds are not unseen opponents. Local practice opponent code and `benchmarks/` results are not part of the committed repo. Improve paired-seed reporting and reproduce locally under true tournament conditions.
2. **History estimation:** preflop `_opponent_history` conflates different decision opportunities (SB limp vs BB defend vs facing 3-bet). River aggression also combines qualitatively different contexts. Use opportunity-specific denominators, minimum observations, and shrinkage; keep current core interfaces until parity-tested.
3. **Exploitation coverage:** current committed V3.2 code assumes zero fold equity when it can check; there is no explicit postflop bluff/steal policy against habitual folders. A future phase could study such opponents without blindly introducing aggression.

**Independently checked against GitHub:** `main/my_bots/uo_monte/bot.py` is still the starter bot (65 lines), while committed V3.2 on `feature/strategy` is 496 lines. `pokercore/table.py` sets `MATCH_LOG_MAX_ENTRIES = 200`. The concerns about ambiguous preflop/river statistics and only betting for value follow from V3.2 code. Claude's approximate p-values presume independent match results; our paired-seed design requires a paired analysis for formal inference. Its statement that UO-Monte *cannot possibly* win the bluffer prize is stronger than the code alone establishes.

**Proposed next Claude assignment (NOT YET AUTHORIZED):** independent, reproducible benchmark harness with pair-level scoring, unseen opponent types, seed/seat swaps, special stack/blind regimes and sandbox timing; outside `my_bots/uo_monte/`. Human approval required before writing code or Git commits/pushes on Alwaleed's branch.

**Highest-priority release issue:** public `main` still contains the starter bot, so the team must deliberately deploy a tested release there **before the 6:30 PM ET cutoff**. Codex is presently running independent V3.4 development; do not interrupt or overwrite its uncommitted files.

### TASK-CLAUDE-002 — Build reproducible paired-seat benchmark harness
**Assigned to:** Alwaleed / Claude Code. **Status:** Approved to implement and test LOCALLY on `alwaleed/exploit-and-testing`; do not commit, push, merge, or modify `main` until the human teammates approve the diff and test results. **Independent of Codex V3.4.**

**Why:** TASK-CLAUDE-001 identified that our results lack fully reproducible per-seed data, and the official tournament evaluates duplicate seated pairs. A rigorous harness can benefit any future UO-Monte version without changing its strategy.

**Scoped deliverable:** A standalone local test harness outside `my_bots/uo_monte/` and `pokercore/`, plus self-tests. Reuse existing scripts where possible rather than replacing them. For example `benchmarks/paired_eval.py` and `tests/test_paired_eval.py`; choose paths after inspecting the partner branch and report them.

**Requirements:**
1. Read current `origin/main:AGENTS.md` and `HANDOFF.md`, inspect the official `play.py` and tournament scoring documentation and local repository/branch status. Do not assume a CLI flag or score interpretation without checking the code.
2. Harness runs two specified bot folders with the same seed in both seat assignments, using official match runner for all gameplay; never access hidden cards or patch the engine.
3. Save per-seed, per-seat results in a reproducible development artifact (CSV/JSON outside the submitted bot), recording opponent, seed, blind format, initial stacks, outcome, crashes, timeouts, and timing where exposed by runner; explicitly mark fields unavailable from the runner. Log exact commands and versions/commit SHA. It is acceptable for development tools to write local files; **the submitted `bot.py` may not**.
4. Report both raw match wins and **duplicate-pair win/draw/loss** following the organizer's actual defined scoring rules. Include seat-stratified summaries, observed win rates and uncertainty bounds with documented assumptions; if qualification scoring cannot be determined from source, flag it clearly rather than inventing it.
5. Demonstrate harness on a tiny self-test / sanity run using only already available bots (e.g. `bots/caller`, `bots/template`) or another safe existing local pair. A short test on seeds 41–43 is enough to check it functions. **Do not run reserved final sealed seeds 1001–1200.** Never claim a new strategy win rate from this small sanity test.
6. Add tests for swapped-seating correctness, deterministic output formatting, incomplete/error matches, correct pair scoring, and uncertainty calculation. If Docker exists, document (not necessarily execute) how to run restricted sandbox timing. Do not install additional system software without Alwaleed's approval.
7. Provide a simple user guide: exact launch commands, output format, limitations, and why it is statistically better than reporting only a total match win rate.

**Boundaries:** Do NOT modify `my_bots/uo_monte/bot.py`, `pokercore/`, `main`, `feature/strategy`, `AGENTS.md`, or `HANDOFF.md` on your branch during this task. Do not incorporate someone else's finalist code. Do not start the opponent-tracker implementation or new opponent bots yet. Do not commit or push without your teammate Alwaleed's explicit approval. Codex owns all actual strategy changes.

**Return for review:** Modified file list; runnable commands; self-test results; example CSV/JSON; pair scoring explanation; limitations; `git status --short`. Stop and await human/coordinator review before new work. Human should send the report to ChatGPT to confirm the next assignment.

### Coordinator review — V3.4 report received
- Codex reports **V3.4 local/uncommitted**, tested with 37 unit tests and official validator; compare to V3.3's local snapshot, not merely the pushed V3.2 baseline.
- Practice benchmark: V3.4 **323/400** wins vs V3.3 **320/400** on seeds 1–20 and fresh holdout 41–60, both seats and five opponents. Gains were primarily against Mixed; check-raise losses decreased **13,004 → 7,884** combined, although holdout check-raise losses increased. River value betting became more selective, with fewer total realized chips from IP river bets.
- **No new strategy task yet.** Current priority is safeguarding the local V3.3/V3.4 artifacts and testing a chosen candidate under true restricted sandbox and duplicate-pair scoring before final promotion. Only humans can authorize commit/push/merge.
- **Release risk:** `main` still contains the starter bot. Keep that visible in all task handoffs; before 6:30 PM ET ensure a vetted UO-Monte bot is on public `main` with the correct submission identifier.

### TASK-CODEX-002 — Local readiness follow-up (received November 21, 2026)
**Status:** V3.4 tested, but neither V3.3 nor V3.4 committed/pushed. Codex reports patch-and-snapshot reconstruction of both from committed V3.2, passing **32 tests for V3.3**, **37 for V3.4** and all four official validator scenarios. Official local runner: **72 freezeouts, 5,949 decisions, zero errors/timeouts/restarts**, rising blinds/antes/198 short-stack decisions/forced blind all-ins, local p95 **2.836 ms**, maximum **4.369 ms**. **Docker unavailable (make sandbox exit 127)**, so official half-core/memory/network/read-only isolation remains unverified.

Qualification pairing: **24 fresh pairings** yielded V3.4 **17W/5D/2L**; prior development and holdout matches re-scored as **V3.3 124W/72D/4L vs V3.4 128W/67D/5L** across 200 pairs. Still not a compelling performance difference. Full context in `docs/testing.md`.

**Next release decision:** human must explicitly approve staged chronological commits/pushes for V3.3 and V3.4 to `feature/strategy`, and approval to place a known-good bot on public `main`. Do not overwrite the V3.4 uncommitted workspace or have Claude edit it. Prioritize a Docker-capable machine or alternative organizer-run sandbox verification, but don't delay deploying a tested fallback until the cutoff.

### Human authorization — V3.3/V3.4 strategy checkpoints (November 21, 2026)
**Approved by primary teammate in chat:** Codex may reconstruct **V3.3 then V3.4** sequentially from saved **V3.2 `cfab27c`**, confirm byte-for-byte match to saved local bot/test snapshots, rerun **32** and **37** unit tests respectively plus the official validator, and **commit and push only `feature/strategy`**. Scope Git staging to `my_bots/uo_monte/bot.py` and `tests/test_uo_monte_bot.py`. Do not commit the untracked benchmark directory, modify `main`, or overwrite teammate branches/coordination files. Stop if reconstruction, tests, or branch safety checks fail; report rather than force-push.

**Important:** This is approval for the two strategy-branch checkpoint commits only, **not** approval to merge or push a tournament release to `main`. Remote `feature/strategy` still points to `cfab27c` as of this entry. After the pushes complete, replace this status with the exact new commit hashes.

**Claude visibility:** Once pushed, Claude may fetch and inspect `origin/feature/strategy` read-only. Claude must not merge or replace its working branch; TASK-CLAUDE-002 remains separate.

### TASK-CODEX-003 — V3.5 selective flop/turn semi-bluffing and fold equity
**Assigned to:** Primary teammate's local Codex CLI on `feature/strategy`. **Status:** Ready for local coding and tests. **No Git commits/pushes or merges without fresh human approval.** **Claude independently owns TASK-CLAUDE-002**; don't modify or wait for its files.

**Starting checkpoint:** V3.4 was verified committed/pushed at `a5ea561ff5b70d5a17533579bfc6557b2979622b`. Parent V3.3 `8fe259052f13bc4a096be132b57cea1c6473a7dd`. `main` is still the public starter submission branch.

**Opportunity grounded in current code:** In V3.4, `_postflop(state)` still has a flop/turn free-check branch with `# No fold equity is assumed`, value-betting only at random-hand equity >=0.72. This is a useful testable improvement area. The V3.4 river-free-check value-bet policy must remain intact.

**Scope for local V3.5 prototype:**
1. Inspect current branch, working tree and tests; preserve V3.4. Implement **only** selective flop/turn betting when checking is free, including occasional principled semi-bluffs (draws + future street equity) and fold-equity exploitation when *legal public observations* indicate excess opponent folding.
2. Use **opportunity-specific** observations for fold-to-bet: count only situations where the opponent actually faced a bet and could fold, not all opponent actions. Incorporate priors/shrinkage, minimum sample sizes, caps and deterministic decisions. Fall back conservatively without sufficient evidence.
3. Compare expected profit for checking versus carefully selected bet sizes using fold probability, equity when called, future street risk and effective stack / SPR. Avoid systematic bluffs against Caller or extremely shallow stacks. Don't hardcode opponent identities or seeds; avoid overfitting to a single toy opponent.
4. Leave preflop, `_stack_commitment` facing flop/turn bets, river defense and V3.4 river value betting unchanged unless strictly required to maintain API correctness and explained in the report.
5. Add isolated regression tests for aggressive over-bluffing, a calling station, a weak opponent that overfolds, no-history fallback, legal raise sizes, short-stack behavior and determinism.
6. Run unit tests and official validator. Compare *against saved V3.4* with paired seed/seat swaps: existing Caller, Aggressive, Tight, Mixed, Floorfix; specifically label Floorfix's fixed blind setting, and use development seeds 61–80 plus a distinct holdout (e.g. 81–100), while **reserving 1001–1200** for Claude's final sealed benchmark. If constructing a new over-folder test opponent locally, segregate its development outcomes from untouched holdout results and don't include its code in UO-Monte submission.
7. Report **pair-level win/draw/loss**, raw match wins, errors/timeouts, p95/max decision time, and chips gained/lost from bets vs checks (clearly labelled as observational, not counterfactual EV). Include any regressions in Caller, Tight, Floorfix and short-stack decisions.
8. End with a recommendation: accept V3.5 only if it offers meaningful gains that survive holdout tests without material safety or performance regression. **Do not commit/push V3.5, edit `main`, `pokercore/`, the partner branch, or `HANDOFF.md`.**

**Important:** Do not use `--dangerously-bypass-approvals-and-sandbox` or disable safety controls. The time-critical release still needs a best validated bot on public `main` before **6:30 PM ET**; preserve a robust fallback and report remaining release blockers.

### TASK-CLAUDE-003 — Harden benchmark harness and create independent practice opponents
**Assigned to:** Alwaleed / Claude, on `alwaleed/exploit-and-testing`. **Status:** Authorized for LOCAL implementation and testing, after TASK-CLAUDE-002 report review. **Do not commit, push, merge, edit `main`, or touch primary teammate's strategy files without new human approval.** `feature/strategy` has committed V3.4, while Codex is developing V3.5 independently.

**Context:** The coordinator reviewed uploaded TASK-CLAUDE-002 source and results. It passes 24 isolated tests with the one real-match test skipped outside the official kit. The sample SHA-256 digest matches the manifest; the three pairing losses reproduce if CSV fields are loaded with correct types. See `main/docs/testing.md` for precise observations.

**Part A — Resolve three independent QA issues first**
1. Make the harness safely ingest its *own archived `matches.csv`* for rescoring/reproducing earlier runs; explicitly convert `seed` and `a_seat` to integers and validate paired records. Add a regression test showing that naive CSV strings lead to wrong pair counts.
2. Make a nonzero runner exit code or missing/inconsistent completed-match log visible as an incomplete/error result; do not silently count a crash as a clean match. Add tests.
3. Replace or qualify claims about Wilson match-rate intervals being **necessarily conservative** under duplicate pairing. Treat pairs (seeds) as clusters; if computing match-rate CIs, bootstrap entire pairs instead of treating all matches as independent. Clearly distinguish team's `W + 0.5D` comparison score from the organizer's final ranking rule.

**Part B — Build diverse *test-only* opponents**
1. Implement **two original, independent** practice opponents that exercise V3.5's untested weaknesses: one **overfolder** (folds too often to modest postflop pressure) and one **trap/value-heavy player** (slowplays or makes stronger raises with strong holdings). Keep each bot in a clearly labeled *benchmark-only* folder, outside `my_bots/uo_monte/`.
2. Both must use only permitted public state and legal actions; include deterministic behavior, clear tunable parameters, and explain why they are unrealistic toy archetypes rather than proxies for the real field. Do not copy another finalist's code.
3. Run validator and small paired-seat sanity checks against existing kit bots, e.g. seeds 101–103. Use the harness and produce reproducible artifacts, but **do not run the reserved final seeds 1001–1200** and do not present toy-opponent results as UO-Monte's tournament win probability.
4. Do **not** integrate with Codex's uncommitted V3.5, alter the active `bot.py`, or touch `pokercore/`. Later, after both agents' reports and human review, we can benchmark V3.5 against these opponents without editing the strategy.

**Required final report:** paths changed; unit tests and validator outputs; sample paired result; manifest/digest; how the CSV parsing, process exit, and confidence-interval issues were handled; limitations; `git status --short`; proposed integration instructions for the primary teammate. Stop before any commit/push and await approval.

### TASK-CODEX-004 — V3.6 heads-up preflop and short-stack optimization (parallel with Claude TASK-003)
**Assigned to:** Primary teammate's local Codex CLI. **Status:** Local research/implementation/testing authorized; **no Git commits/pushes/merges until human approval**. Claude continues independent QA and benchmark opponents on `alwaleed/exploit-and-testing`. No shared strategy-file edits.

**Rationale:** V3.5 changed no action in 400 standard-opponent matches and is **not** accepted as a release upgrade. Existing committed V3.4 `a5ea561ff5b70d5a17533579bfc6557b2979622b` remains the stronger proven fallback. The V3.4 `_preflop(state)` still uses broad heuristic hand scores and fixed thresholds, including the <=8 big-blind shove/fold branch; that suggests a testable leak when effective stacks, antes and 3-bet pressure vary. This is not a claim that a specific new policy is stronger.

**Safe workflow:** Do not discard V3.5's **local/uncommitted** `bot.py` and tests. Preserve exact copies and a reproducible diff outside the repo and verify byte hashes. Prefer a *separate clean temporary Git worktree* at committed V3.4 for V3.6 experiments so the V3.5 workspace remains intact; do not use `git reset --hard`, `git clean`, force-push, or merge. Confirm the local interpreter and official testing commands work there.

**Phase A — Quantify leaks before coding**
1. Audit `_preflop`, `_hand_features`, legal raise-to semantics, position/button, blinds/antes, effective stacks and opponent raise history. Identify likely mistakes or exploitable patterns from existing logged hands; distinguish documented evidence from assumptions.
2. Review short-stack push/fold and 3-bet defense for <=4BB, 4–8BB, 8–15BB, and deep-stack cases. Look at *effective* rather than just hero stack depth and the actual price when facing a raise.
3. Produce a small, explainable change hypothesis; if no credible leak is identified, return a diagnosis instead of gratuitously changing strategy.

**Phase B — Scoped V3.6 implementation (only if justified)**
1. Improve preflop choices (open/limp, raise sizing, call/3-bet, re-raise, shove/fold) where measured weaknesses exist; use poker ranges/equity/stack economics, not fragile opponent names or seed-specific logic.
2. Preserve V3.4's postflop river and stack-off policies, action legality, existing runtime limits; do not implement V3.5 semi-bluff code as an assumed improvement.
3. Add focused tests for legality, total-street raising, short-stack actions, rising blinds/antes, button order, min raises, and preflop decision regressions. Avoid restricted API/dependencies.

**Phase C — Paired benchmarking and safety**
1. Run full unit tests, all four official validator scenarios, rising-blind/ante/forced-all-in smoke matches and local latency checks.
2. Compare exact committed V3.4 vs the local V3.6 candidate on seeds **201–220 (development)** and **221–240 (holdout)**, two seats per seed, against Caller, Aggressive, Tight, Mixed, and external Floorfix (Floorfix's flat blinds must be clearly labelled). Also test short-stack-specific cases that the default freezeout might rarely generate.
3. Report both raw match wins and *paired-seat* W/D/L, per-opponent regressions, showdown losses, timeouts and p95/max timing; never claim a small observed gain proves general superiority. Do **not** use sealed seeds 1001–1200.
4. Stop and report; do **not commit or push** V3.6, update `main`, change `pokercore/`, edit partner's branch or handoff files. V3.5 remains a separately preserved experimental patch for possible later use after Claude's new opponent tests.

**Release reminder:** This remains local experimentation. Public `main` still contains the starter template; the human team must place a tested, validated bot on `main` in a controlled release prior to **6:30 PM ET** and verify the actual competition submission procedure. Restricted Docker tests remain unavailable locally.

### Coordinator review — TASK-CODEX-004 / V3.6 (November 21, 2026)
**Completed locally, awaiting human review:** V3.6 passed **43 unit tests** and all four official validator scenarios. Local WSL test report: **968 matches** with zero errors/timeouts/restarts. Compared with committed V3.4 using seeds 201–220 and holdout 221–240, V3.6 achieved **318/400 vs 316/400 raw wins**, and **123W/72D/5L vs 121W/74D/5L duplicate pairs**. Stress tests at 3.5/7.5/12BB improved **56/84 → 61/84** wins. Caveats: Aggressive holdout **29/40 → 26/40**, gross all-showdown chip losses increased, and official Docker sandbox remains untested. Full breakdown in `docs/testing.md`.

**Version status:** Committed `feature/strategy` remains **V3.4 `a5ea561`**. V3.6 is uncommitted in an *isolated worktree*, and V3.5 was preserved separately as an experiment. Do not merge/push V3.6 without new human authorization. Claude TASK-CLAUDE-003 is independently developing harness corrections and toy opponents.

### TASK-CODEX-005 — V3.6.1 regression diagnosis and evidence-based refinement
**Assigned:** Primary teammate / Codex CLI. **Status:** local analysis/experiments allowed, no commit, push, merge or changes to `main`. **Workstream:** strategy-only; Claude retains all benchmarking harness/independent opponent ownership.

1. Preserve V3.6 source/tests exactly as an isolated, reproducible snapshot + patch; preserve V3.4 `a5ea561` and V3.5 experimental patch. Verify the isolated `v36-worktree` and its Git status before working; no destructive cleaning/reset.
2. First compare V3.4 and V3.6 preflop decisions for **Aggressive holdout seeds 221–240**, showing which changed decisions correspond to lost matches and whether paired-seat results changed. Review equity/stack-price assumptions, effective stack, antes, repeated reraises, and short-stack conditions. Don't assume the exact 3 fewer match wins are a strategic regression without causal evidence.
3. Produce an explainable preflop-only V3.6.1 change **only if the diagnosis indicates a generalizable error**; do not hardcode opponent IDs, seeds, exact hand histories or test results. Preserve all V3.4 postflop logic and bot safety constraints.
4. Run tests, validator, local latency and stress suite with seeds 201–240 as regression tests. Compare **V3.4, V3.6 and V3.6.1** with seed swaps on fresh seeds **241–260 for development** and **261–280 for holdout**, with five baseline opponents and explicit Floorfix fixed blinds. Reserve **1001–1200** for final sealed testing. Track paired W/D/L, raw wins, short-stack EV proxies, stack-off severity and changes against Aggressive. Avoid interpreting small gains as proof of stronger strategy.
5. **Do not commit/push V3.6 or V3.6.1**. Return a diff, action-level root cause analysis, tests/benchmarks and a recommendation whether to retain V3.4, V3.6, or V3.6.1. Claude may later add harder independent opponents, but its branch is not to be edited or pulled into this worktree while active.
6. Do not edit `pokercore/`, public `main`, `HANDOFF.md`, partner's branch or the tournament submission. Ask the human for approval to publish any strategy version.

**Deadline gate:** Well before **6:30 PM ET**, the human teammates must put the best vetted bot into public `main` and verify the competition's required submission; do not spend the entire window tuning one toy opponent.

## Status
- [x] `AGENTS.md`, `CLAUDE.md`, `HANDOFF.md` reviewed and published to shared `main` as docs-only coordination.
- [x] V3.2 verified pushed to `feature/strategy` at `cfab27c`.
- [x] V3.3 committed and pushed at `8fe2590`, followed by V3.4 at `a5ea561` (verified remote `feature/strategy` tip). Both changed only the bot and its strategy regression tests.
- [x] V3.3 local benchmark report reviewed; subsequently committed/pushed at `8fe2590` after human approval.
- [x] TASK-CLAUDE-001 report supplied as DOCX and reviewed; findings above.
- [x] TASK-CLAUDE-002 paired-seat harness completed locally; 25 self-tests reported; 6-match sanity check; files and digest reviewed from uploaded artifacts. **Uncommitted/unpushed pending Alwaleed approval.**
- [ ] TASK-CLAUDE-003 independent harness hardening and overfolder/trapper toy opponents in progress locally; no Git writes authorized.
- [x] TASK-CODEX-002 local V3.4 readiness completed; **human approved chronological V3.3/V3.4 checkpoint commits and pushes on `feature/strategy` only; execution pending**. Docker sandbox still untested. No `main` release approval. Claude TASK-CLAUDE-002 continues independently.
- [x] TASK-CODEX-003 V3.5 local tests complete (43/43 + official validator); **310/400 vs V3.4 310/400 on standard opponents; identical decisions**. 18 extra bets / 15 immediate folds in overfolder diagnostic, but no match-win gain. Preserve local patch; no publication approval.
- [x] TASK-CODEX-004 V3.6 local comparison complete: 43 tests + validator, 318/400 vs V3.4 316/400, 61/84 vs 56/84 ante/short-stack stress, Aggressive holdout -3. **Uncommitted in isolated worktree.**
- [ ] TASK-CODEX-005 V3.6.1 regression analysis and conditional refinement assigned locally, no Git publication approval.
- [ ] Final release approved by both teammates, official sandbox validated and final `main` commit verified.

## Open questions and decisions
1. **Legacy `_opponent_history` vs new tracker:** New tracker should provide independent features and a well-tested optional adapter. No immediate replacement. Ask Codex to integrate only after approval.
2. **Monte Carlo function:** Current actual function is `estimate_equity(hole_cards, community_cards, simulations=320, seed=0)`, not planned `_equity`. Proposed tracker need not call it directly.
3. **Integration approach:** Claude proposes/tests independent functions or harnesses on its own branch, after approval; Codex alone brings approved, reviewed code into `bot.py`. Avoid simultaneous modifications.
4. **Release on `main`:** Requires explicit human approval after tests, with cutoff **6:30 PM Eastern Time, November 21, 2026**. Keep learning/explanation time near the end and freeze code before then.
5. **Open-source legality:** Organizers reportedly approve public open-source research and offline opponents but explicitly reject wholesale copying another finalist bot.

## Collaboration mechanics
- Shared source of truth is **`https://github.com/Wriskyzeus/poker-bot-hackathon/blob/main/HANDOFF.md`**.
- Claude on the partner branch can read fresh notes **without merging**: `git fetch origin` then `git show origin/main:HANDOFF.md`, and similarly for `AGENTS.md`.
- To adopt shared files into an agent's local branch, first review `git status`; sync only the three coordination files with a deliberate workflow. Never run a blind merge/pull into a working branch containing uncommitted code.
- GitHub does **not automatically notify** a Claude session when this file changes. The human must tell Claude to fetch/re-read it (or use an explicitly configured refresh workflow).
- Changes to this coordination file are normal GitHub commits. The humans have approved the initial docs-only publish to `main`; future tasks can be posted after the human approves the assignment.

## Development roadmap (provisional, updated November 21, 2026)

- **V3.5:** completed exploratory semi-bluff experiment; no observed match-win gain on standard field, preserve as local patch.
- **V3.6:** preflop/3-bet/effective-stack prototype completed locally. Promising short-stack stress gains but uncertain overall value due to Aggressive holdout regression; use TASK-CODEX-005 to investigate before acceptance.
- **V3.7:** potential integration of vetted opponent-opportunity statistics from Claude's QA after its task-003 harness/opponents are reviewed. No duplicate modeling code or unconditional integration.
- **V4:** diverse opponents, pair-level tournament scoring, Docker/sandbox if available, latency and safety validation, freeze and deploy strongest candidate to `main`.

The team intends to prioritize development rather than a lengthy presentation session, but must leave a practical release buffer and verify the exact public `main` SHA and submission form before cutoff. Documentation and a brief explanation are built into each checkpoint.
