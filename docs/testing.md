# Testing and benchmarking

Use **organizer's own** `play.py`, not other Fullhouse implementations.

```bash
make install
python3 play.py my_bots/uo_monte bots/caller --seed 7
python3 play.py my_bots/uo_monte bots/caller --seed 7 --show
python3 play.py my_bots/uo_monte bots/caller --seed 7 --log match.jsonl
make validate BOT=my_bots/uo_monte
make sandbox
python3 play.py my_bots/uo_monte bots/caller --docker
```

`make sandbox` / `--docker` require Docker; `make validate` does not.

## First local baseline result — November 21, 2026

**Status:** Organizer's unchanged starter bot executed a complete local freezeout match, but the validator has **not yet been run**.

```bash
python3 play.py my_bots/uo_monte bots/caller --seed 7
```

- Official core fingerprint reported: `2687febda342c653`
- Result: `caller` won, `uo_monte` lost after **134 hands** (one player left)
- Final stacks: `caller` **20,000**, `uo_monte` **0**
- Reported average think time: 0 ms (display rounded)
- No errors/timeouts were shown in the terminal summary
- **Interpretation:** setup and game integration work; this is **one seed**, not a statistically meaningful performance benchmark. The bot still uses the unmodified starter strategy.

**Next gate:** `make validate BOT=my_bots/uo_monte`. Then benchmark strategy upgrades using repeated matched seeds, swapped seats and timing checks.

## Checklist

- [ ] Warmup returns safely.
- [ ] Valid actions and total-street raise amounts; never checks when it owes money.
- [ ] Handles short stacks, all-ins, empty preflop board and final street.
- [ ] No non-allowlisted modules or forbidden behavior.
- [ ] Under 2 seconds on half a CPU core, not just your laptop.
- [x] Initial local freezeout completed without reported errors/timeouts (seed 7; official validator and sandbox still pending).
- [ ] Reproducible matched seeds and swapped seats.
- [ ] Validator passes on exact final submission folder.

Record match seeds, commit SHA, opponent, seat, outcomes, errors/timeouts, and average think time. Qualification is based on duplicate pairing wins/draws, not fixed-hand bb/100. Keep a known-good bot on `main`.
