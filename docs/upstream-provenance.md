# Source provenance and attribution

The repository combines the **official tournament development kit** with the team's own autonomous decision policy.

## Official upstream components

- **Source:** [FreddyyAndrews/poker-hackathon-kit](https://github.com/FreddyyAndrews/poker-hackathon-kit)
- **License:** [MIT](../LICENSE) (upstream notices retained)
- **Imported:** November 21, 2026
- **Preserved official components:** `CORE_VERSION`, `.kit-files`, `LICENSE`, `Makefile`, `requirements.txt`, `play.py`, `bots/`, `pokercore/` and starter documentation.
- The organizers' original README is archived at [`official-starter-kit.md`](official-starter-kit.md).

## UO-Monte team implementation

The team began with the starter template, then built a distinct **V3.4** strategy in [`my_bots/uo_monte/bot.py`](../my_bots/uo_monte/bot.py), including stack-aware preflop rules, `eval7` showdown equity simulations, postflop pot-commitment decisions, river-specific logic and conservative use of public opponent actions.

- **Release checkpoint:** `a5ea561ff5b70d5a17533579bfc6557b2979622b`
- **Released `bot.py` Git blob:** `27acb669ee3ac35172a88293c198182b56db0f78`
- **Official engine code:** Unmodified, including the `pokercore/` runtime used to test the bot.
- **Evaluation:** Team-authored regression tests, reproducible seeded match experiments and additional adversarial benchmarks. See [evaluation notes](engineering-case-study.md).

Development used coding assistants for implementation and analysis. The released bot performs **no live network calls or AI model inference**. Any third-party licensed reference tools explored during research are not silently implied to be part of the submitted policy.

## Reuse

The upstream engine and kit remain under the bundled MIT license. Check original licenses and attribution requirements before redistributing third-party tools or datasets. This document distinguishes team-authored strategy code from organizer-provided tournament infrastructure.

Historical documents in this repository may reference the **initial template state**; the final public `main` submission is V3.4, not that template.
