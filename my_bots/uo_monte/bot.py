"""UO-Monte Version 1: an explainable heads-up preflop policy.

The ranges are coarse heuristics, not a solved/GTO chart.  They trade mixed
strategy precision for fast, reproducible decisions and legal actions.
Postflop remains the starter policy until the equity module is added.
"""

RANKS = "23456789TJQKA"


def _hand_features(cards):
    """Return a bucket score and structural features; score is not equity."""
    first, second = cards
    r1, r2 = RANKS.index(first[0]) + 2, RANKS.index(second[0]) + 2
    high, low = max(r1, r2), min(r1, r2)
    pair = r1 == r2
    suited = first[1] == second[1]
    gap = high - low
    connected = gap == 1
    one_gap = gap == 2
    if pair:
        score = 66 + (high - 2) * 3.2
    else:
        score = high * 3.7 + low * 1.45
        if suited:
            score += 7
        if connected:
            score += 5
        elif one_gap:
            score += 2
        if high == 14:
            score += 4
        if high >= 11 and low >= 10:
            score += 3
    return score, pair, suited, connected, high, low


def _opponent_id(state):
    mine = state.get("your_bot_id")
    for player in state.get("players", []):
        if player.get("bot_id") != mine:
            return player.get("bot_id")
    return None


def _opponent_history(state):
    """Apply a conservative exploit adjustment after 10 observed decisions."""
    opponent = _opponent_id(state)
    actions = [event for event in state.get("match_action_log", [])
               if event.get("bot_id") == opponent and event.get("street") == "preflop"]
    raises = sum(event.get("action") in ("raise", "all_in") for event in actions)
    calls = sum(event.get("action") == "call" for event in actions)
    decisions = raises + calls + sum(event.get("action") == "fold" for event in actions)
    if decisions < 10:
        return 0
    if raises / decisions > 0.35:
        return -3
    if calls / decisions > 0.55:
        return 2
    return 0


def _is_facing_raise(state):
    mine = state.get("your_bot_id")
    return any(event.get("bot_id") != mine
               and event.get("action") in ("raise", "all_in")
               and event.get("street") == "preflop"
               for event in state.get("action_log", []))


def _respond(action, state):
    """Convert a policy choice to an action respecting total-bet semantics."""
    stack = max(0, int(state.get("your_stack", 0)))
    owed = max(0, int(state.get("amount_owed", 0)))
    if stack <= owed:
        return {"action": "all_in"} if stack else {"action": "call"}
    if action == "check" and state.get("can_check"):
        return {"action": "check"}
    if action == "call":
        return {"action": "call"} if owed else {"action": "check"}
    if action == "fold":
        return {"action": "fold"}
    if action == "all_in":
        return {"action": "all_in"}
    target = max(int(state.get("min_raise_to", 0)), int(action))
    affordable_total = int(state.get("your_bet_this_street", 0)) + stack
    if target >= affordable_total:
        return {"action": "all_in"}
    return {"action": "raise", "amount": target}


def _preflop(state):
    cards = state.get("your_cards", [])
    if len(cards) != 2:
        return _respond("check" if state.get("can_check") else "fold", state)
    score, _pair, _suited, _connected, _high, _low = _hand_features(cards)
    bb = max(1, int((state.get("blinds") or {}).get("bb", 1)))
    stack_bb = float(state.get("your_stack", 0)) / bb
    adjustment = _opponent_history(state)
    facing_raise = _is_facing_raise(state)
    button = state.get("seat_to_act") == state.get("button_seat")
    current_bet = int(state.get("current_bet", 0))
    own_bet = int(state.get("your_bet_this_street", 0))

    # Practical shove/fold approximations, not Nash thresholds.
    if stack_bb <= 8:
        if facing_raise:
            cutoff = 68 if stack_bb > 4 else 63
            return _respond("all_in" if score + adjustment >= cutoff else "fold", state)
        cutoff = 49 if button else 56
        return _respond("all_in" if score + adjustment >= cutoff
                        else ("check" if state.get("can_check") else "fold"), state)

    if not facing_raise:
        # Heads-up button == small blind and acts first preflop.
        cutoff = (43 if button else 49) + adjustment
        if score >= cutoff:
            size_bb = 2.2 if button else 2.5
            # The API wants the total street bet, so 2.2bb means 220 chips,
            # not the current 1bb plus another 2.2bb.
            target = int(round(size_bb * bb))
            return _respond(target, state)
        return _respond("check" if state.get("can_check") else "fold", state)

    # Current bet and prior actions determine price/pressure.
    raise_increment = max(bb, current_bet - max(own_bet, bb if not button else 0))
    raise_multiple = current_bet / float(bb)
    owed = int(state.get("amount_owed", 0))
    pot = int(state.get("pot", 0))
    price = owed / float(max(1, pot + owed))
    pressure = (5 if raise_multiple >= 4 else 0) + (4 if raise_increment >= 4 * bb else 0)
    value_3bet = 77 + pressure - adjustment
    call_cutoff = 50 + pressure - adjustment
    if stack_bb <= 15:
        value_3bet = 70 + pressure - adjustment
        call_cutoff = 57 + pressure - adjustment
        if score >= value_3bet:
            return _respond("all_in", state)
    elif score >= value_3bet:
        multiplier = 3.0 if button else 3.5
        target = max(int(state.get("min_raise_to", 0)), int(round(current_bet * multiplier)))
        return _respond(target, state)
    # Price only widens the bottom of the calling bucket; it does not replace
    # range/equity reasoning.
    if score >= call_cutoff or (price <= 0.20 and score >= call_cutoff - 5):
        return _respond("call", state)
    return _respond("fold", state)


def decide(game_state: dict) -> dict:
    if game_state.get("type") == "warmup":
        return {"action": "check"}
    if game_state.get("street") == "preflop":
        return _preflop(game_state)

    # Preserve the baseline postflop policy, with legal all-in handling and no
    # check while chips are owed.
    pot = int(game_state.get("pot", 0))
    owed = int(game_state.get("amount_owed", 0))
    if not owed and game_state.get("can_check"):
        return {"action": "check"}
    if owed and int(game_state.get("your_stack", 0)) <= owed:
        return {"action": "all_in"}
    if owed <= pot * 0.25:
        return {"action": "call"}
    return {"action": "fold"}
