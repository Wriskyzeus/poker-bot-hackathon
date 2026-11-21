# Hackathon release checklist — final recorded state

**Event:** IEEE uOttawa × LARUS Poker Bot Hackathon, November 21, 2026  
**Official identifier:** `uo_monte` · **Repository:** [Wriskyzeus/poker-bot-hackathon](https://github.com/Wriskyzeus/poker-bot-hackathon)

This page records the project team's release-day status; it is **not** a live health dashboard or an organizer-issued acceptance certificate.

| Gate | Recorded status |
| :-- | :-- |
| Public GitHub repository with default `main` | **Verified** |
| Registered team folder `my_bots/uo_monte` | **Verified** |
| Protected V3.4 release blob on public main | **Verified** |
| Google submission form sent | **Confirmed by team** (receipt not independently checked) |
| Python 3.10 official validator | **Passed** (4 starter scenarios) |
| Release regression suite | **37 tests passed** in the archived V3.4 run |
| Docker sandbox image build | **Passed** on WSL2 Docker Desktop |
| Full Docker smoke vs organizer Caller | **Passed** — 46-hand freezeout, win, ~2 ms average decision time |
| Against unknown tournament entries | **Not established in advance** |

The team was informed of a **6:30 PM Eastern** submission cutoff on November 21, 2026.

## Reproduce basic checks

With dependencies installed in a Python 3.10 environment:

```bash
make validate BOT=my_bots/uo_monte
python3 play.py my_bots/uo_monte bots/caller --seed 7
```

With Docker configured:

```bash
make sandbox
python3 play.py my_bots/uo_monte bots/caller --docker --seed 7
```

**No further coding or re-submission was needed after the selected V3.4 release.** Later V4–V6 experiments and a rare mathematical edge-case fix remain archived research because they did not demonstrate robust tournament-match improvement.

Evidence: [engineering case study](engineering-case-study.md) · [full testing history](testing.md) · [official starter kit](official-starter-kit.md).
