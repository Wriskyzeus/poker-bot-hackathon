"""UO-Monte 3.2: preflop ranges, stack-aware postflop play, and river defense.

The ranges are coarse heuristics, not a solved/GTO chart.  They trade mixed
strategy precision for fast, reproducible decisions and legal actions.
When facing a river bet, weight exact showdown outcomes by the opponent's
observed aggression and the current betting line.
"""

import random
from bisect import bisect_left, bisect_right
from itertools import combinations

import eval7


RANKS = "23456789TJQKA"
SUITS = "shdc"
POSTFLOP_SIMULATIONS = {"flop": 320, "turn": 384, "river": 512}


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
    # Preserve the policy's intent before applying stack-size normalization.
    # In particular, a fold must never become an all-in call when covered.
    if action == "fold":
        return {"action": "fold"}
    if action == "check":
        return {"action": "check"} if state.get("can_check") else {"action": "call"}
    if action == "call":
        return {"action": "call"} if owed else {"action": "check"}
    if action == "all_in":
        return {"action": "all_in"}
    if stack <= owed:
        return {"action": "all_in"} if stack else {"action": "call"}
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


def _card_strings(cards):
    """Normalize card strings without relying on engine-internal card objects."""
    return [str(card) for card in cards]


def _remaining_cards(known):
    known = set(known)
    return [rank + suit for rank in RANKS for suit in SUITS
            if rank + suit not in known]


def _sample_runout(hole_cards, community_cards, rng):
    """Draw opponent hole cards and the missing board cards without overlap."""
    known = _card_strings(hole_cards) + _card_strings(community_cards)
    available = _remaining_cards(known)
    draw_count = 2 + max(0, 5 - len(community_cards))
    drawn = rng.sample(available, draw_count)
    opponent = drawn[:2]
    board = _card_strings(community_cards) + drawn[2:]
    return opponent, board


def estimate_equity(hole_cards, community_cards, simulations=POSTFLOP_SIMULATIONS["flop"], seed=0):
    """Estimate showdown equity versus one uniformly random opponent hand.

    Each trial samples two opponent cards plus enough unseen board cards to
    reach five, then evaluates both seven-card hands with eval7. Ties count as
    half a win. The finite sample count is intentionally bounded for the
    tournament decision deadline; it is not exact equity and does not model a
    betting range.
    """
    hole_cards = _card_strings(hole_cards)
    community_cards = _card_strings(community_cards)
    if len(hole_cards) != 2 or not 3 <= len(community_cards) <= 5:
        raise ValueError("postflop equity requires two hole cards and a 3-5 card board")
    if len(set(hole_cards + community_cards)) != len(hole_cards) + len(community_cards):
        raise ValueError("known cards must be unique")
    simulations = max(1, min(int(simulations), 4096))
    hero = [eval7.Card(card) for card in hole_cards]
    wins = 0.0
    rng = random.Random(int(seed))
    for _ in range(simulations):
        opponent, board = _sample_runout(hole_cards, community_cards, rng)
        board_cards = [eval7.Card(card) for card in board]
        hero_score = eval7.evaluate(hero + board_cards)
        villain_score = eval7.evaluate(
            [eval7.Card(card) for card in opponent] + board_cards
        )
        if hero_score > villain_score:
            wins += 1.0
        elif hero_score == villain_score:
            wins += 0.5
    return wins / simulations


def _state_seed(state):
    """Build a reproducible seed without clock/process-randomized hashing."""
    text = "|".join(_card_strings(state.get("your_cards", []))
                    + _card_strings(state.get("community_cards", [])))
    text += "|" + str(state.get("hand_num", 0)) + "|" + str(state.get("street", ""))
    return sum((index + 1) * ord(char) for index, char in enumerate(text))


def _value_bet_target(state, equity):
    """Choose a modest total-street value bet when checking is free."""
    pot = max(1, int(state.get("pot", 0)))
    minimum = int(state.get("min_raise_to", 0))
    # 60% pot is an intentionally simple value size; _respond enforces the
    # engine's minimum and converts an unaffordable intended raise to all-in.
    return max(minimum, int(round(pot * 0.60)))


