# Poker Bot Hackathon — IEEE uOttawa × LARUS

Two-person Python poker-bot project for the November 21, 2026 hackathon.

**Game:** heads-up No-Limit Texas Hold'em, freezeout matches, rising blinds and antes. **Runtime:** Python 3.10; 2 seconds per decision, 768 MB RAM, 0.5 CPU core. **Competition:** duplicate-seated qualification pairings followed by a top-four heads-up knockout.

## Start here

This repo incorporates the [official organizer starter kit](https://github.com/FreddyyAndrews/poker-hackathon-kit): actual tournament engine (`pokercore/`), bot template (`bots/template/`), reference caller (`bots/caller/`), runner (`play.py`), validator, and pinned dependencies. **Don't edit `pokercore/`.**

An unchanged template bot is at **`my_bots/poker_bot_hackathon/bot.py`**. The `poker_bot_hackathon` name is **provisional**. The submission folder **must equal your registered team name** (lowercase letters, digits, underscores). Rename it before submitting if necessary.

### Run locally — Windows

The organizers recommend **WSL Ubuntu**; commands below are for a Linux shell, not PowerShell. Install `git`, `make`, `build-essential` and the [uv Python manager](https://docs.astral.sh/uv/) if needed.

```bash
git clone https://github.com/Wriskyzeus/poker-bot-hackathon.git
cd poker-bot-hackathon
uv python install 3.10
uv venv --seed -p 3.10 .venv
source .venv/bin/activate
make install
python3 play.py my_bots/poker_bot_hackathon bots/caller --seed 7
make validate BOT=my_bots/poker_bot_hackathon
```

For verbose play: `python3 play.py my_bots/poker_bot_hackathon bots/caller --seed 7 --show`. For full sandbox testing: `make sandbox`, then `python3 play.py my_bots/poker_bot_hackathon bots/caller --docker` (requires Docker).

### Project documents

- [Rules and API](docs/event-spec.md) · [Day checklist](docs/hackathon-checklist.md)
- [Architecture](docs/architecture.md) · [Strategy](docs/strategy.md)
- [Testing](docs/testing.md) · [Team workflow](docs/team-workflow.md)
- [Original organizers' README](docs/official-starter-kit.md) · [Research references](docs/resources.md)

## Submission

Only `my_bots/<exact_team_name>/` is collected, with `bot.py` and optional `data/`. Validate with `make validate BOT=my_bots/<exact_team_name>`, complete the [submission form](https://docs.google.com/forms/d/e/1FAIpQLScV6yLoWM0q7Lk-zqzqdfnfFYoZOYSK2VqGXTcsKB445uebsQ/viewform), and commit the final bot to **public `main` before the organizers' deadline**. The exact cutoff time has not yet been confirmed.

## Development rules

Keep `main` runnable. Use `feature/strategy`, `feature/engine-integration`, `feature/benchmarking` for experimental work. The validator restricts imports, file writes, network calls, background work and other sandbox operations. **Only the chosen bot folder is shipped; do not depend on local `src/` helpers outside that folder.**

The kit is copied from [FreddyyAndrews/poker-hackathon-kit](https://github.com/FreddyyAndrews/poker-hackathon-kit) under its MIT `LICENSE`. The starter bot is unchanged; no benchmarks or performance improvements are claimed yet.
