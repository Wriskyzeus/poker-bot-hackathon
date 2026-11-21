# AGENTS.md — UO-Monte poker bot

Shared instructions for every coding agent on this repo (Claude Code, Codex, and others).
`CLAUDE.md` just imports this file, so edit rules here, not there.

## Every session
- **At the start of every session, read `HANDOFF.md`.** It records who owns what, the function signatures each side relies on, current status, and open questions.
- **Before pushing, update the Status section of `HANDOFF.md`**: one line per task. If you changed a function listed under Interfaces, update its signature there too.

## Goal
- Build a bot for **heads-up No-Limit Texas Hold'em**. We write `decide(game_state)` in `my_bots/uo_monte/bot.py`.
- Bots play a tournament. Judges give prizes for the **best exploitative** strategy and the **best game-theoretic** strategy. Both teammates must be able to explain the code, and Alwaleed is new to poker and git. Explain changes in plain language and teach as you go.

## Ownership
- **Teammate (uses Codex)** owns the core `my_bots/uo_monte/bot.py`: the preflop strategy and the Monte Carlo equity code.
- **Alwaleed (uses Claude Code)** owns the **test harness**, the **test opponent bots**, and the **opponent tracker with exploit rules**. Alwaleed works on the branch `alwaleed/exploit-and-testing`.
- Don't rewrite code the other person owns. If you need a change there, describe it under Open questions in `HANDOFF.md` or ask your user.

## Runtime and sandbox rules
- **Python 3.10 only.** Activate the venv first: `source .venv/bin/activate`.
- Allowed libraries inside the bot: standard library, `eval7`, `numpy`, `scipy`, `treys`, `scikit-learn`.
- Not allowed inside the bot: network access, file writes, subprocesses, threads, `eval`, `exec`.
- Limits: **2 seconds per decision**, 768 MB RAM, 0.5 CPU core.

## What not to touch
- **Never edit `pokercore/`.** It is the tournament engine.

## What gets graded
- Only `my_bots/uo_monte/` is graded: `bot.py` plus an optional `data/` folder (no `.py` files in `data/`).
- Anything the bot needs at runtime, including the opponent tracker, must end up inside `bot.py` when it ships.

## Git rules
- Work only on your own branch. **Never push to `main`.**
- Never push, force-push, delete branches, or delete files without asking your user first.
- Commit small, with clear messages.

## Definition of done
Before calling anything done, run both:
1. `make validate BOT=my_bots/uo_monte`
2. A test match, e.g. `python3 play.py my_bots/uo_monte bots/caller --seed 7`

## Engine gotchas
- Returning `check` when we owe chips is played as a **call**.
- Raise amounts are the **total** bet for the street, not the extra amount added.
- A crash or timeout **folds** the hand.
