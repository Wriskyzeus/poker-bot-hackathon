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
- **V3.4 free-river value bets:** tested locally with **37 unit tests**, official validator, and **800 match runs** comparing V3.3 with V3.4. V3.4 scored **323/400** vs **320/400** for V3.3 (development seeds 1–20 plus fresh holdout 41–60), with a reported 39% reduction in combined check-raise losses but fewer realized in-position river value-bet chips. **Not yet committed or pushed.** V3.2 at `cfab27c` remains the known-good committed fallback.

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

## Status
- [x] `AGENTS.md`, `CLAUDE.md`, `HANDOFF.md` reviewed and published to shared `main` as docs-only coordination.
- [x] V3.2 verified pushed to `feature/strategy` at `cfab27c`.
- [x] V3.3 local benchmark report received and documented: 32 unit tests, four validator scenarios, 800 matches, 318/400 vs V3.2 316/400. **Uncommitted; no approval yet to publish.**
- [x] TASK-CLAUDE-001 report supplied as DOCX and reviewed; findings above.
- [ ] TASK-CLAUDE-002 paired-seat benchmark harness assigned; local implementation/testing authorized; Git writes require Alwaleed's approval.
- [x] TASK-CODEX-002 V3.4 local work and follow-up readiness complete: 37 tests, validator, 72 local freezeouts, 24 fresh pairings. **Uncommitted; Docker sandbox untested (Docker unavailable).** Requires human release/checkpoint approval. Claude TASK-CLAUDE-002 continues independently.
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
