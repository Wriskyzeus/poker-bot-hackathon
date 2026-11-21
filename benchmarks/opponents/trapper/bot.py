"""BENCHMARK-ONLY practice opponent: the "trapper". Not part of any submission.

Archetype: a value-heavy player that never bluffs. It slowplays strong hands
(limps premium hands before the flop, checks and calls on the flop and turn
with strong made hands) and then punishes bets with large raises or big
river bets. Everything else is played straightforwardly and cautiously.

Why this exists: to test whether a bot's semi-bluffs and thin value bets get
punished by a player who is "waiting" with strong hands, and whether the bot
loses too many chips to check-raises.

Why it is a TOY, not a model of the real field: it never bluffs, follows fixed
bet-size thresholds and slowplays by street rather than by board texture or
history. Real strong opponents mix bluffs and vary their lines. Results against
it say nothing about tournament win probability. Do not tune against it alone.

Rules: public state and legal actions only, no hidden cards, no randomness
(same state -> same action), standard library only, no file or network use.
Tunable behaviour lives in PARAMS. Written from scratch for this repo.
"""

RANKS = "23456789TJQKA"

PARAMS = {
    "limp_trap_preflop": True,       # premium hands call instead of raising when first to act
    "preflop_value_raise_bb": 3.0,   # big blind with the option and a premium hand raises to this
    "preflop_reraise_mult": 3.0,     # premium hand re-raises a raise to this multiple of the bet
    "preflop_reraise_cap_bb": 12,    # ...but only if the bet being faced is at most this many big blinds
    "preflop_call_cap_bb": 4,        # medium hands call raises up to this many big blinds
    "slowplay_streets": ("flop",),   # streets on which strong hands check and call
    "monster_raise_mult": 3.0,       # raise to this multiple of the bet once the trap is sprung
    "river_bet_fraction": 0.9,       # monster river bet, as a fraction of the pot
    "strong_bet_fraction": 0.7,      # strong (two pair) hand bet after the slowplay street
    "value_bet_fraction": 0.5,       # top pair bets this fraction of the pot
    "top_pair_max_call": 0.8,        # top pair calls bets up to this fraction of the pot (0.5 on the river)
    "weak_pair_max_call": 0.25,      # weak pair calls only small bets
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
    owed, bet = state["amount_owed"], state["current_bet"]
    if state["can_check"]:                       # big blind with the option
        return _raise_to(state, p["preflop_value_raise_bb"] * bb) if tier >= 3 else {"action": "check"}
    if bet <= bb:                                # first to act, or facing a limp
        if tier >= 3:
            return {"action": "call"} if p["limp_trap_preflop"] else _raise_to(state, 3 * bb)
        return {"action": "call"} if (tier >= 1 and owed <= bb // 2) or tier == 2 else {"action": "fold"}
    if tier >= 3:                                # facing a raise: spring the trap
        if bet <= p["preflop_reraise_cap_bb"] * bb:
            return _raise_to(state, bet * p["preflop_reraise_mult"])
        return {"action": "call"}
    if tier == 2 and bet <= p["preflop_call_cap_bb"] * bb:
        return {"action": "call"}
    return {"action": "fold"}


def _postflop(state):
    p = PARAMS
    strength = made_strength(state["your_cards"], state["community_cards"])
    street = state["street"]
    pot, owed, bet = state["pot"], state["amount_owed"], state["current_bet"]
    bb = state["blinds"]["bb"]
    slow = street in p["slowplay_streets"]
    pressure = owed / max(1, pot - owed) if owed > 0 else 0.0

    if owed > 0:                                  # facing a bet
        if strength >= 4:
            return {"action": "call"} if slow else _raise_to(state, bet * p["monster_raise_mult"])
        if strength == 3:
            return {"action": "fold"} if (street == "river" and pressure > 1.0) else {"action": "call"}
        if strength == 2:
            limit = 0.5 if street == "river" else p["top_pair_max_call"]
            return {"action": "call"} if pressure <= limit else {"action": "fold"}
        if strength == 1:
            return {"action": "call"} if pressure <= p["weak_pair_max_call"] else {"action": "fold"}
        return {"action": "fold"}                 # air never calls and never bluffs

    if strength >= 4:                             # checked to us
        if slow:
            return {"action": "check"}
        return _raise_to(state, bet + max(bb, int(pot * p["river_bet_fraction"])))
    if strength == 3:
        if slow:
            return {"action": "check"}
        return _raise_to(state, bet + max(bb, int(pot * p["strong_bet_fraction"])))
    if strength == 2:
        return _raise_to(state, bet + max(bb, int(pot * p["value_bet_fraction"])))
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
