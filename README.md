# UO-Monte — IEEE uOttawa × LARUS Poker Bot

Two-person Python poker-bot project for the November 21, 2026 hackathon.

**Game:** heads-up No-Limit Texas Hold'em, freezeout matches, rising blinds and antes. **Runtime:** Python 3.10; 2 seconds per decision, 768 MB RAM, 0.5 CPU core. **Competition:** duplicate-seated qualification pairings followed by a top-four heads-up knockout.

## Start here

This repo incorporates the [official organizer starter kit](https://github.com/FreddyyAndrews/poker-hackathon-kit): actual tournament engine (`pokercore/`), bot template (`bots/template/`), reference caller (`bots/caller/`), runner (`play.py`), validator, and pinned dependencies. **Don't edit `pokercore/`.**

Our team is **UO-Monte**. For the official submission, enter the exact identifier **`uo_monte`** as the team name, matching our entry at **`my_bots/uo_monte/bot.py`** (the rules require lowercase letters, digits and underscores). The submitted entry contains **UO-Monte V3.4**, our final tested rule-based and simulation-assisted poker strategy—not the starter template. The official submission folder is `my_bots/uo_monte/`; only the team's bot is collected.

### Run locally — Windows

The organizers recommend **WSL Ubuntu**; commands below are for a Linux shell, not PowerShell. Install `git`, `make`, `build-essential` and the [uv Python manager](https://docs.astral.sh/uv/) if needed.

```bash
git clone https://github.com/Wriskyzeus/poker-bot-hackathon.git
cd poker-bot-hackathon
uv python install 3.10
uv venv --seed -p 3.10 .venv
source .venv/bin/activate
make install
python3 play.py my_bots/uo_monte bots/caller --seed 7
make validate BOT=my_bots/uo_monte
```

For verbose play: `python3 play.py my_bots/uo_monte bots/caller --seed 7 --show`. For full sandbox testing: `make sandbox`, then `python3 play.py my_bots/uo_monte bots/caller --docker` (requires Docker).

**Final strategy (V3.4):** Stack-aware heads-up preflop scoring and opening/defense, bounded Monte Carlo showdown-equity estimates using `eval7`, pot-odds/stack-commitment analysis on flop and turn, selective river value-betting and opponent-conditioned defensive adjustments from public actions. This is a heuristic poker policy, **not a solved/GTO or live LLM system**. Alternate V4–V6 strategies were experimentally evaluated but did not establish a reliable generalization improvement; see the [testing history](docs/testing.md).

### Project documents

- [Windows / WSL setup](docs/windows-setup.md) · [Rules and API](docs/event-spec.md) · [Day checklist](docs/hackathon-checklist.md)
- [Architecture](docs/architecture.md) · [Strategy](docs/strategy.md)
- [Testing](docs/testing.md) · [Team workflow](docs/team-workflow.md)
- [Original organizers' README](docs/official-starter-kit.md) · [Research references](docs/resources.md)

## Submission

Only `my_bots/uo_monte/` is collected, with `bot.py` and optional `data/`. Validate with `make validate BOT=my_bots/uo_monte`, complete the [submission form](https://docs.google.com/forms/d/e/1FAIpQLScV6yLoWM0q7Lk-zqzqdfnfFYoZOYSK2VqGXTcsKB445uebsQ/viewform), and commit the final bot to **public `main` before the organizers' deadline**. The team was told the actual submission cutoff is **6:30 PM Eastern on November 21, 2026**. Team members confirmed submitting the registration form; preserve the confirmation receipt. The public `main` branch already holds final V3.4.

## Development rules

Keep `main` runnable. Use `feature/strategy`, `feature/engine-integration`, `feature/benchmarking` for experimental work. The validator restricts imports, file writes, network calls, background work and other sandbox operations. **Only the chosen bot folder is shipped; do not depend on local `src/` helpers outside that folder.**

The kit is copied from [FreddyyAndrews/poker-hackathon-kit](https://github.com/FreddyyAndrews/poker-hackathon-kit) under its MIT `LICENSE`. UO-Monte's `bot.py` is original team strategy code built on top of the official starter-kit interface; the rest of the organizer's engine remains unmodified. **Final bot:** protected V3.4 at `feature/strategy@a5ea561ff5b70d5a17533579bfc6557b2979622b`; released `bot.py` Git blob `27acb669ee3ac35172a88293c198182b56db0f78`. It passed the official validator and extensive local matched-seat matches. The restricted Docker 0.5-CPU/768MB tournament sandbox was not independently tested; competition performance is not guaranteed. Detailed evaluation records and experiment limitations appear in [docs/testing.md](docs/testing.md).
