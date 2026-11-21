# UO-Monte V3.4 — Strategy and Algorithms

> This document describes the **released policy**, not an aspirational design brief. Implementation: [`bot.py`](../my_bots/uo_monte/bot.py). For rationale and experimental context, see the [engineering case study](engineering-case-study.md).

## Design objective

Optimize complete **heads-up freezeout** outcomes within the engine's legal-action, time and resource constraints. The policy intentionally trades exact game-theoretic solutions for fast, reproducible and measurable decisions.

## 1. Preflop decisions

`_hand_features()` computes a **heuristic starting-hand score**, considering:

- Pocket pair rank and high/low card strength
- Suitedness and connectedness
- Broadways/high cards

`_preflop()` then considers position, current big blind, remaining stack in big blinds, amount owed, raise size and an opponent-history adjustment. Its responses include opens, calls, folds, value 3-bets and approximate short-stack shove/fold choices.

**Important limitation:** The score is **not hand equity** and the shove/fold rules are **not Nash ranges**. A later V6-P experiment with a 169-class preflop alternative changed more decisions but failed to establish broad improvement.

## 2. Monte Carlo equity

On the flop/turn/river, the function `estimate_equity()` draws legal random opponent hands and any missing community cards from a deck excluding known cards. It evaluates showdown outcomes using `eval7` and counts a tie as half a win.

```text
equity ≈ (wins + 0.5 × ties) / simulations
flop: 320 · turn: 384 · river: 512 simulations
```

This is **equity against a uniformly random opponent hand**, not equity against a perfect opponent-range model. It is a useful approximate input rather than a complete action-selection strategy.

## 3. Betting and defense

- **Pot odds:** With pot `P` already containing current wagers and additional call cost `C`, a simplified break-even threshold is `C / (P + C)`, assuming no later betting.
- **Flop/turn:** `_postflop()` can value bet when estimated equity is high, check without cost, or use `_stack_commitment()` when facing pressure.
- **Commitment:** `_stack_commitment()` considers hand category, live draws, approximate opponent-range strength, stack-to-pot ratio and how many raises occurred.
- **River:** `_river_defense()` compares a call's price with a conditioned estimate. `_river_value_bet()` compares potential bet sizes, weaker calls and raise exposure using possible opponent hole-card combinations.

**Trade-off:** A call's simple pot-odds threshold does not capture all future betting, value lost by forcing a fold, or opponent responses. These approximations were investigated through later experiments.

## 4. Opponent evidence

The bot reads `match_action_log`, the public rolling log of recent actions. `_opponent_history()` uses a **sample-size gate** before adjusting simple preflop tendencies. River logic uses more specific public street-level actions.

It is deliberately conservative: small, noisy samples can easily misclassify an opponent. The bot does **not** see an opponent's folded cards or call a live AI model.

## 5. Why the release stayed at V3.4

The team tested multiple alternative policies: richer opponent tracking, additional 3-bets, defensive thresholds, 169-class preflop rules, adaptive stabs, flop/turn protection betting and a rare terminal all-in price correction.

Some alternatives won more chips in isolated hands, but the outcomes did not generalize reliably. In a frozen holdout comparison, **V6-Protection dropped from V3.4's 63/108 wins to 60/108** and full-match BB/hand declined. The final mathematical fix altered only **three archived decisions** and left a 54-match development comparison tied.

The strongest validated and tournament-submitted policy was therefore **V3.4**. This is a release-quality decision under uncertainty, not a claim that its strategy is optimal.

Read the [case study](engineering-case-study.md), [full experimental archive](testing.md) and [official rules](event-spec.md).