def _river_aggression(state, opponent):
    """Shrink river aggression toward earlier streets and a cautious prior.

    Count the first voluntary decision per street per hand. A small window
    of repeated raises in a single pot should not make a player look loose.
    Match history has revealed hole cards but no historical boards, so it
    cannot reliably label a showdown as a bluff.
    """
    counts = {"flop": [0, 0], "turn": [0, 0], "river": [0, 0]}
    seen = set()
    for event in state.get("match_action_log", []):
        street = event.get("street")
        hand = event.get("hand_num")
        action = event.get("action")
        if (opponent is None or event.get("bot_id") != opponent
                or street not in counts or hand is None
                or hand == state.get("hand_num")
                or action not in ("check", "call", "fold", "raise", "all_in")
                or (hand, street) in seen):
            continue
        seen.add((hand, street))
        counts[street][0] += action in ("raise", "all_in")
        counts[street][1] += 1

    flop_bets, flop_chances = counts["flop"]
    turn_bets, turn_chances = counts["turn"]
    river_bets, river_chances = counts["river"]
    earlier = (2 + flop_bets + turn_bets) / (8 + flop_chances + turn_chances)
    return (4 * earlier + river_bets) / (4 + river_chances)


def _river_range_equity(state):
    """Return equity against the betting range and a tighter raise-calling range."""
    hole = _card_strings(state.get("your_cards", []))
    board = _card_strings(state.get("community_cards", []))
    if len(hole) != 2 or len(board) != 5 or len(set(hole + board)) != 7:
        return 0.0, 0.0
    community = [eval7.Card(card) for card in board]
    hero = eval7.evaluate(community + [eval7.Card(card) for card in hole])
    deck = [eval7.Card(card) for card in _remaining_cards(hole + board)]
    ranks = sorted(eval7.evaluate(community + [a, b]) for a, b in combinations(deck, 2))
    losses_end = bisect_left(ranks, hero)
    ties_end = bisect_right(ranks, hero)

    def equity_from(start):
        wins = max(0, losses_end - start)
        ties = max(0, ties_end - max(start, losses_end))
        return (wins + 0.5 * ties) / (len(ranks) - start)

    opponent = _opponent_id(state)
    aggression = _river_aggression(state, opponent)
    opponent_raises = [
        action for action in state.get("action_log", [])
        if action.get("bot_id") == opponent and action.get("action") in ("raise", "all_in")
    ]
    street_raises = sum(action.get("street") == "river"
                        and action.get("action") in ("raise", "all_in")
                        for action in state.get("action_log", []))
    barrels = len({action.get("street") for action in opponent_raises
                   if action.get("street") in ("flop", "turn")})
    owed = state["amount_owed"]
    size = owed / max(1, state["pot"] - owed)
    pressure = min(1.0, 0.35 * max(0, street_raises - 1) + 0.18 * barrels
                   + 0.28 * max(0.0, size - 0.5))
    # Frequent aggression broadens both the value cutoff and the unfiltered
    # component. It is a proxy for bluffs and thin bets, not a bluff count.
    broad_weight = min(0.90, max(0.08, 1.55 * aggression - 0.12 - 0.35 * pressure))
    value_width = max(0.08, 0.16 + 0.42 * aggression - 0.20 * pressure)
    value_equity = equity_from(int((1 - value_width) * len(ranks)))
    continuing = equity_from(int((1 - value_width * 0.5) * len(ranks)))
    return broad_weight * equity_from(0) + (1 - broad_weight) * value_equity, continuing


def _river_defense(state):
    owed = state["amount_owed"]
    stack = state["your_stack"]
    paid = min(stack, owed)
    # The pot already includes the outstanding bet. Excess chips are returned
    # when an all-in call cannot cover that bet.
    pot = max(0, state["pot"] - (owed - paid))
    price = paid / max(1, pot + paid)
    equity, raise_equity = _river_range_equity(state)
    if equity < price + 0.02:
        return _respond("fold", state)
    if stack > owed and raise_equity >= 0.70:
        return _respond(int(round((pot + paid) * 0.65)), state)
    return _respond("call", state)


