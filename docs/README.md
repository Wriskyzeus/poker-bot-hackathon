# Documentation

A guided tour of UO-Monte's engineering work. The root [README](../README.md) is the **portfolio overview**; these pages provide implementation detail, results and historical context.

## Start here

| Read | Content | Audience |
| :-- | :-- | :-- |
| [Engineering case study](engineering-case-study.md) | Problem, design decisions, experiments, limitations and release rationale | Recruiters and engineers |
| [Current strategy](strategy.md) | What V3.4 actually does, including approximations and trade-offs | Poker/algorithm readers |
| [Architecture](architecture.md) | Public game-state interface, policy layers, constrained execution | Software engineers |
| [Tournament specification](event-spec.md) | Official runtime requirements, legal actions and submission contract | Reproducers |
| [Setup / WSL](windows-setup.md) | Windows development environment | Contributors |

## Implementation and evidence

- [Final bot](../my_bots/uo_monte/bot.py) — one self-contained submission file.
- [Bot regression tests](../tests/test_uo_monte_bot.py) — action legality, behavior and algorithmic edge cases.
- [Full experiment journal](testing.md) — comprehensive task-by-task development evidence, including rejected variants and local benchmark results. **Long archival log; start with the case study instead.**
- [Upstream provenance](upstream-provenance.md) — boundary between the organizer kit and team implementation.

## Historical project records

The files below are intentionally preserved as **development history**, not authoritative descriptions of the current released implementation. The active root [HANDOFF](../HANDOFF.md) is now a concise final-state summary.

| Archive | What it records |
| :-- | :-- |
| [Internal agent handoff archive](archive/development-handoff-2026-11-21.md) | Verbatim record of multi-agent tasks and decisions, preserved for traceability |\n| [Original starter-kit guide](official-starter-kit.md) | Official engine, sandbox, tournament and submission instructions |
| [V2 equity design brief](v2-monte-carlo.md) | Early Monte Carlo requirements and testing plan |
| [Build milestones](build-milestones.md) | Initial roadmap |
| [Opponent threat model](opponent-threat-model.md) | Adversarial assumptions and potential strategy risks |
| [External benchmarking](external-bot-benchmarking.md) | Research notes on independent opponents and measurements |
| [Open-source research](open-source-strategy-research.md) | Strategy-source and licensing considerations |
| [Hackathon checklist](hackathon-checklist.md) | Event-day planning and historical checkmarks |
| [Final-stretch notes](hackathon-final-stretch.md) | Time-sensitive development checklist, now archived |
| [Team workflow](team-workflow.md) | Development branches and human release-approval process |
| [Resources](resources.md) | Earlier research links |

> **Historical note:** Some early design briefs refer to a starter template on `main`, planned strategy features or an incomplete submission. Those statements describe earlier checkpoints. The released entry is **UO-Monte V3.4** in [`my_bots/uo_monte/bot.py`](../my_bots/uo_monte/bot.py).

## Reproduce the release checks

From the repository root with Python 3.10 dependencies installed:

```bash
make validate BOT=my_bots/uo_monte
python3 play.py my_bots/uo_monte bots/caller --seed 7
```

For the Docker smoke test, with a working Docker daemon:

```bash
make sandbox
python3 play.py my_bots/uo_monte bots/caller --docker --seed 7
```

The team previously completed the Docker smoke successfully on the release candidate. These commands describe how to **reproduce** the checks, not results from a new run.
