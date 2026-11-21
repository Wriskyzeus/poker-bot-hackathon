# Open-source strategic upgrades — UO-Monte (research, November 21, 2026)

**Purpose:** identify algorithmic upgrades with credible potential to outperform small heuristic tweaks. Public web-based research, not yet installed or benchmarked locally. **Not permission to copy finalist submissions or to modify the deployed bot.** The human teammates reported that original work built using appropriately licensed open-source research, pretrained strategy tables and AI assistance is allowed, subject to official runtime/size constraints.

## Current bot bottlenecks

V3.4 `my_bots/uo_monte/bot.py` uses an unsolved scalar score for all 169 preflop starting-hand classes, with manually selected cutoffs for button opens, 3-bets and 4-bet defense. When acting postflop with no bet owed on flop/turn, its generic policy bets primarily above random-hand equity **0.72**; its equity estimates often sample from a *uniform random opposing hand*, not a betting-line-conditioned opponent range. These are major structural limitations relative to stronger poker algorithms. Preflop heuristic changes V3.6 and V3.6.1 had inconclusive fresh-seed wins and failed to replicate their initial short-stack advantage. The next opportunity is better **strategy representation and decision EV**, not simply lowering a threshold.

## Priority 1 — Offline CFR/Nash-derived preflop strategy tables

**Hypothesis:** Replace coarse score cutoffs with **heads-up, position-, action-, and effective-stack-specific** 169-hand-class strategy probabilities from a solver, while preserving exploitative adaptation and legal bet formatting. Use a small static table (or compact embedded constants) at runtime; the solver itself does **not** run in the tournament sandbox. Focus first on **3–15BB push/fold/call** because full all-in equity gives more trustworthy values here than deep-stack terminal approximation. Rising blinds, antes and effective stacks must be modeled or documented; cash-game 100BB ranges cannot be blindly transplanted.

**Strong candidates to evaluate OFFLINE:**

