# Heads-up poker bot strategy

**Objective:** win duplicate freezeout pairings and the final heads-up bracket, not merely maximize cash-game bb/100. The original `bots/template/bot.py` is deliberately simple, and has been copied unchanged to the team entry `my_bots/uo_monte/bot.py`.

## Team identity and competitive plan

The team name is **UO-Monte**; the official submission identifier and folder name must be **`uo_monte`**. The name is chosen but the submission form still needs to be filed.

The proposed strategy is **heads-up, stack-aware, exploitative hybrid**:
- **Solid baseline:** position-aware heads-up preflop ranges, 3-bet/call rules, effective stack in big blinds, and tested short-stack shove/fold choices.
- **Equity estimation:** `eval7`-based Monte Carlo on flop, turn and river, sampled from sensible opponent ranges, with deterministic seeds and hard computation budgets. Equity alone is not an action policy.
- **Action EV:** pot odds for calls; sizing/fold equity/equity when called for raises; risk and changing blind structure for freezeouts. Avoid fixed arbitrary thresholds.
- **Opponent adaptation:** exploit leaks using `match_action_log` and showdown reveals, only when the sample size justifies a change. Track by `bot_id`.
- **Benchmarks:** test against callers, tight and aggressive opponents, matched seeds and swapped seats, with sandbox time measurements.

**Do not** start with Deep CFR training, neural networks, or massive external datasets. Prioritize correct legal actions and a fast validated bot. The 2-second wall clock limit and half CPU are hard constraints.

## Upgrade sequence

1. Robust legal actions and warmup handling.
2. Heads-up preflop ranges, position, raise/call/3-bet logic.
3. Effective stacks normalized by current big blind, including short-stack shove/fold decisions.
4. Postflop equity estimation with an allowed evaluator; select simulation budget under the 2-second half-core limit.
5. Pot odds and sizing: if `P` is the current pot and `C` the cost to call, basic showdown break-even equity (assuming no further betting) is `C/(P+C)`.
6. Opponent adaptation from `match_action_log`: fold/call/raise rates and showdown reveals, using adequate samples.
7. Randomized mixed actions if useful, seeded reproducibly; benchmark rather than assume improvement.

## Decision pseudocode

```text
decide(state):
    if state.type == "warmup": initialize permitted resources; return {"action":"check"}
    gather cards, board, street, pot, amount_owed, can_check,
           stack, position, blinds, action_log and match_action_log
    measure effective stacks in big blinds
    if preflop: use heads-up preflop policy
    else: estimate equity and choose value / bluff / defend based on prices
    optionally adjust using reliable opponent stats
    ensure the decision is legal and amount is total street bet
    return before 2000 ms
```

A call's pot-odds threshold alone does **not** select the best raise; betting also depends on fold equity, called equity, stack depth, and risk. Prioritize reliability and benchmark changes.


## Current repository status (November 21, 2026)

- Version 1.1, heads-up preflop heuristics plus a critical all-in safety correction, is committed to `feature/strategy` at `26c0a935eea310dbe7c64527d202f02a30431a53`.
- The submitted `main` branch still uses the organizer's template and must stay untouched until a stronger branch passes tests.
- 10 initial Version 1 matches against caller yielded 4 wins / 6 losses over seeds 1–5 with swapped bot ordering. This is too little data to claim an advantage.
- The next development milestone is specified in [v2-monte-carlo.md](v2-monte-carlo.md).
