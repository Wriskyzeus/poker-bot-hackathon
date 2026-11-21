# UO-Monte — Final Project Status

**Release:** V3.4 · **Event:** IEEE uOttawa × LARUS Poker Bot Hackathon, November 21, 2026 · **Submission:** [`my_bots/uo_monte/bot.py`](my_bots/uo_monte/bot.py)

> This file is a short **final-state handoff**. The complete development task queue, test notes and prior instructions have been preserved **verbatim** in the [historical agent-handoff archive](docs/archive/development-handoff-2026-11-21.md). Archived tasks are **not active**.

## Final release state

| Item | Final recorded status |
| :-- | :-- |
| Selected strategy | **UO-Monte V3.4** |
| Protected strategy checkpoint | `a5ea561ff5b70d5a17533579bfc6557b2979622b` |
| Released `bot.py` blob | `27acb669ee3ac35172a88293c198182b56db0f78` |
| GitHub | Public repository, default branch `main` |
| Submission identifier | `uo_monte` |
| Registration form | Submitted, as confirmed by the team |
| Official Python validator | **Passed** |
| V3.4 release regression tests | **37 passed** |
| Docker sandbox | **Built and successfully smoke-tested** — 46-hand win against the reference Caller; approximately 2 ms average decision time |
| Tournament placement | **Not recorded in the development evidence**; do not infer it |

**Release decision:** No V4–V6 experiment or final rare short-stack price correction established enough consistent improvement to replace V3.4. The match results favored preserving the validated candidate. The tournament bot and organizer-provided engine remained unchanged during final portfolio documentation edits.

## Developer orientation

- [Project README](README.md): recruiter-facing overview, architecture and quick start
- [Engineering case study](docs/engineering-case-study.md): strategy, methods, results and trade-offs
- [Current strategy](docs/strategy.md): released V3.4 decision logic
- [Architecture](docs/architecture.md): actual components and API
- [Full evaluation journal](docs/testing.md): detailed experiment results and caveats
- [Complete historical task handoff](docs/archive/development-handoff-2026-11-21.md): original chronological agent notes and prompts
- [Organizer starter kit](docs/official-starter-kit.md): authoritative API and sandbox requirements

## Source control and provenance

The official competition submission is **only** `my_bots/uo_monte/`. Do not confuse benchmark opponents, local worktrees, partner experiments, internal docs or archive material with the deployed bot.

The starter engine, `pokercore/`, templates and sandbox are organizer-provided, licensed under the repository's [MIT notice](LICENSE). UO-Monte's final policy is team-authored and AI-assisted during development; **no live LLM inference** occurs during play.

## Working on a future version

Keep V3.4 as an immutable comparison baseline. Develop new ideas in a separate branch or worktree, using properly licensed sources and the organizer's legal-action and runtime rules. Compare **identical deals and swapped seats**, preserve genuine holdout seeds, and don't merge policy changes to `main` without explicit human review and validation.

The November 21 tournament workstream is **closed**; no prior archived tasks should be resumed merely because they appear in the historical handoff.
