# Strategy plan

This is a plan, **not** a working poker strategy or guaranteed winning policy.

## Baseline

- Handle each legal action explicitly (fold / check / call / raise or equivalents).
- Avoid illegal amounts and timeouts.
- Start with position- and stack-aware preflop decisions where the variant supports them.
- Use a simple postflop policy until equity calculation is validated.

## Candidate improvements

- **Equity:** Estimate win/tie probability against appropriate opponent ranges, using the official evaluator or an allowed optimized library.
- **Pot odds:** For a call costing `C` into a current pot `P`, basic break-even showdown equity with no further betting is `C / (P + C)`.
- **Raises:** Evaluate fold equity, value when called, risk, stack sizes, and legal bet sizes. Do not use call equity alone to choose raises.
- **Opponent modeling:** Track tendencies only when the engine supplies action history and enough observations.
- **Randomization:** Use mixed actions sparingly to avoid being predictable; honor reproducible seeds for tests.

## Decision pseudocode

```text
decide(raw_state):
    state = parse_official_state(raw_state)
    actions = state.legal_actions
    if no actions: handle according to official contract
    if insufficient information: return safe_legal_fallback(actions)

    context = summarize_hand_position_stacks_pot(state)
    if preflop:
        candidate = preflop_policy(context)
    else:
        equity = estimate_equity_if_supported(context)
        candidate = postflop_policy(context, equity)

    action = adjust_for_opponent_if_evidence_is_sufficient(candidate, context)
    return validate_or_fallback(action, actions)
```

All helper names are placeholders and must be adapted to the starter code.

## Questions to answer with tests

1. Does aggression improve the actual competition score?
2. How many simulations fit under the decision-time limit?
3. Which opponents are the baseline policy weak against?
4. Do opponent-specific adjustments beat a stable default policy over enough trials?
