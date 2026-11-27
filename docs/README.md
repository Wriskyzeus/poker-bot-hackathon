# Documentation guide

The [root README](../README.md) is the portfolio overview. This directory contains the technical details, a concise experimental index and a preserved chronological development record.

## Recommended reading order

| Page | Purpose |
| :-- | :-- |
| [Engineering case study](engineering-case-study.md) | Project goals, technical decisions, evidence and lessons |
| [Architecture](architecture.md) | API, code components, execution constraints and data flow |
| [Strategy and algorithms](strategy.md) | The actual V3.4 preflop, equity and postflop policy |
| [Experiment index](experiment-index.md) | Short, searchable summary of attempted variants and findings |
| [Tournament rules](event-spec.md) | Runtime, legal actions and submission contract |
| [WSL setup](windows-setup.md) | Reproduction instructions for Windows/Linux development |

## Validation and reproducibility

- [Submitted agent](../my_bots/uo_monte/bot.py) and [regression tests](../tests/test_uo_monte_bot.py)
- [Full testing journal](testing.md) — **long historical record**, retained for traceability rather than quick reading
- [Release checklist](hackathon-checklist.md) — recorded checks and what they establish
- [Upstream provenance](upstream-provenance.md) — team policy versus official starter kit

## Preserved project archives

These files document exploratory work, planning and decisions at the time. **They may contain outdated status statements** (for example, earlier mentions of an unsubmitted template). Refer to the main README and the case study for the released implementation.

| Historical resource | Content |
| :-- | :-- |
| [Agent coordination archive](archive/development-handoff-2026-11-21.md) | Complete preserved multi-agent handoff and tasks |
| [V2 Monte Carlo brief](v2-monte-carlo.md) | Early evaluator design goals |
| [Build milestones](build-milestones.md) | Initial roadmap |
| [Opponent threat model](opponent-threat-model.md) | Practice-opponent hypotheses and risk areas |
| [External benchmarking](external-bot-benchmarking.md) | Independent benchmarking research |
| [Strategy and licensing research](open-source-strategy-research.md) | Source audits and reuse concerns |
| [Event-day notes](hackathon-final-stretch.md) | Historical deadline planning |
| [Team workflow](team-workflow.md) | Development-branch and review practices |
| [Original organizer documentation](official-starter-kit.md) | Original kit instructions |
| [Resources](resources.md) | Earlier references |

## Reproducing a minimal verification

With Python 3.10 dependencies installed:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
make validate BOT=my_bots/uo_monte
python play.py my_bots/uo_monte bots/caller --seed 7
```

For the isolated engine run, see the [Docker instructions](../README.md#getting-started). These commands are provided for reproducibility, not evidence of a fresh test execution.
