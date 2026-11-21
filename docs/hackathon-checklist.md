# Hackathon day checklist

- [ ] Submit the team name as `uo_monte` (display name UO-Monte) on the form. **Organizer-reported submission cutoff is November 21, 2026, 6:30 PM ET.**
- [x] Organizer verbally approved AI-assisted development, offline open-source benchmark opponents, licensed strategy adaptation, and external model/data tables subject to original runtime rules (reported by team on November 21).
- [ ] Install WSL Ubuntu / build-essential / git / make if on Windows; prepare Python 3.10 using uv.
- [ ] Run `make install`, then `python3 play.py my_bots/uo_monte bots/caller --seed 7`.
- [ ] Run `make validate BOT=my_bots/uo_monte`.
- [ ] If possible build Docker sandbox and run `--docker`.
- [ ] Enter `uo_monte` as the team name and the repository URL on the [submission form](https://docs.google.com/forms/d/e/1FAIpQLScV6yLoWM0q7Lk-zqzqdfnfFYoZOYSK2VqGXTcsKB445uebsQ/viewform).

## Implement in order

1. Reliable legal output within 2 seconds.
2. Heads-up preflop and effective-stack rules.
3. Postflop equity/pot-odds calculation.
4. Opponent-model improvements.
5. Repeatable benchmark runs and speed checks.

## Before cutoff

- [ ] Entry at `my_bots/uo_monte/bot.py`, plus only allowed optional data.
- [ ] No dependence on `src/` files or altered `pokercore/`.
- [ ] Run validator and one full match; Docker sandbox if possible.
- [ ] Final code merged to **public main** and pushed safely before **6:30 PM ET on November 21, 2026**.
- [ ] Folder name equals submission form; record final commit SHA.
