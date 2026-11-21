"""BENCHMARK-ONLY practice opponent "rangebot" (TASK-CLAUDE-007). Not part of any submission.

A structurally different adversary from the TASK-006 family (it shares no code with the earlier five-bot family):
those bots map hand CATEGORIES to actions through lookup tables; this one reasons with EQUITY AGAINST A
RANGE ESTIMATE, using eval7 Monte Carlo on the public state only.

  * Preflop: ranks hands by equity-vs-random, defends the big blind by the MINIMUM-DEFENCE FREQUENCY implied
    by the open size (re-derived from the pot, not hard-coded), 3-bets value plus Ace-blocker bluffs at
    roughly a 2:1 value:bluff ratio, mixes limp / 2x / 2.5x / 3x opening sizes, 4-bets, and shoves/calls by
    effective stack with equity against an assumed jam range.
  * Postflop: narrows the opponent's range from the bet size and street (bigger bet = tighter range, judged by
    the hand's strength on the CURRENT board plus some draws), then calls when equity beats the pot-odds price,
    value-raises strong hands, check-raises (OOP) at times, and bluff-raises rarely.
  * When it bets: value if equity against a "calling range" is high; bluffs with weak hands that have draw
    potential or blockers, at a frequency set by the bet size (b = s/(1+2s) of its bets are bluffs);
    sizes vary with board wetness and street (0.33 .. 1.4x pot).

Designed stress test, NOT an equilibrium strategy and not a forecast of tournament opponents. Known simple
spots: crude range narrowing, no memory across hands (it does not adapt), no reads on the opponent.
Rules: public game_state only; own hole cards and board are the only cards used; deterministic (hash-seeded);
imports limited to eval7, random, zlib; no file/network/process use. Written from scratch for this repo.
"""

import random
import zlib

import eval7

RANKS = "23456789TJQKA"
SUITS = "cdhs"
ALL_CARDS = [r + s for r in RANKS for s in SUITS]
ALL_E7 = {c: eval7.Card(c) for c in ALL_CARDS}


# ------------------------------------------------------------------ preflop strength table
def _class_of(a, b):
    ra, rb = RANKS.index(a[0]), RANKS.index(b[0])
    if ra < rb:
        a, b, ra, rb = b, a, rb, ra
    if ra == rb:
        return a[0] + b[0]
    return a[0] + b[0] + ("s" if a[1] == b[1] else "o")


def _build_table():
    """equity-vs-random for each of the 169 classes (fixed-seed Monte Carlo, ~0.3 s at import)."""
    rng = random.Random(20261121)
    classes = {}
    for i in range(52):
        for j in range(i + 1, 52):
            classes.setdefault(_class_of(ALL_CARDS[i], ALL_CARDS[j]), []).append((ALL_CARDS[i], ALL_CARDS[j]))
    eqs = {}
    for cl, combos in classes.items():
        h = combos[0]
        deck = [c for c in ALL_CARDS if c not in h]
        w = 0.0
        n = 900
        for _ in range(n):
            s = rng.sample(deck, 7)
            a = eval7.evaluate([ALL_E7[h[0]], ALL_E7[h[1]]] + [ALL_E7[c] for c in s[2:]])
            b = eval7.evaluate([ALL_E7[s[0]], ALL_E7[s[1]]] + [ALL_E7[c] for c in s[2:]])
            w += 1.0 if a > b else 0.5 if a == b else 0.0
        eqs[cl] = w / n
    order = sorted(classes, key=lambda c: eqs[c])
    total = sum(len(classes[c]) for c in order)
    rank = {}
    run = 0
    for c in order:
        rank[c] = (run + len(classes[c]) / 2.0) / total      # 0 = worst .. 1 = best (combo-weighted)
        run += len(classes[c])
    return eqs, rank


_PF_EQ, _PF_RANK = _build_table()


def _pf_rank(cards):
    return _PF_RANK[_class_of(cards[0], cards[1])]