1. [cRITlamb/poker_solver](https://github.com/cRITlamb/poker_solver) — claims MIT license; heads-up no-limit, precomputed preflop blueprints, 169-class lookup across stack/ante configurations, CLI for short-stack push/fold and joint range-vs-range DCFR, Python reference + Rust core. Uses a Rust build and additional dependencies **offline**; not a permitted direct tournament import. Repository instructions include `poker-solver pushfold --stack 10 --position sb_jam --hand AKs` and `--full-range --json`. Need independent correctness spot checks, license/attribution verification and an artifact extraction script. Its description states deep-stack full-range flop solving takes minutes.
2. [chirenonhive/poker-solver](https://github.com/chirenonhive/poker-solver) — claims MIT license; Python/NumPy CFR+ preflop heads-up solver, exact blocker enumeration, push/fold config `poker-solver solve --stack 12 --push-fold`. **Caution:** the author explicitly says deep-stack non-all-in terminal equities are an optimistic approximation; repo is young and has few independent adopters. Cross-check with a second source and explicit tests.
3. [jensbaagaard/poker-practice](https://github.com/jensbaagaard/poker-practice) — **DO NOT INCORPORATE CODE OR DATA**: the repository's public root did **not** contain an explicit LICENSE file or GitHub license label during the November 21 audit. Our earlier description of it as MIT-licensed was **incorrect/unverified**. Its published 6/8/9-handed ranges are not heads-up solutions anyway. Reading its publicly documented concept is different from copying code or charts; obtain express permission and check dataset provenance before any reuse.

**Engineering:** two-stage architecture `offline solver/trainer -> tiny JSON data/ tables -> safe Python3.10 lookup in bot.py`. Use deterministic per-hand frequency mixing (seeding only public observations) when strategies are mixed; preserve legal total-street bet semantics. Store provenance, date/commit SHA, model parameters and MIT notices if any code/data is incorporated. The rules permit optional `my_bots/uo_monte/data/` files up to **200 MB**, and `bot.py` max **5 MB**. All reads occur at import/warmup if needed, no file writes/threads/external processes/network during play.

**Important risk:** Nash-style approximate ranges are not necessarily maximally exploitative against practice bots; a new chart must beat the baseline in fresh paired freezeouts, not merely look theoretically impressive.

## Priority 2 — Opponent-range-weighted equity and action-value betting

V3.4 includes some river aggression/range approximations, but generic flop/turn branches use random-opponent Monte Carlo. A better design models *conditional* opponent hand probabilities from position, preflop action (open/call/three-bet/four-bet), effective stack, flop/turn bet size, board blockers, draws, showdowns and Bayesian shrinkage for sparse action history. Then estimate **equity versus that range**, rather than versus arbitrary random cards. Evaluate alternative actions using a rough **action-EV** decomposition, including fold probability, equity when called, cost, payout, stack-to-pot ratio and tournament freezeout considerations. This is a much bigger design improvement than a static `equity >= 0.72` betting trigger.

Bound computational budget strictly: precompute ranges/lookup tables, retain existing optimized `eval7` and Monte Carlo runtime where useful, and benchmark on the official 0.5CPU/768MB sandbox. The priority is **calibrated opponent ranges, legal actions and EV ranking**, not expensive online CFR.

## Priority 3 — Offline CFR blueprint for complex postflop

[CFR river reference from noambrown/poker_solver](https://github.com/noambrown/poker_solver) appears MIT-licensed and includes river subgame solving via CFR/CFR+/DCFR in Python/C++. Useful for research on proper river bluff:value proportions and sizing, but may be overkill for today's deadline.

[matteo-psnt/poker-solver](https://github.com/matteo-psnt/poker-solver) has an **unverified license in this audit** and uses pre-trained abstracted poker blueprints and a 3–100BB depth ladder. Its public 100BB blueprint reportedly consumes **1.9GB**—far beyond our 200MB data allowance—so **do not integrate the entire model or its runtime**; inspect algorithms/compact preflop chart ideas only. That repository describes needing many thousands of paired games for reliable improvement evaluation. Availability of a model is not proof it matches our game rules.

The well-known [TexasSolver](https://github.com/bupticybee/TexasSolver) is **AGPL-3.0**, not MIT. Do not represent it as MIT or transplant its source into the submitted bot without a separately cleared license decision. A project's description of solver output does not necessarily establish licensing of every dataset and derivative. Preserve attribution and record the exact third-party file origin and license in any implementation.

## License, organizer-rule and model/data provenance audit — November 21, 2026

**Evidence levels:**
- The **official published starter-kit README** regulates runtime constraints, submission folder, allowed libraries, file/data limits, peeking, collaboration, and cheating. It does **not itself explicitly grant blanket rights to incorporate arbitrary external solver source or charts**. The human teammates reported that the organizers verbally approved *properly licensed open-source research/adaptation and pretrained strategy tables*. That organizer statement is secondhand; clarify specific uncertain cases directly with an organizer, ideally in writing, before adoption.
- Verified exact repository **MIT LICENSE** text at `https://raw.githubusercontent.com/cRITlamb/poker_solver/main/LICENSE`, `https://raw.githubusercontent.com/chirenonhive/poker-solver/main/LICENSE`, and `https://raw.githubusercontent.com/noambrown/poker_solver/master/LICENSE`. MIT normally requires **preserving copyright notices and license permission text with substantial copied portions**, not treating copyright as absent. Check license for the exact selected commit/file, its dependencies and associated tables; repository-wide license alone does not prove ownership or permissions for every embedded asset, pretrained model or third-party dataset.
- `jensbaagaard/poker-practice`: **not verified MIT**, despite an erroneous earlier research note; do not copy or incorporate its JSON charts, source code or assets without a confirmed license or express permission.
- `bupticybee/TexasSolver` prominently states **AGPL-3.0** and separate commercial-license commentary: **excluded from incorporation** pending legal clearance. General high-level ideas such as CFR are not proprietary source code; write our own implementation or use a compatible verified source instead.
- `matteo-psnt/poker-solver` has not had its exact license and any pretrained data rights audited in this check: **unverified, no reuse** until checked.
- **Solver-generated outputs** may have their own provenance, restrictions, third-party inputs or terms; confirm rights before distributing table files in the public tournament repository. Keep a source register with repository URL, exact commit SHA, file path, original author, SPDX license, copied portions, dependencies, output-data rights, notices/attribution, and validation results.

**Mandatory integration gate:** (1) Confirm tournament rules and explicit organizer clarification covers the proposed form of use; (2) confirm all copied code/data and dependencies carry a compatible license/permission and preserve notices; (3) reject sources with unclear ownership, restrictive or unknown licensing, or copied finalist submissions; (4) verify no prohibited imports, network, subprocesses, file writes, threading, hidden-card access, engine edits, or runtime solver work; (5) test official validator and 0.5 CPU / 768MB / 2-second sandbox; (6) show human teammate the exact diff/provenance for approval **before committing/merging/deploying**. If a requirement is uncertain, restrict to **research only**.

No outside algorithm or data artifact has been installed or added to the tournament bot as a result of this research.

## Practical next experiment, not automatic promotion

A. Codex finishes **TASK-CODEX-006 / V3.7** without interruption. If its postflop change is only marginal or hurts fresh holdout, retain committed V3.4.

B. As a next separate scoped task, assess whether an MIT-sourced **offline 169-class SB-vs-BB push/fold/defense table** can be generated and tested quickly. First validate one supported stack depth against at least two solvers or known equilibrium examples. Ensure action mapping for the organizer's blind/ante structure and costs. If feasible, implement a candidate in a clean worktree based on V3.4, **not** on unapproved stacked experiments.

C. Compare baseline vs new table with identical seats/deals over independent dev and holdout seeds, multiple opponent styles (especially aggressive/mixed, not just Caller), shallow/rising blinds, total tournament wins, pair W/D/L and hand-level EV/risk proxies. Record action-change frequency and cases of divergence. Use Claude's independent opponents as further diagnostics. **Never use sealed seeds 1001–1200 for optimization.**

D. In parallel with / after source feasibility, prioritize **range-conditioned postflop equity + action-EV** for the next substantive upgrade. This may be higher strategic upside than chart replacement in deep stacks, but is technically more complex and requires careful opponent-model validation.

**Stop conditions:** no compatible license, untrustworthy/untestable solver data, poor runtime/size behavior, inability to map rules cleanly, or no reproducible improvement. Protect V3.4 as fallback. Deadline **6:30 PM ET**, release checkpoint **5:30 PM ET** and final human approval required for commits/merges/pushes.

## Source status

Public project descriptions checked November 21, 2026; three MIT LICENSE files subsequently checked directly. Mathematical correctness, nested dependencies and strategy-data reuse rights are **not audited or confirmed**. MIT code may require retention of license text/attribution. No third-party code or tables have been incorporated into UO-Monte by this research note.
