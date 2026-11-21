# Architecture

Keep the decision policy independent from the tournament interface so the bot can be tested locally.

```text
Official game state
        |
        v
Input adapter and validation
        |
        v
Context (hand, board, stacks, pot, position, history, legal moves)
        |
        +--> Preflop policy / hand evaluation
        +--> Equity estimation (if feasible)
        +--> Opponent tendencies (if history available)
        +--> Pot odds, EV, and sizing
        |
        v
Decision policy
        |
        v
Legal action / amount validation
        |
        v
Official game engine
```

## Responsibilities

**Integration owner:** Map official input/output types, legal action constraints, safe fallback, submission format, and runtime.

**Strategy owner:** Implement preflop rules, showdown equity/pot-odds calculations, and opponent adaptation only where justified by the rules and test data.

Both owners share test cases and review changes before merging.

## Implementation priorities

1. Agent always returns a valid action.
2. Starter bot can complete a full game/match.
3. Basic strategy improves on the organizer baseline.
4. Equity and sizing enhancements pass benchmarks.
5. Opponent adaptation is added only if data and runtime allow it.

## Decisions pending official rules

Programming language, entry point, data structures, libraries, multiprocessing, state persistence, simulation budget, and game variant are all TBD.
