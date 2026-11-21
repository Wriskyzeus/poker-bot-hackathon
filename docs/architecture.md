# Tournament-compatible bot architecture

Only `my_bots/uo_monte/bot.py` and optional `data/` are submitted. Keep any runtime helpers in that bot file or otherwise conform to the submission contract. Don't modify `pokercore/` or rely on modules from `src/` that won't be collected.

```text
game_state dictionary / warmup
          |
          v
read street, cards, pot, stack, button, blinds, bet and history
          |
          +--> heads-up preflop ranges and effective stack in bb
          +--> postflop equity (eval7 / treys as permitted)
          +--> pot odds and legal total-street sizing
          +--> opponent stats from match_action_log
          |
          v
decision policy, measured against 2-second budget
          |
          v
return legal {"action": ..., "amount": ... if raising}
```

**Key details:** Button is small blind and acts first preflop; the big blind acts first postflop. Blinds rise every 20 hands. `pot` already includes wagers this street; `raise.amount` is the total bet on this street, not raise-by. `check` while owing money will call, so never use it as a fallback in that case. Use warmup to initialize safely, and seeded `random`/NumPy for reproducible decisions.

**Work split:** Integration teammate focuses on the engine's contract, action legality, runtime, sandbox and submission. Strategy teammate focuses on preflop policy, equity, betting and adaptation. Both evaluate benchmarks and review changes.