# ------------------------------------------------------------------------------ helpers
def _canon_hand(state):
    """Canonical hand key for the hash-based "chance": depends only on the hand NUMBER, never on the runner's
    match id or on either bot's name/version, so two hero versions face identical opponent choices in identical
    spots. The "local_h%04d" form reproduces the ids the official play.py produces."""
    n = state.get("hand_num")
    if n is None:
        n = int(str(state["hand_id"]).rsplit("_h", 1)[-1])
    return "local_h%04d" % n


def _rng(state, salt):
    key = "%s|%s|%s|%s|%d" % (_canon_hand(state), ",".join(state["your_cards"]), ",".join(state["community_cards"]),
                               salt, len(state["action_log"]))
    return random.Random(zlib.crc32(key.encode()))


def _view(state):
    me = state["seat_to_act"]
    opp = [p for p in state["players"] if p["seat"] != me][0]
    bb = state["blinds"]["bb"]
    eff = min(state["your_stack"] + state["your_bet_this_street"], opp["stack"] + opp["bet_this_street"]) / float(bb)
    pre = [e for e in state["action_log"] if e["street"] == "preflop"]
    nraise = sum(1 for e in pre if e["action"] in ("raise", "all_in"))
    last_raiser = [e["seat"] for e in pre if e["action"] in ("raise", "all_in")]
    return {"me": me, "bb": bb, "eff": eff, "nraise": nraise,
            "ip": state["sb_seat"] == me,
            "aggr": bool(last_raiser) and last_raiser[-1] == me,
            "ante": state["blinds"]["ante"] / float(bb)}


def _raise_to(state, target):
    if state["amount_owed"] >= state["your_stack"]:
        return {"action": "call"}
    cap = state["your_bet_this_street"] + state["your_stack"]
    target = int(max(target, state["min_raise_to"]))
    if target >= cap or cap - target < state["blinds"]["bb"]:
        return {"action": "all_in"}
    return {"action": "raise", "amount": target}


def _bet_pot(state, frac):
    return _raise_to(state, state["current_bet"] + max(state["blinds"]["bb"], int(state["pot"] * frac)))


def _fold_or_check(state):
    return {"action": "check"} if state["can_check"] else {"action": "fold"}


def _sample_villain(rng, dead, board, count, top_q, preflop):
    """Villain hands consistent with the dead cards. Postflop the 'range' is the top `top_q` of random hands
    by strength on the CURRENT board (plus ~15% unfiltered hands to represent draws/bluffs)."""
    deck = [c for c in ALL_CARDS if c not in dead]
    pool = []
    tries = 0
    while len(pool) < count * (1 if preflop else 4) and tries < 4000:
        tries += 1
        a, b = rng.sample(deck, 2)
        pool.append((a, b))
    if preflop or not board:
        return pool[:count]
    bd = [ALL_E7[c] for c in board]
    scored = sorted(pool, key=lambda h: eval7.evaluate([ALL_E7[h[0]], ALL_E7[h[1]]] + bd))
    keep = int(len(scored) * top_q)
    strong = scored[len(scored) - max(keep, 1):]
    loose = scored[:max(1, int(len(scored) * 0.15))]
    rng.shuffle(loose)
    mix = strong[:max(1, int(count * 0.85))] + loose[:max(1, int(count * 0.15))]
    rng.shuffle(mix)
    return mix[:count]


def _equity(rng, hole, board, villains):
    """MC equity of `hole` vs the sampled villain hands, one random runout each."""
    hh = [ALL_E7[c] for c in hole]
    bd = [ALL_E7[c] for c in board]
    w = 0.0
    n = 0
    for v in villains:
        used = set(hole) | set(board) | set(v)
        need = 5 - len(board)
        deck = [c for c in ALL_CARDS if c not in used]
        run = [ALL_E7[c] for c in rng.sample(deck, need)] if need else []
        a = eval7.evaluate(hh + bd + run)
        b = eval7.evaluate([ALL_E7[v[0]], ALL_E7[v[1]]] + bd + run)
        w += 1.0 if a > b else 0.5 if a == b else 0.0
        n += 1
    return w / max(1, n)


