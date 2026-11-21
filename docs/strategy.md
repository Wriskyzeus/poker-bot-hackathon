# Heads-up poker bot strategy

**Objective:** win duplicate freezeout pairings and the final heads-up bracket, not merely maximize cash-game bb/100. The original `bots/template/bot.py` is deliberately simple, and has been copied unchanged to the provisional entry `my_bots/poker_bot_hackathon/bot.py`.

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
