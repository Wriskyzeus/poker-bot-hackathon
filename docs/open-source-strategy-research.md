# Open-source strategic upgrades — UO-Monte (research, November 21, 2026)

**Purpose:** identify algorithmic upgrades with credible potential to outperform small heuristic tweaks. Public web-based research, not yet installed or benchmarked locally. **Not permission to copy finalist submissions or to modify the deployed bot.** The human teammates reported that original work built using appropriately licensed open-source research, pretrained strategy tables and AI assistance is allowed, subject to official runtime/size constraints.

## Current bot bottlenecks

V3.4 `my_bots/uo_monte/bot.py` uses an unsolved scalar score for all 169 preflop starting-hand classes, with manually selected cutoffs for button opens, 3-bets and 4-bet defense. When acting postflop with no bet owed on flop/turn, its generic policy bets primarily above random-hand equity **0.72**; its equity estimates often sample from a *uniform random opposing hand*, not a betting-line-conditioned opponent range. These are major structural limitations relative to stronger poker algorithms. Preflop heuristic changes V3.6 and V3.6.1 had inconclusive fresh-seed wins and failed to replicate their initial short-stack advantage. The next opportunity is better **strategy representation and decision EV**, not simply lowering a threshold.

## Priority 1 — Offline CFR/Nash-derived preflop strategy tables

**Hypothesis:** Replace coarse score cutoffs with **heads-up, position-, action-, and effective-stack-specific** 169-hand-class strategy probabilities from a solver, while preserving exploitative adaptation and legal bet formatting. Use a small static table (or compact embedded constants) at runtime; the solver itself does **not** run in the tournament sandbox. Focus first on **3–15BB push/fold/call** because full all-in equity gives more trustworthy values here than deep-stack terminal approximation. Rising blinds, antes and effective stacks must be modeled or documented; cash-game 100BB ranges cannot be blindly transplanted.

**Strong candidates to evaluate OFFLINE:**

