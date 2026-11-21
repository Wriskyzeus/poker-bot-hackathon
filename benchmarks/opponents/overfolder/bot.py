"""BENCHMARK-ONLY practice opponent: the "overfolder". Not part of any submission.

Archetype: a tight, passive player that gives up far too easily. It only
continues against a postflop bet of any real size when it holds two pair or
better, so almost any bet takes the pot away from it. It almost never bluffs
and bets only with a made pair or better.

Why this exists: to test whether a bot gains from fold equity (betting or
bluffing a player who folds too much) without losing chips to a caller.

Why it is a TOY, not a model of the real field: real opponents do not fold
this uniformly, do not ignore bet size or board texture, and do not fold
the same hands in every spot. Beating it by a lot says only that a bot can
exploit an extreme overfolder. It says nothing about tournament win
probability. Do not tune against it alone.

Rules: public state and legal actions only, no hidden cards, no randomness
(same state -> same action), standard library only, no file or network use.
Tunable behaviour lives in PARAMS. Written from scratch for this repo.
"""

RANKS = "23456789TJQKA"

PARAMS = {
    "open_min_tier": 2,            # preflop hands needed to open-raise or call a raise (tier 0-3)
    "open_raise_bb": 2.5,          # open-raise size in big blinds
    "continue_min_strength": 3,    # postflop: need two pair+ to continue against a real bet
    "pressure_floor": 0.25,        # bet/pot below this counts as a small bet
    "small_bet_call_min_strength": 1,   # against a small bet any pair calls
    "bet_min_strength": 2,         # bets only with top pair or better when checked to
    "bet_pot_fraction": 0.4,       # bet size as a fraction of the pot
}


def _rv(card):
    return RANKS.index(card[0]) + 2


def preflop_tier(cards):
    """0 weak .. 3 premium, from the two hole cards only."""
    a, b = sorted((_rv(cards[0]), _rv(cards[1])), reverse=True)
    suited = cards[0][1] == cards[1][1]
    if a == b:
        return 3 if a >= 10 else 2
    if a == 14 and b >= 12:
        return 3
    if a >= 10 and b >= 10:
        return 2
    if a == 14 and suited:
        return 2
    if a == 14 or (suited and b >= 6 and a - b <= 3) or (a >= 8 and a - b == 1):
        return 1
    return 0


def made_strength(cards, board):
    """0 air, 1 weak pair, 2 top pair/overpair, 3 two pair, 4 trips/straight/flush/full house+.
    A hand only counts if at least one hole card is part of it."""
    allc = list(cards) + list(board)
    vals = [_rv(c) for c in allc]
    hole = [_rv(c) for c in cards]
    bvals = [_rv(c) for c in board]
    counts = {}
    for v in vals:
        counts[v] = counts.get(v, 0) + 1
    trips = [v for v, n in counts.items() if n == 3]
    pairs = [v for v, n in counts.items() if n == 2]
    quads = [v for v, n in counts.items() if n == 4]

    suits = {}
    for c in allc:
        suits[c[1]] = suits.get(c[1], 0) + 1
    flush = any(n >= 5 and any(c[1] == s for c in cards) for s, n in suits.items())

    uniq = set(vals)
    if 14 in uniq:
        uniq.add(1)
    straight = False
    for lo in range(1, 11):
        window = set(range(lo, lo + 5))
        if window <= uniq and any(h in window or (h == 14 and 1 in window) for h in hole):
            straight = True

    if flush or straight or any(v in hole for v in quads):
        return 4
    if any(v in hole for v in trips):
        return 4
    if trips and pairs and any(v in hole for v in pairs):
        return 4
    if len(pairs) >= 2 and any(v in hole for v in pairs):
        return 3
    held = [v for v in pairs if v in hole]
    if held:
        return 2 if max(held) >= max(bvals) else 1
    return 0


def _raise_to(state, target):
    """A legal raise to `target` (total street bet), all-in if short, call if we cannot raise."""
    if state["amount_owed"] >= state["your_stack"]:
        return {"action": "call"}
    cap = state["your_bet_this_street"] + state["your_stack"]
    target = max(int(target), state["min_raise_to"])
    if target >= cap:
        return {"action": "all_in"}
    return {"action": "raise", "amount": target}


def _safe(state):
    return {"action": "check"} if state.get("can_check") else {"action": "fold"}


def _preflop(state):
    p = PARAMS
    tier = preflop_tier(state["your_cards"])
    bb = state["blinds"]["bb"]
    owed = state["amount_owed"]
    if state["can_check"]:                       # big blind with the option
        return _raise_to(state, 3 * bb) if tier >= 3 else {"action": "check"}
    if state["current_bet"] <= bb:               # first to act, or facing a limp: open or fold
        if tier >= p["open_min_tier"]:
            return _raise_to(state, p["open_raise_bb"] * bb)
        return {"action": "call"} if (tier >= 1 and owed <= bb // 2) else {"action": "fold"}
    return {"action": "call"} if tier >= p["open_min_tier"] else {"action": "fold"}   # facing a raise


def _postflop(state):
    p = PARAMS
    strength = made_strength(state["your_cards"], state["community_cards"])
    bb = state["blinds"]["bb"]
    pot, owed = state["pot"], state["amount_owed"]
    if owed > 0:
        pressure = owed / max(1, pot - owed)     # bet size relative to the pot before the bet
        need = p["small_bet_call_min_strength"] if pressure < p["pressure_floor"] else p["continue_min_strength"]
        return {"action": "call"} if strength >= need else {"action": "fold"}
    if strength >= p["bet_min_strength"]:
        return _raise_to(state, state["current_bet"] + max(bb, int(pot * p["bet_pot_fraction"])))
    return {"action": "check"}


def decide(game_state: dict) -> dict:
    if game_state.get("type") == "warmup":
        return {"action": "check"}
    try:
        if game_state["street"] == "preflop":
            return _preflop(game_state)
        return _postflop(game_state)
    except Exception:                            # never crash: fall back to the safest legal action
        return _safe(game_state)
