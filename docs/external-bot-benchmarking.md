# External poker-bot benchmarking — candidate research and rules gate

**Prepared 2026-11-21. Status: organizer permission reported verbally by UO-Monte team.** Team reports the organizers approved all four questions: (1) public open-source bots as offline practice opponents, (2) studying/adapting open-source code with license compliance, (3) pretrained model weights/strategy tables within submission limits, and (4) Codex/AI coding assistance during development. This is team-reported verbal guidance, not an independent written policy update. **The original runtime restrictions and ban on peeking at active tournament entries still apply.** This file documents a plan, not any completed external-bot benchmark.

## Why do this?

UO-Monte V2 reportedly won 40/40 local freezeouts against the organizer-provided `bots/caller`, but that opponent never bets postflop. We need stronger adversaries that value bet, bluff, raise postflop and exploit bad calls. Maintain objective win/loss measures on *paired seeds and seat swaps*, with match logs, failure counts and decision latencies.

## Strong open-source candidates

1. **Tanuj Kakumani, Fullhouse finalist**: https://github.com/txnujk09/fullhouse-poker-bot — reported top-64 qualifier; MIT-licensed. Its final `bots/floorfix/bot.py` is primarily Python + `eval7`, with Monte Carlo, a preflop equity table and opponent profiling. Candidate **first** external opponent if organizers approve using public competitor code for offline tests.
2. **Advit Arora, Deep CFR finalist**: https://github.com/advitrocks9/fullhouse-bot — reports 15th/64 in Fullhouse final, with pretrained weights and a NumPy runtime. Candidate **second**, because integration needs careful feature/action translation and may be more work than the expected benefit.

Both were built for predominantly **six-player** competitions rather than IEEE's **heads-up, 10,000-chip freezeouts with rising blinds**, so neither can be assumed to outperform UO-Monte without testing. Original README claims are author-reported, not verified head-to-head results.

The current IEEE starter kit derives from Full House's engine but modifies state format, rising blinds and sandbox. **Do not simply copy a third-party bot into `my_bots/uo_monte/`**, and do not change `pokercore/` to make a bot work. A test-only action/state adapter would need correct semantics, especially the button, `min_raise_to`, total street betting, `amount_owed`, `match_action_log`, runtime memory and 2-second deadline.

## Organizer clarifications (answered verbally by team)

The official README (https://github.com/FreddyyAndrews/poker-hackathon-kit) says **No peeking**: do not read other bots' code or hidden cards. It does not explicitly distinguish public, previously published external projects from other *current tournament entries*.

Ask:
1. May we download and run publicly published GitHub poker bots solely as **offline local practice opponents**? Does the 'no peeking' rule refer only to other tournament submissions or extend to public historical code?
2. May we adapt **MIT-licensed** code/algorithms in the submitted bot, with attribution, or must all submitted strategy code originate from our team?
3. Are **externally pretrained** model weights or precomputed strategy tables allowed in `my_bots/<team_name>/data/` (subject to published sizes/import-time reads)? The kit allows generic data files, but does not explicitly resolve third-party model provenance.
4. Is AI-assisted coding during development (e.g. local Codex CLI) permitted? The rule explicitly bans **live** network/LLM calls from the submitted bot.

**Status:** On November 21, the team reported the organizer said **yes to all four questions**. Public historical GitHub code can be considered for offline benchmarking; licensed reuse and pretrained weights are allowed subject to license and all published tournament restrictions. Avoid interpreting this as permission to inspect an active participant's private or unpublished entry, collude, or bypass sandbox limits.

## Meanwhile: compliant-looking test development

The starter kit explicitly provides the match runner for local tests and encourages building test harnesses and opponents. Proceed with original, self-written **tight-aggressive (TAG)**, **loose-aggressive (LAG)**, **nit**, and **mixed/bluffing** benchmark opponents using only the publicly documented game-state fields and a clean `decide()` action contract. Store test bots in a separate `bots/local_*/bot.py` directory; they must not be imported at runtime by `my_bots/uo_monte/bot.py`.

Run `python3 play.py my_bots/uo_monte bots/local_aggressive --seed N` and reverse bot order for the same seed; do repeated matched seeds, record errors/timeouts, ensure no hidden-card peeking and no changes to `pokercore/`.

## Implementation now that organizer approval is reported

- Clone the external repo **outside the submission folder**; note its exact license and commit SHA.
- Use a test-only adapter, which maps the IEEE state to the external bot's expected interface and translates back only legal actions. Preserve hidden information; never expose future cards or read opponent memory.
- Test both seat assignments, multiple seeds, realistic stack/blind levels and Docker sandbox timing where feasible. Compare UO-Monte V2, V1.1 and the test-only external opponent.
- If external code is approved for submission, independently review it against every IEEE runtime restriction and the original MIT notices; do not blindly merge it into `uo_monte`.
- If an unanticipated case is not clearly covered by what the organizer approved, ask again before submitting external components.

## Key restrictions to preserve

Only `my_bots/uo_monte/bot.py` and permitted `data/` ship; Python 3.10 with `eval7`, NumPy, SciPy, Treys, scikit-learn and standard library; 2-second deadline, 0.5 CPU core, 768 MB RAM, no network/file writes/processes/background work/reflection/peeking/collusion. Final tested entry must be on public `main` by organizer cutoff. Passing the static validator is necessary but **not sufficient** for every rules question.

## Submission deadline

The team reports the organizers set **6:30 PM Eastern Time on Saturday, November 21, 2026** as the cutoff. The official README requires the repo to be **public** and the final tested bot to be on **`main`** by that time. Plan to freeze and push well before the cutoff, rather than at exactly 6:30 PM.
