# HANDOFF.md — UO-Monte

Read this at the start of every session. Update **Status** before every push.

## Ownership
| Area | Owner | Branch |
|---|---|---|
| Core `my_bots/uo_monte/bot.py`: preflop strategy and Monte Carlo equity | Teammate (Codex) | `feature/strategy` |
| Test harness | Alwaleed (Claude Code) | `alwaleed/exploit-and-testing` |
| Test opponent bots | Alwaleed (Claude Code) | `alwaleed/exploit-and-testing` |
| Opponent tracker with exploit rules | Alwaleed (Claude Code) | `alwaleed/exploit-and-testing` |

## Interfaces
Functions that one side calls and the other side provides. Change a signature only after you've updated it here and told the other person.

**Engine contract (fixed, nobody owns it)**
- `decide(game_state: dict) -> dict` in `my_bots/uo_monte/bot.py`. Returns `{"action": "fold" | "check" | "call" | "all_in"}` or `{"action": "raise", "amount": <total street bet>}`.

**Teammate provides (in `bot.py` on `feature/strategy`)**
- `_hand_features(cards: list[str]) -> tuple[score, pair, suited, connected, high, low]`: a preflop bucket score, not equity.
- `_respond(action: str | int, state: dict) -> dict`: turns a policy choice ("fold", "check", "call", "all_in", or a total raise amount) into a legal engine action.
- `_preflop(state: dict) -> dict`: the preflop policy.
- `_opponent_history(state: dict) -> int`: the current simple exploit adjustment (-3, 0 or +2) used by `_preflop`.
- *Planned (V2, not written yet):* a Monte Carlo equity function, e.g. `_equity(your_cards, community_cards, trials) -> float` (0..1, ties count 0.5). The name and signature are still to be confirmed.

**Alwaleed provides (proposed, not written yet)**
- Tracker: `_opponent_stats(state: dict) -> dict`, built from `match_action_log`. Example keys: `vpip`, `pfr`, `fold_to_raise`, `aggression`, `hands_seen`.
- Exploit rules: `_exploit_adjustment(stats: dict, street: str) -> dict`, returning tweaks the strategy can apply (e.g. `{"score_shift": int, "bluff_ok": bool, "call_margin": float}`).
- Test opponent bots: folders under `bots/`, each with the same `decide(game_state)` contract.
- Test harness: a script that runs `play.py` across seeds and both seats and reports win rate.

## Status
- Preflop v1.1 (teammate): done on `feature/strategy`; `main` still has the starter template `bot.py`.
- Monte Carlo equity V2 (teammate): spec written in `docs/v2-monte-carlo.md`; not started in code.
- Test harness (Alwaleed): not started.
- Test opponent bots (Alwaleed): not started (`bots/caller` and `bots/template` exist from the starter kit).
- Opponent tracker and exploit rules (Alwaleed): not started.
- Shared agent instructions (Alwaleed): `AGENTS.md`, `CLAUDE.md` → `@AGENTS.md`, and `HANDOFF.md` drafted, not committed.

## Open questions
- `_opponent_history` in `bot.py` already does a small exploit adjustment. Should Alwaleed's tracker replace it, or feed into it?
- What should the final equity function be called, and what is its signature? The tracker's exploit rules need to call it.
- Only `bot.py` ships. How do we merge the tracker into it: Alwaleed hands over functions to paste in, or a shared section of `bot.py` that Alwaleed owns?
- When does v1.1 get merged to `main`, and who signs off?
