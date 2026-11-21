# Two-person workflow

## Branches

- `main` — tested, stable work.
- `feature/engine-integration` — starter-code integration, action validation, game-state adapter.
- `feature/strategy` — decision rules, equity, opponent modeling.
- `feature/benchmarking` — test agents, reproducible matches, reports.

## Start of work

```powershell
git clone https://github.com/Wriskyzeus/poker-bot-hackathon.git
cd poker-bot-hackathon
git fetch origin
git switch feature/engine-integration   # or the branch you own
git pull --ff-only
```

## Save changes

```powershell
git status
git add .
git commit -m "Implement legal action validation"
git push -u origin HEAD
```

Open a pull request into `main`. Ask the other teammate to review. Merge only when it runs correctly.

## Avoid collisions

- Integration owner: official engine files, state adapter, output validation.
- Strategy owner: decision policy, equity and opponent-model modules.
- Benchmark owner: shared responsibility, or whoever is not integrating.
- Do not both edit the same starter-code file simultaneously unless pairing.
- Keep external engines and third-party bots separate; honor competition rules and licenses.