def _commitment_hand(hole, board, score):
    """Distinguish hole-card strength from strength supplied by the board."""
    category = eval7.handtype(score)
    ranks = [card[0] for card in hole]
    board_ranks = [card[0] for card in board]
    high = max(board_ranks, key=RANKS.index)
    if category == "Three of a Kind" or category == "Trips":
        if ranks[0] == ranks[1] and board_ranks.count(ranks[0]) == 1:
            return "set"
        return "trips" if any(board_ranks.count(rank) == 2 for rank in ranks) else "board"
    if category == "Two Pair" and all(rank in board_ranks for rank in ranks) and ranks[0] != ranks[1]:
        return "two pair"
    if category in ("Pair", "Two Pair"):
        if ranks[0] == ranks[1] and RANKS.index(ranks[0]) > RANKS.index(high):
            return "overpair"
        if high in ranks and board_ranks.count(high) == 1:
            return "top pair"
        if ranks[0] == ranks[1] or any(rank in board_ranks for rank in ranks):
            return "pair"
        return "board"
    return category.lower()


def _live_draw(hole, board):
    """Detect a hole-card flush draw or a straight draw with two rank outs."""
    if any(sum(card[1] == suit for card in hole + board) == 4
           and any(card[1] == suit for card in hole) for suit in SUITS):
        return True
    board_ranks = {card[0] for card in board}
    known = board_ranks | {card[0] for card in hole}
    order = "A" + RANKS
    outs = set()
    for index in range(len(order) - 4):
        window = set(order[index:index + 5])
        missing = window - known
        if len(missing) == 1 and window & (known - board_ranks):
            outs.update(missing)
    return len(outs) >= 2


def _commitment_equity(state, hero, board, deck, broad_weight, width):
    """Sample runouts against a broad range and its stronger made-hand tail."""
    ranked = [(eval7.evaluate(board + list(pair)), pair) for pair in combinations(deck, 2)]
    ranked.sort(key=lambda entry: entry[0])
    cutoff = ranked[int(len(ranked) * (1 - width))][0]
    pairs = [pair for _, pair in ranked]
    value_pairs = [pair for score, pair in ranked if score >= cutoff]
    rng = random.Random(_state_seed(state))
    samples = POSTFLOP_SIMULATIONS[state["street"]] // 2

    def equity(pool):
        points = 0.0
        for _ in range(samples):
            first, second = rng.choice(pool)
            runout = rng.sample(deck, 4 if len(board) == 3 else 3)
            runout = [card for card in runout if card != first and card != second]
            community = board + runout[:5 - len(board)]
            ours = eval7.evaluate(community + hero)
            theirs = eval7.evaluate(community + [first, second])
            points += (ours > theirs) + 0.5 * (ours == theirs)
        return points / samples

    broad = equity(pairs)
    value = equity(value_pairs)
    return broad_weight * broad + (1 - broad_weight) * value, value


