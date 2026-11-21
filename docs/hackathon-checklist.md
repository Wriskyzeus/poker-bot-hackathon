# Hackathon day checklist

- [ ] Confirm exact registered team name and submission cutoff; rename `my_bots/poker_bot_hackathon/` if needed.
- [ ] Confirm whether AI-assisted **development** is allowed.
- [ ] Install WSL Ubuntu / build-essential / git / make if on Windows; prepare Python 3.10 using uv.
- [ ] Run `make install`, then `python3 play.py my_bots/poker_bot_hackathon bots/caller --seed 7`.
- [ ] Run `make validate BOT=my_bots/poker_bot_hackathon`.
- [ ] If possible build Docker sandbox and run `--docker`.
- [ ] Enter team name and repository URL on the [submission form](https://docs.google.com/forms/d/e/1FAIpQLScV6yLoWM0q7Lk-zqzqdfnfFYoZOYSK2VqGXTcsKB445uebsQ/viewform).

## Implement in order

1. Reliable legal output within 2 seconds.
2. Heads-up preflop and effective-stack rules.
3. Postflop equity/pot-odds calculation.
4. Opponent-model improvements.
5. Repeatable benchmark runs and speed checks.

## Before cutoff

- [ ] Entry at `my_bots/<registered_team_name>/bot.py`, plus only allowed optional data.
- [ ] No dependence on `src/` files or altered `pokercore/`.
- [ ] Run validator and one full match; Docker sandbox if possible.
- [ ] Final code merged to **public main** and pushed before cutoff.
- [ ] Folder name equals submission form; record final commit SHA.
