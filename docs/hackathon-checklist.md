# Hackathon quick start

## First 15 minutes

- [ ] Confirm event rules, permitted dependencies, and submission cutoff.
- [ ] Update [event-spec.md](event-spec.md).
- [ ] Clone this repository and run `git status`.
- [ ] Install only the required official dependencies.
- [ ] Run the supplied starter bot unchanged and verify a complete match.
- [ ] Agree which teammate owns integration and which owns strategy.

## Coding order

1. Make the official entry point return valid actions for all common states.
2. Add tests for action legality and edge cases.
3. Establish baseline match scores.
4. Implement preflop and postflop improvements one at a time.
5. Benchmark each improvement using repeatable seeds.
6. Preserve a known-good submission version before the cutoff.

## Before submitting

- [ ] Confirm correct branch, file paths, and entry-point signature.
- [ ] Check no unused or unauthorized dependencies.
- [ ] Run a complete match using the official engine.
- [ ] Check timeout, crash, invalid action and bet-size cases.
- [ ] Record the final commit SHA.
- [ ] Follow the official submission instructions.