def _stack_commitment(state, owed, pot):
    hole = _card_strings(state["your_cards"])
    board = _card_strings(state["community_cards"])
    hero = [eval7.Card(card) for card in hole]
    community = [eval7.Card(card) for card in board]
    hand = _commitment_hand(hole, board, eval7.evaluate(hero + community))
    draw = _live_draw(hole, board)

    opponent = _opponent_id(state)
    opponent_stack = next((p.get("stack") for p in state.get("players", [])
                           if p.get("bot_id") == opponent), None)
    own_stack = state["your_stack"]
    effective = own_stack if opponent_stack is None else min(own_stack, opponent_stack + owed)
    paid = min(owed, own_stack)
    contestable = max(1, pot - (owed - paid) + paid)
    spr = (effective - paid) / contestable
    fraction = paid / max(1, effective)
    price = paid / contestable

    aggression = _river_aggression(state, opponent)
    actions = state.get("action_log", [])
    raises = sum(a.get("street") == state["street"] and a.get("action") in ("raise", "all_in")
                 for a in actions)
    earlier_bet = any(a.get("bot_id") == opponent and a.get("street") == "flop"
                      and a.get("action") in ("raise", "all_in") for a in actions)
    pressure = min(1.0, 0.26 * max(0, raises - 1) + 0.13 * (earlier_bet and state["street"] == "turn")
                   + 0.60 * max(0, price - 0.22) + 0.40 * max(0, fraction - 0.25))
    broad = min(0.96, max(0.15, 0.80 + 0.30 * aggression - pressure * (0.72 - 0.48 * aggression)))
    width = max(0.10, 0.22 + 0.43 * aggression - 0.17 * pressure)
    deck = [eval7.Card(card) for card in _remaining_cards(hole + board)]
    equity, value_equity = _commitment_equity(state, hero, community, deck, broad, width)

    strong = hand in ("set", "straight", "flush", "full house", "quads", "straight flush")
    pair = hand in ("top pair", "overpair")
    two_pair = hand in ("two pair", "trips")
    # Calls preserve bluff-catching. Extra caution applies when a marginal
    # made hand risks a large fraction of a stack after repeated aggression.
    margin = 0.05 + 0.12 * pressure * (1 - aggression)
    if (pair or two_pair) and raises >= 2 and fraction >= 0.35:
        margin += 0.12 * (1 - aggression)
    if draw and spr <= 0.5:
        margin -= 0.025
    if equity < price + margin:
        return _respond("fold", state)

    can_raise = effective > owed and (opponent_stack is None or opponent_stack > 0)
    value_raise = (
        strong and value_equity >= (0.62 if raises < 2 else 0.72)
        or two_pair and raises < 2 and value_equity >= 0.65
        or pair and raises <= 1 and spr <= 0.65 and value_equity >= 0.58
    )
    if can_raise and value_raise:
        proposed = max(state["min_raise_to"], round((pot + paid) * 0.65))
        effective_target = state["your_bet_this_street"] + effective
        if effective_target >= state["min_raise_to"]:
            return _respond(min(proposed, effective_target), state)
        if own_stack == effective:
            return _respond("all_in", state)
    return _respond("call", state)


def _postflop(state):
    owed = max(0, int(state.get("amount_owed", 0)))
    pot = max(0, int(state.get("pot", 0)))
    street = state.get("street")
    if street == "river" and owed:
        return _river_defense(state)
    if street in ("flop", "turn") and owed and state.get("action_log"):
        return _stack_commitment(state, owed, pot)
    simulations = POSTFLOP_SIMULATIONS.get(street, POSTFLOP_SIMULATIONS["river"])
    equity = estimate_equity(
        state.get("your_cards", []), state.get("community_cards", []),
        simulations=simulations, seed=_state_seed(state),
    )

    if not owed and state.get("can_check"):
        # No fold equity is assumed: only bet for clear value.
        if equity >= 0.72 and int(state.get("your_stack", 0)) > 0:
            return _respond(_value_bet_target(state, equity), state)
        return {"action": "check"}

    if owed:
        pot_odds = owed / float(max(1, pot + owed))
        # Random-hand equity is optimistic against a raiser, so require a
        # margin before continuing. This remains a price heuristic, not GTO.
        required_equity = min(0.98, pot_odds + 0.08)
        if equity >= required_equity:
            # Value raise only with a substantial edge and enough chips left;
            # otherwise call and preserve the fold option when the price is bad.
            if equity >= 0.78 and int(state.get("your_stack", 0)) > owed:
                target = max(int(state.get("min_raise_to", 0)), int(round((pot + owed) * 0.65)))
                return _respond(target, state)
            return _respond("call", state)
        return _respond("fold", state)

    # Defensive fallback for malformed/incomplete state: never check while
    # owed, but otherwise keep the action legal and conservative.
    return _respond("check", state)


def decide(game_state: dict) -> dict:
    if game_state.get("type") == "warmup":
        return {"action": "check"}
    if game_state.get("street") == "preflop":
        return _preflop(game_state)

    return _postflop(game_state)
