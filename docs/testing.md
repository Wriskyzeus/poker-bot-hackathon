# Testing and benchmarks

## First tests

- [ ] A baseline bot completes a hand without exceptions.
- [ ] Legal fold/check/call/raise cases return legal actions and amounts.
- [ ] Zero-cost check is handled correctly.
- [ ] Short stacks and all-in cases are handled.
- [ ] Missing history / empty board / final street are handled.
- [ ] Decision time remains below the official limit.
- [ ] Full match runs from start to finish.

## Benchmarks

Use the official engine whenever possible. Record:
- Game variant, score metric, number of hands/matches.
- Agent version / commit SHA.
- Opponent name / version.
- Random seed(s) and seat assignments (swap seats when possible).
- Runtime, errors, invalid actions, and timeouts.
- Mean score and uncertainty across batches, not just one lucky result.

### Experiments

1. Baseline vs organizer reference agent.
2. Baseline vs passive caller.
3. Baseline vs aggressive agent.
4. Equity model vs baseline on matched deals/seeds.
5. Opponent adaptation vs nonadaptive policy.

Do not claim a strategy is stronger from a handful of hands.

## Stable submission

Always keep the most recently tested, valid bot on `main`. Experiment in dedicated branches and merge only after a working match.
