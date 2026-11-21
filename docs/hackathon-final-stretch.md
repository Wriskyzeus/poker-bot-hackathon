# UO-Monte hackathon final-stretch plan — November 21, 2026

## Hard deadline and release rules

- **Organizer-reported cutoff:** **6:30 PM Eastern Time on November 21, 2026**.
- Tournament collection reads **public `main`**, not `feature/strategy`. Preserve a tested commit hash for the final entry.
- Aim to **freeze, validate and push the best bot by 5:00 PM ET at the latest**. Do not spend the last minute merging.
- The user plans to dedicate the final ~1–2 hours to **understanding, documenting and explaining the implementation** to judges. Prioritize this rather than adding untested features near cutoff.
- `feature/strategy` currently contains Version 2, commit `ef760ca5bf14b367feac9accb3f4b3fbeb478181`. Main is **not** yet the V2 tournament submission.

## Clarification from organizers (as relayed by the team)

Organizers verbally permit open-source poker bots as local opponents, studying open-source techniques, pretrained data and AI development tools under published runtime restrictions. **They explicitly do not want a copied-and-pasted finalist bot submitted as this team's own entry.** Build and document independent UO-Monte logic; use external projects primarily as sparring partners and research references, credit any sourced or adapted ideas/code, and seek explicit confirmation again if a borderline use arises.

## Sequenced priorities

### Gate A — External benchmark opponent

- Run the previously approved local external-opponent benchmark, starting with the MIT-licensed Fullhouse `floorfix` bot at `https://github.com/txnujk09/fullhouse-poker-bot`.
- Clone into an isolated, clearly named external benchmark directory **outside** `my_bots/uo_monte`. Keep license and origin SHA.
- Write a **test-only state/action adapter** against the official IEEE engine. Do not reveal hidden cards or change `pokercore/`.
- Run smoke test plus 20 matched seeds with swapped seats if compatible, report wins/losses, invalid actions, latency and hand-history leak examples. Do not copy the opponent's source into the UO-Monte entry.
- If six-max incompatibilities are costly, stop and return to V3 based on existing custom opponents.

### Gate B — V3 opponent-aware exploitative strategy

Driven by established V2 weaknesses:
1. River calls overestimate equity against a tight value-betting range.
2. One-pair hands are overcommitted against raises.
3. Thin river value bets are vulnerable to check-raises.

Develop one focused change per checkpoint. Model opponent tendencies and range strength from allowed `match_action_log` and `action_log`, adjust to observed street/bet-size/action, with adequate-sample fallbacks. Preserve strong performance against passive Caller and Aggressive while improving against Tight and Mixed.

### Gate C — Proper regression tests

- Benchmark each candidate vs Caller, Aggressive, Tight, Mixed and approved external bot using paired seeds + swapped seats.
- Compare against saved V2 and V1.1; do not choose a version based on one win rate.
- Run unit tests, `make validate BOT=my_bots/uo_monte`, and ideally Docker sandbox (`make sandbox` and `play.py ... --docker`) under the true 0.5 CPU / 768 MB / 2s limits.
- Review worst-case latency and errors, not just averages. Keep a frozen rollback commit.

### Gate D — Final deployment

- Freeze features before 5 PM ET; pick best tested candidate, merge or cherry-pick only approved bot/test changes to `main`, validate again on the actual `main` tree, push `main`.
- Confirm public repository, exact submission folder `my_bots/uo_monte/bot.py`, official team identifier `uo_monte`, submitted form, last commit SHA and actual remote `main`.
- Be careful: updating docs on `main` before the final candidate is ready does **not** submit V2/V3. Do not assume feature-branch code is the deployed entry.

### Gate E — Learning/presentation practice (~5:00–6:15 PM ET)

Use the exact final `bot.py` and documentation, not an old draft, to teach the team step by step:
- state/action API and safety limits
- heads-up preflop, stacks, opening/calling/3-betting
- Monte Carlo equity, tie weighting, pot odds and bet sizing
- opponent modeling (range assumptions, history sample sizes, exploitation)
- evidence from benchmarks, limitations, live demo and judge questions

Allocate the last ~15 minutes before cutoff to check the submitted URL and branch once more rather than changing strategy.

## Scope protections

Do not change `pokercore/`, access other competitors' hidden cards/code, call remote services at bot runtime, write files from the bot, bypass the 2s deadline, or copy a third-party finalist bot wholesale into the submission. The official validator is necessary but not proof of total compliance.
