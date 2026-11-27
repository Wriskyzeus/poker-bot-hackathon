# Experiments at a glance

A short index of the team's development investigations. For detailed seeds, caveats, test transcripts and source-specific measurements, consult the [full chronological testing record](testing.md). The [engineering case study](engineering-case-study.md) explains the overall method and learning outcomes.

## How comparisons were evaluated

Candidate policies were tested against controlled **practice opponents**, frequently with matched seeds and swapped starting seats. Primary release decisions used **complete freezeout wins and duplicate-pair results**, rather than only the chips won in selected hands. Individual experiments use different seed sets, so results should not be compared across rows as if they came from one tournament.

| Iteration | Research question | Result / lesson |
| :-- | :-- | :-- |
| **V3.4 (released)** | Could a conservative stack-aware policy plus river value logic run reliably? | Official validator and 37 regression tests passed; Docker reference-Caller smoke passed |
| V3.5 | Would selective semi-bluffs generate additional fold equity? | No observed general match-win advantage on the initial synthetic field |
| V3.6 / V3.6.1 | Could effective-stack and 3-bet adjustments help? | Some gains in specific tests, but mixed holdout/short-stack outcomes |
| V3.7 | Would smaller flop/turn bet sizes improve match wins? | Small or inconsistent gains, insufficient to promote |
| V4 / V4.1 | Could tracking opponent actions improve range-conditioned choices? | Useful diagnostics, but no consistent improvement over the released policy |
| V5-P / V5-F | Should the bot defend more carefully at specific prices? | Mixed or identical results |
| V5-R | Could evidence-based river overbet defense improve performance? | Safeguards produced effectively no meaningful action divergence |
| V5-S / V5-A | More precise preflop size defense and 3-bet decisions | V5-S slightly worsened; V5-A changed no decisions in the evaluated sets |
| V6-P | Would a 169 starting-hand class representation improve preflop play? | Multiple changed actions, but mixed generalization and short-stack regressions |
| V6-Stab | Could the bot exploit checked-to pots when opponents overfold? | Profitable against a synthetic overfolder, but not consistently across callers and trappers |
| V6-Protection | Could additional value/protection betting improve outcomes? | Development **45/72** vs V3.4 **43/72**; holdout **60/108** vs V3.4 **63/108** |
| Final short-stack price audit | Was there a specific all-in pot-odds oversight? | Rare edge case identified; only **3 decisions** altered in 800 archived matches; no development match-win gain |

## Lessons retained

**1. Stronger local EV doesn't imply more wins.** A bet may win an immediate pot but sacrifice future value from weaker hands that would have called later. Whole-match testing caught these effects.

**2. Opponent exploitation needs reliable evidence.** A bet that works against a deliberately exploitable check-folder may be expensive against a calling or check-raising opponent. Small samples of public actions can be misleading.

**3. Simulation is not a full poker strategy.** Monte Carlo equity against random hands is a useful building block but does not solve opponent ranges, future-street value or multi-action decisions.

**4. Reproducibility and deployment count.** The project used unit tests, the official validator, seeded matches and an isolated Docker sandbox. The official reference-Caller smoke confirmed baseline compatibility but not strength against unknown tournament entrants.

## Archive policy

This index deliberately omits task-by-task command logs, speculative counterfactual estimates, and internal agent messages. Nothing has been deleted: the original [testing history](testing.md) and [full multi-agent handoff](archive/development-handoff-2026-11-21.md) remain available. The released bot remains [V3.4](../my_bots/uo_monte/bot.py).