def _draw_potential(rng, hole, board):
    """How much equity-vs-random rises on average when one more board card arrives (flop/turn only)."""
    if len(board) >= 5 or len(board) < 3:
        return 0.0
    base_v = _sample_villain(rng, set(hole) | set(board), board, 40, 1.0, False)
    base = _equity(rng, hole, board, base_v)
    deck = [c for c in ALL_CARDS if c not in set(hole) | set(board)]
    gain = 0.0
    k = 8
    for c in rng.sample(deck, k):
        b2 = board + [c]
        v = _sample_villain(rng, set(hole) | set(b2), b2, 14, 1.0, False)
        gain += _equity(rng, hole, b2, v)
    return gain / k - base


def _wetness(board):
    suits = {}
    for c in board:
        suits[c[1]] = suits.get(c[1], 0) + 1
    vals = sorted(RANKS.index(c[0]) for c in board)
    conn = sum(1 for a, b in zip(vals, vals[1:]) if b - a <= 2)
    return (1 if max(suits.values()) >= 2 else 0) + (1 if max(suits.values()) >= 3 else 0) + (1 if conn >= 2 else 0)


# ------------------------------------------------------------------------------ preflop
def _mdf_vs_steal(open_bb, ante):
    """Minimum-defence frequency of the BB against an SB open of `open_bb` big blinds (derived from pot sizes)."""
    pot_before = 2 * ante + 1.5
    add = open_bb - 0.5
    return pot_before / (pot_before + add)


def _jam_freq(eff):
    return max(0.40, min(0.85, 0.96 - 0.037 * eff))


def _preflop(state, v):
    rng = _rng(state, "pre")
    u = rng.random()
    rank = _pf_rank(state["your_cards"])
    bb = v["bb"]
    eff = v["eff"]
    owed, bet = state["amount_owed"], state["current_bet"]
    ace_blocker = any(c[0] == "A" for c in state["your_cards"])
    suited = state["your_cards"][0][1] == state["your_cards"][1][1]
    first_in = (state["sb_seat"] == v["me"]) and v["nraise"] == 0 and bet <= bb

    if eff <= 12:                                          # push/fold by effective stack, with equity vs a range
        jf = _jam_freq(eff)
        if first_in:
            return {"action": "all_in"} if rank >= 1 - jf else {"action": "fold"}
        if v["nraise"] >= 1:
            call_amount = owed / float(max(1, state["your_stack"] + state["your_bet_this_street"]))
            pot = state["pot"]
            req = owed / float(pot + owed)
            vill = _sample_villain(rng, set(state["your_cards"]), [], 90, 1.0, True)
            vill = [h for h in vill if _pf_rank(h) >= 1 - jf][:60] or vill[:30]
            eq = _equity(rng, state["your_cards"], [], vill)
            if eq >= req + (0.02 if call_amount > 0.5 else 0.05):
                return {"action": "call"}
            return {"action": "fold"}
        return {"action": "all_in"} if rank >= 0.82 else _fold_or_check(state)

    if first_in:                                            # button: mixed sizes, a limp slice, ~75% opens
        if rank < 0.25:
            return {"action": "fold"}
        if rank < 0.33 and u < 0.45:
            return {"action": "call"}                       # complete the small blind
        size = 2.0 if u < 0.3 else 2.5 if u < 0.7 else 3.0
        return _raise_to(state, size * bb)
    if v["nraise"] == 0:                                    # BB: option after a limp
        if state["can_check"]:
            return _raise_to(state, 3.5 * bb) if (rank > 0.85 or (ace_blocker and suited and u < 0.25)) else {"action": "check"}
        return {"action": "call"}
    if v["nraise"] == 1:                                    # BB facing an open (or SB facing a BB raise-over-limp)
        open_bb = bet / float(bb)
        mdf = _mdf_vs_steal(open_bb, v["ante"])
        defend = min(0.85, mdf * 1.08)
        if rank >= 1 - 0.10:                                # value 3-bet
            return _raise_to(state, 3.4 * bet)
        if ace_blocker and suited and rank >= 1 - defend * 0.7 and u < 0.45:
            return _raise_to(state, 3.4 * bet)              # blocker 3-bet bluff (~2:1 value:bluff)
        return {"action": "call"} if rank >= 1 - defend else {"action": "fold"}
    if v["nraise"] == 2:                                    # facing a 3-bet
        req = owed / float(state["pot"] + owed)
        if rank >= 0.965 or (ace_blocker and suited and rank >= 0.7 and u < 0.35):
            return _raise_to(state, 2.3 * bet)
        return {"action": "call"} if rank >= max(0.45, 0.28 + 1.5 * req) else {"action": "fold"}
    return {"action": "all_in"} if rank >= 0.975 else ({"action": "call"} if rank >= 0.93 else {"action": "fold"})


