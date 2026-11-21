# Confirmed event specification

Source: [official organizers' README](official-starter-kit.md).

| Topic | Confirmed rule |
|---|---|
| Game | Heads-up No-Limit Texas Hold'em |
| Tournament | Duplicate paired freezeouts (same cards, seats swapped); round robin; top four knockout |
| Starting stack | 10,000 each |
| Blinds | Rise every 20 hands: 25/50, 50/100, 75/150, 100/200, 150/300, then levels with antes |
| Language | Python 3.10 |
| Entry point | `my_bots/<team_name>/bot.py` exposing `decide(game_state: dict) -> dict` |
| Actions | `fold`, `check`, `call`, `raise` (total street bet amount), `all_in` |
| Time | 2,000 ms per decision; timeouts/crashes fold that action |
| Compute | 0.5 CPU core and 768 MB memory in sandbox |
| Imports | Python 3.10 standard library, `eval7`, `numpy`, `scipy`, `treys`, `scikit-learn` |
| Data | `bot.py` <= 5 MB; optional `data/` <= 200 MB, total <= 250 MB; data read at import time; no Python files in data |
| History | Module memory for one match; `match_action_log` last 200 actions, including showdown cards |
| Submission | Public `main` at deadline; exact registered team-name folder, lowercase letters/digits/underscores |
| Validation | `make validate BOT=my_bots/<team_name>` |

## API contract

```python
{"action": "fold"}
{"action": "check"}
{"action": "call"}
{"action": "raise", "amount": 1200}  # TOTAL bet committed this street
{"action": "all_in"}
```

Watch out: `check` while facing a bet becomes a **call**; `call` with nothing owed becomes a check. Undersized raises are adjusted to the minimum and unaffordable raises become all-in. Use `can_check`, `amount_owed`, `current_bet`, `min_raise_to`, `your_bet_this_street`, `your_stack`.

Game-state keys: `your_cards`, `community_cards`, `street`, `pot`, `your_stack`, `your_bet_this_street`, `amount_owed`, `can_check`, `current_bet`, `min_raise_to`, `your_bot_id`, `seat_to_act`, `button_seat`, `sb_seat`, `bb_seat`, `blinds`, `players`, `hand_num`, `hand_id`, `action_log`, `match_action_log`, `time_limit_ms`.

Before hand 1 the engine calls `decide({"type":"warmup"})`; use for initialization. Showdown cards are revealed only for players who reach showdown. Track opponent `bot_id` rather than seat. `pot` includes current bets.

## Restrictions

No network or external LLM calls during play; no file writes, subprocesses, shell commands, background compute after return, reflection with `eval`/`exec`/`compile`/`__import__`, peeking at opponents' code/cards, or collusion. Use the official validator.

## Ranking and prizes

Qualification is decided by pairing wins/draws; top four advance to knockout. The $750 prize pool also includes judged exploitative/game-theoretic strategies and measured bluffing, seven-two, comeback, and lowest-winning-showdown categories. See original README for exact metrics and minimum thresholds.

## Still requires confirmation

- Exact coding and submission cutoff time.
- Team name: chosen display name **UO-Monte**, required submission identifier **`uo_monte`**; verify the submission form has been completed using that exact identifier.
- Whether using AI assistance **during development** is permitted; this is distinct from the explicitly forbidden in-game LLM API calls.

## Schedule note

The attendee-reported event schedule is **9:30 AM–10:00 PM on November 21, 2026**. The starter kit's README header says **9:00 AM–10:00 PM**. Confirm check-in time directly with the organizers. Neither end time establishes the exact code cutoff; ask before assuming submissions are accepted until 10 PM.
