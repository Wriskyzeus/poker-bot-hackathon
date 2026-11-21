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
- **V3.3 adaptive aggression:** Codex CLI has been given a focused task; *work/results remain unverified here until the teammate reports back*. Do not assume V3.3 is ready, saved or tested.

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

V3.2 passed **29 unit tests** and the official validator at its saved checkpoint. Local benchmark errors/timeouts were reported as zero. This is evidence for development prioritization, **not a guarantee of tournament strength**. Full logs and version-by-version notes: `docs/testing.md` on `main`.

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

**Objective:** Determine what valuable, non-overlapping tasks Claude can perform to strengthen UO-Monte and improve the reliability of our evaluation while Codex finishes its current V3.3 task.

**Instructions:**
1. Read `origin/main:AGENTS.md`, this `HANDOFF.md`, `docs/testing.md`, and the latest **committed** `feature/strategy/my_bots/uo_monte/bot.py`. Do not treat possible local uncommitted V3.3 work as settled.
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

## Status
- [x] `AGENTS.md`, `CLAUDE.md`, `HANDOFF.md` reviewed and published to shared `main` as docs-only coordination.
- [x] V3.2 verified pushed to `feature/strategy` at `cfab27c`.
- [ ] V3.3 result and commit status awaiting primary teammate's Codex report.
- [ ] TASK-CLAUDE-001 report awaiting Alwaleed/Claude.
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