# ------------------------------------------------------------------------------ postflop
def _range_tightness(frac, street, raised):
    q = 0.55 if frac <= 0.4 else 0.42 if frac <= 0.8 else 0.32 if frac <= 1.2 else 0.24
    q -= 0.04 if street == "river" else 0.0
    q -= 0.10 if raised else 0.0
    return max(0.10, q)


def _postflop(state, v):
    rng = _rng(state, state["street"])
    u = rng.random()
    street = state["street"]
    board = state["community_cards"]
    hole = state["your_cards"]
    pot, owed = state["pot"], state["amount_owed"]
    dead = set(hole) | set(board)

    if owed > 0:
        frac = owed / float(max(1, pot - owed))
        raised = any(e["street"] == street and e["action"] in ("raise", "all_in") and e["seat"] == v["me"]
                     for e in state["action_log"])
        q = _range_tightness(frac, street, raised)
        vill = _sample_villain(rng, dead, board, 70, q, False)
        eq = _equity(rng, hole, board, vill)
        req = owed / float(pot + owed)
        if eq >= 0.78 and u < (0.55 if street != "river" else 0.7):
            return _raise_to(state, state["current_bet"] + max(owed * 1.7, pot * 0.65))      # value raise
        if not v["ip"] and eq >= 0.85 and u < 0.8:
            return _raise_to(state, state["current_bet"] + max(owed * 1.7, pot * 0.65))
        if eq >= req + 0.02:
            return {"action": "call"}
        if street != "river" and eq < 0.30 and frac <= 0.5 and u < 0.05 and _draw_potential(rng, hole, board) >= 0.10:
            return _raise_to(state, state["current_bet"] * 3)                                  # semi-bluff raise
        return {"action": "fold"}

    # to act with no bet: value bet / bluff / check
    vill = _sample_villain(rng, dead, board, 60, 0.55, False)           # assumed calling range
    eq = _equity(rng, hole, board, vill)
    wet = _wetness(board)
    if street == "river":
        sizes = (0.5, 0.8, 1.4) if eq >= 0.85 else (0.4, 0.7)
    else:
        sizes = (0.33, 0.5, 0.75) if wet == 0 else (0.5, 0.75, 1.0)
    size = sizes[min(len(sizes) - 1, int(rng.random() * len(sizes)))]
    value_thr = 0.62 if v["ip"] else 0.66
    if eq >= 0.85 and not v["ip"] and street != "river" and u < 0.3:
        return {"action": "check"}                                       # OOP trap, plans a check-raise
    if eq >= value_thr:
        return _bet_pot(state, size)
    if 0.50 <= eq < value_thr and (v["ip"] or v["aggr"]) and u < 0.35:
        return _bet_pot(state, 0.33)                                     # thin / protection bet
    if eq < 0.32:
        b = size / (1.0 + 2.0 * size)                                    # bluff share of my bets
        potential = _draw_potential(rng, hole, board) if street != "river" else 0.0
        blocker = any(c[0] in "AK" for c in hole)
        eligible = potential >= 0.08 or (street == "river" and blocker) or (v["aggr"] and street == "flop")
        decay = {"flop": 1.0, "turn": 0.8, "river": 0.9}[street]
        if eligible and u < min(0.7, 0.9 * b / (1.0 - b) * 1.5) * decay * (1.0 if (v["ip"] or v["aggr"]) else 0.5):
            return _bet_pot(state, size)
    return {"action": "check"}


# --------------------------------------------------------------------------------- entry
def decide(game_state: dict) -> dict:
    if game_state.get("type") == "warmup":
        return {"action": "check"}
    try:
        v = _view(game_state)
        if game_state["street"] == "preflop":
            return _preflop(game_state, v)
        return _postflop(game_state, v)
    except Exception:
        return _fold_or_check(game_state)
