# Two-person Git workflow

- `main`: tested submission code.
- `feature/engine-integration`: entry-point validation, runtime, imports and sandbox.
- `feature/strategy`: algorithm changes in `my_bots/uo_monte/bot.py`.
- `feature/benchmarking`: extra local tests and match reports, which are not submitted.

```bash
git clone https://github.com/Wriskyzeus/poker-bot-hackathon.git
cd poker-bot-hackathon
git fetch origin
git switch feature/strategy
git merge origin/main
# edit / test
git add .
git commit -m "Improve heads-up preflop policy"
git push -u origin HEAD
```

Create pull requests into `main`. Keep at least one baseline that passes validation. To prevent merge conflicts, coordinate ownership of `my_bots/<team_name>/bot.py`; the other teammate can own benchmarking and analysis. Don't both change one function simultaneously.

**Important:** only the bot's exact matching team-name folder is collected. `src/` and `tests/` are local tools and not packaged. Never modify `pokercore/`.
