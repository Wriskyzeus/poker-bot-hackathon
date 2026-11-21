# Testing and benchmarking

Use **organizer's own** `play.py`, not other Fullhouse implementations.

```bash
make install
python3 play.py my_bots/poker_bot_hackathon bots/caller --seed 7
python3 play.py my_bots/poker_bot_hackathon bots/caller --seed 7 --show
python3 play.py my_bots/poker_bot_hackathon bots/caller --seed 7 --log match.jsonl
make validate BOT=my_bots/poker_bot_hackathon
make sandbox
python3 play.py my_bots/poker_bot_hackathon bots/caller --docker
```

Replace provisional team name in commands when confirmed. `make sandbox` / `--docker` require Docker; `make validate` does not.

## Checklist

- [ ] Warmup returns safely.
- [ ] Valid actions and total-street raise amounts; never checks when it owes money.
- [ ] Handles short stacks, all-ins, empty preflop board and final street.
- [ ] No non-allowlisted modules or forbidden behavior.
- [ ] Under 2 seconds on half a CPU core, not just your laptop.
- [ ] Full freezeout completes with no errors/timeouts.
- [ ] Reproducible matched seeds and swapped seats.
- [ ] Validator passes on exact final submission folder.

Record match seeds, commit SHA, opponent, seat, outcomes, errors/timeouts, and average think time. Qualification is based on duplicate pairing wins/draws, not fixed-hand bb/100. Keep a known-good bot on `main`.