1. [cRITlamb/poker_solver](https://github.com/cRITlamb/poker_solver) — claims MIT license; heads-up no-limit, precomputed preflop blueprints, 169-class lookup across stack/ante configurations, CLI for short-stack push/fold and joint range-vs-range DCFR, Python reference + Rust core. Uses a Rust build and additional dependencies **offline**; not a permitted direct tournament import. Repository instructions include `poker-solver pushfold --stack 10 --position sb_jam --hand AKs` and `--full-range --json`. Need independent correctness spot checks, license/attribution verification and an artifact extraction script. Its description states deep-stack full-range flop solving takes minutes.
2. [chirenonhive/poker-solver](https://github.com/chirenonhive/poker-solver) — claims MIT license; Python/NumPy CFR+ preflop heads-up solver, exact blocker enumeration, push/fold config `poker-solver solve --stack 12 --push-fold`. **Caution:** the author explicitly says deep-stack non-all-in terminal equities are an optimistic approximation; repo is young and has few independent adopters. Cross-check with a second source and explicit tests.
3. [jensbaagaard/poker-practice](https://github.com/jensbaagaard/poker-practice) — MIT-licensed published open-range JSON, scenarios including opens/vs 3-bet and 5–100BB tournament ranges. **Not a direct heads-up solver:** source charts are mostly **6/8/9-handed**, so use as a *format/interpretation reference*, not a substitute for correct SB/BTN versus BB charts.

**Engineering:** two-stage architecture `offline solver/trainer -> tiny JSON data/ tables -> safe Python3.10 lookup in bot.py`. Use deterministic per-hand frequency mixing (seeding only public observations) when strategies are mixed; preserve legal total-street bet semantics. Store provenance, date/commit SHA, model parameters and MIT notices if any code/data is incorporated. The rules permit optional `my_bots/uo_monte/data/` files up to **200 MB**, and `bot.py` max **5 MB**. All reads occur at import/warmup if needed, no file writes/threads/external processes/network during play.

**Important risk:** Nash-style approximate ranges are not necessarily maximally exploitative against practice bots; a new chart must beat the baseline in fresh paired freezeouts, not merely look theoretically impressive.

## Priority 2 — Opponent-range-weighted equity and action-value betting

V3.4 includes some river aggression/range approximations, but generic flop/turn branches use random-opponent Monte Carlo. A better design models *conditional* opponent hand probabilities from position, preflop action (open/call/three-bet/four-bet), effective stack, flop/turn bet size, board blockers, draws, showdowns and Bayesian shrinkage for sparse action history. Then estimate **equity versus that range**, rather than versus arbitrary random cards. Evaluate alternative actions using a rough **action-EV** decomposition, including fold probability, equity when called, cost, payout, stack-to-pot ratio and tournament freezeout considerations. This is a much bigger design improvement than a static `equity >= 0.72` betting trigger.

Bound computational budget strictly: precompute ranges/lookup tables, retain existing optimized `eval7` and Monte Carlo runtime where useful, and benchmark on the official 0.5CPU/768MB sandbox. The priority is **calibrated opponent ranges, legal actions and EV ranking**, not expensive online CFR.

## Priority 3 — Offline CFR blueprint for complex postflop

[CFR river reference from noambrown/poker_solver](https://github.com/noambrown/poker_solver) appears MIT-licensed and includes river subgame solving via CFR/CFR+/DCFR in Python/C++. Useful for research on proper river bluff:value proportions and sizing, but may be overkill for today's deadline.

[matteo-psnt/poker-solver](https://github.com/matteo-psnt/poker-solver) claims MIT license and uses pre-trained abstracted poker blueprints and a 3–100BB depth ladder. Its public 100BB blueprint reportedly consumes **1.9GB**—far beyond our 200MB data allowance—so **do not integrate the entire model or its runtime**; inspect algorithms/compact preflop chart ideas only. That repository describes needing many thousands of paired games for reliable improvement evaluation. Availability of a model is not proof it matches our game rules.

The well-known [TexasSolver](https://github.com/bupticybee/TexasSolver) is **AGPL-3.0**, not MIT. Do not represent it as MIT or transplant its source into the submitted bot without a separately cleared license decision. A project's description of solver output does not necessarily establish licensing of every dataset and derivative. Preserve attribution and record the exact third-party file origin and license in any implementation.

## Practical next experiment, not automatic promotion

A. Codex finishes **TASK-CODEX-006 / V3.7** without interruption. If its postflop change is only marginal or hurts fresh holdout, retain committed V3.4.

B. As a next separate scoped task, assess whether an MIT-sourced **offline 169-class SB-vs-BB push/fold/defense table** can be generated and tested quickly. First validate one supported stack depth against at least two solvers or known equilibrium examples. Ensure action mapping for the organizer's blind/ante structure and costs. If feasible, implement a candidate in a clean worktree based on V3.4, **not** on unapproved stacked experiments.

C. Compare baseline vs new table with identical seats/deals over independent dev and holdout seeds, multiple opponent styles (especially aggressive/mixed, not just Caller), shallow/rising blinds, total tournament wins, pair W/D/L and hand-level EV/risk proxies. Record action-change frequency and cases of divergence. Use Claude's independent opponents as further diagnostics. **Never use sealed seeds 1001–1200 for optimization.**

D. In parallel with / after source feasibility, prioritize **range-conditioned postflop equity + action-EV** for the next substantive upgrade. This may be higher strategic upside than chart replacement in deep stacks, but is technically more complex and requires careful opponent-model validation.

**Stop conditions:** no compatible license, untrustworthy/untestable solver data, poor runtime/size behavior, inability to map rules cleanly, or no reproducible improvement. Protect V3.4 as fallback. Deadline **6:30 PM ET**, release checkpoint **5:30 PM ET** and final human approval required for commits/merges/pushes.

## Source status

All external links checked November 21, 2026 via public repository README pages. Descriptions and license claims are **upstream author statements**, not independently audited mathematical correctness or compatibility. MIT code may require retention of license text/attribution. No third-party code or tables have been incorporated into UO-Monte by this research note.
