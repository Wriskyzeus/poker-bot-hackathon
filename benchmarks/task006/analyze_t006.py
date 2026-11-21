"""TASK-006 hand-level threat analysis of committed V3.4 (hero = bot name starting 'uo_monte_v34').
Reads benchmark logs under /tmp/t006/results/*/logs/*.jsonl. Offline ground truth (opponent hole cards from
hand_start) is used ONLY after the fact to label opponent bets as bluff/value; neither bot ever sees it.
"""
import collections, glob, json, os, sys
import eval7

R = "/tmp/t006/results"
OUT = "/tmp/t006/analysis"
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, "/tmp/t005/work")
NASH = json.load(open("/tmp/t005/work/nash_tables.json"))
CL = NASH["classes"]; IDX = {c: i for i, c in enumerate(CL)}
RK = "23456789TJQKA"


def cls(c1, c2):
    r1, r2 = c1[0], c2[0]; s = c1[1] == c2[1]
    if RK.index(r1) < RK.index(r2):
        r1, r2 = r2, r1
    return r1 + r2 if r1 == r2 else r1 + r2 + ("s" if s else "o")


def htype(hole, board):
    cards = [eval7.Card(c) for c in list(hole) + list(board)]
    if len(cards) < 5:
        return None
    return eval7.handtype(eval7.evaluate(cards))


def bucket(x):
    return "small<=0.4" if x <= 0.4 else "medium<=0.8" if x <= 0.8 else "pot<=1.2" if x <= 1.2 else "over>1.2"


def stage(h):
    return "early(0-39)" if h < 40 else "mid(40-99)" if h < 100 else "late(100+)"


def load_runs():
    for d in sorted(glob.glob(R + "/*_*_*/")):
        name = os.path.basename(d.rstrip("/"))
        block, setting, opp = name.split("_", 2)
        for f in sorted(glob.glob(d + "logs/*.jsonl")):
            yield block, setting, opp, f


def parse(f):
    hands = {}
    for line in open(f):
        r = json.loads(line)
        t = r["type"]
        if t == "hand_start":
            hands[r["hand"]] = {"hole": r["hole"], "stacks": r["stacks"], "blinds": r["blinds"], "dec": [], "net": {}}
        elif t == "decision":
            hands[r["hand"]]["dec"].append(r)
        elif t == "hand_end":
            hands[r["hand"]]["net"] = r["deltas"]; hands[r["hand"]]["board"] = r["board"]
    return hands


def hero_of(h):
    return [b for b in h["hole"] if b.startswith("uo_monte_v34")][0]


facing = collections.defaultdict(lambda: collections.Counter())      # (opp, street, sizebucket, truth) -> actions
facing_net = collections.defaultdict(float)
raise_resp = collections.defaultdict(collections.Counter)            # v34 bet -> opp raise -> v34 response
pre = collections.defaultdict(collections.Counter)
short = collections.defaultdict(collections.Counter)
timeline = collections.defaultdict(lambda: collections.Counter())    # (opp, stage) -> counts
net_stage = collections.defaultdict(lambda: [0.0, 0])
examples = collections.defaultdict(list)

for block, setting, opp, f in load_runs():
    hands = parse(f)
    for hn, h in hands.items():
        if "board" not in h:
            continue
        hero = hero_of(h); villain = [b for b in h["hole"] if b != hero][0]
        bbv = h["blinds"]["bb"]
        net_bb = h["net"].get(hero, 0) / bbv
        net_stage[(setting, opp, stage(hn))][0] += net_bb; net_stage[(setting, opp, stage(hn))][1] += 1
        for d in h["dec"]:
            if d["bot"] != hero:
                continue
            s = d["state"]; a = d["applied"]["action"]; st = s["street"]
            owed = s["amount_owed"]
            if st != "preflop" and owed > 0:
                big = owed / max(1, s["pot"] - owed)
                ht = htype(h["hole"][villain], s["community_cards"])
                truth = "air" if ht == "High Card" else "pair" if ht == "Pair" else "twopair+"
                key = (setting, opp, st, bucket(big), truth)
                facing[key][a] += 1
                if a == "fold":
                    facing_net[key] += 0
                if len(examples[(opp, st, truth, a)]) < 3:
                    examples[(opp, st, truth, a)].append({
                        "match": os.path.basename(f), "setting": setting, "hand": hn, "hero": h["hole"][hero],
                        "opp": h["hole"][villain], "board": s["community_cards"], "pot": s["pot"], "owed": owed,
                        "action": a, "hero_net_chips": h["net"].get(hero)})
                timeline[(setting, opp, stage(hn))]["faced_bet_" + a] += 1
            # preflop behaviour
            if st == "preflop":
                n_r = sum(1 for e in s["action_log"] if e["action"] in ("raise", "all_in"))
                eff = min(s["your_stack"] + s["your_bet_this_street"],
                          [p for p in s["players"] if p["bot_id"] != hero][0]["stack"] +
                          [p for p in s["players"] if p["bot_id"] != hero][0]["bet_this_street"]) / bbv
                is_sb = s["sb_seat"] == s["seat_to_act"]
                pos = "SB" if is_sb else "BB"
                pre[(setting, opp, pos, "facing_%draise" % min(n_r, 3) if n_r else "first_in")][a] += 1
                if eff <= 15 and n_r >= 1 and any(e["action"] == "all_in" for e in s["action_log"]) and not is_sb or \
                        (eff <= 15 and n_r >= 1 and owed >= s["your_stack"] + s["your_bet_this_street"] and not is_sb):
                    bb_eff = eff
                    dpt = min((3, 4, 5, 6, 7, 8, 10, 12, 15), key=lambda x: abs(x - bb_eff))
                    ante = 0.1 if s["blinds"]["ante"] > 0 else 0.0
                    res = NASH["res"]["%d_%s" % (dpt, ante)]
                    c = cls(*h["hole"][hero])
                    nash = "call" if res["call"][IDX[c]] >= 0.5 else "fold"
                    short[(setting, opp, "BB_vs_jam", "eff<=8" if eff <= 8 else "eff8-15")][(a == "call", nash)] += 1
            # V3.4 bets then faces a raise
        # v34 bet followed by opp raise -> v34 response (visible in decisions order)
        decs = h["dec"]
        for i in range(len(decs) - 1):
            d, e = decs[i], decs[i + 1]
            if d["bot"] == hero and d["applied"]["action"] == "raise" and d["street"] != "preflop" and e["bot"] == hero \
                    and e["street"] == d["street"]:
                raise_resp[(setting, opp, d["street"])][e["applied"]["action"]] += 1

# ---- outputs
def dump(name, obj):
    json.dump(obj, open(os.path.join(OUT, name), "w"), indent=1, default=str)

fac = collections.defaultdict(lambda: collections.Counter())
for (setting, opp, st, b, truth), c in facing.items():
    for a, n in c.items():
        fac["|".join((setting, opp, st, b, truth))][a] += n
dump("v34_facing_bet.json", {k: dict(v) for k, v in sorted(fac.items())})
dump("v34_preflop.json", {"|".join(k): dict(v) for k, v in sorted(pre.items())})
dump("v34_vs_jam_short.json", {"|".join(k): {"%s,nash=%s" % ("call" if x[0] else "notcall", x[1]): n for x, n in v.items()} for k, v in short.items()})
dump("v34_raise_response.json", {"|".join(k): dict(v) for k, v in sorted(raise_resp.items())})
dump("stage_net_bb.json", {"|".join(k): {"hands": v[1], "avg_bb_per_hand": v[0] / max(1, v[1])} for k, v in sorted(net_stage.items())})
dump("timeline_counts.json", {"|".join(k): dict(v) for k, v in sorted(timeline.items())})
dump("examples.json", {"|".join(k): v for k, v in examples.items()})

# ---- human-readable summary for the standard-structure holdout+dev combined
def agg(filter_fn, group):
    out = collections.defaultdict(collections.Counter)
    for k, v in fac.items():
        setting, opp, st, b, truth = k.split("|")
        if filter_fn(setting, opp, st, b, truth):
            for a, n in v.items():
                out[group(setting, opp, st, b, truth)][a] += n
    return out

def show(title, d):
    print("\n##", title)
    for k in sorted(d):
        c = d[k]; n = sum(c.values())
        print("  %-42s n=%4d  fold %4.1f%%  call %4.1f%%  raise %4.1f%%" % (
            k, n, 100 * (c["fold"]) / n, 100 * c["call"] / n, 100 * (c["raise"] + c["all_in"]) / n))

for opp in ("bluffer_low", "bluffer_mid", "bluffer_high", "adaptive", "pressure"):
    show("V3.4 facing bets, standard blinds, vs %s, by street x size" % opp,
         agg(lambda s, o, st, b, t: s == "standard" and o == opp, lambda s, o, st, b, t: "%s %s" % (st, b)))
show("V3.4 facing RIVER bets by opponent truth (standard, all opps)",
     agg(lambda s, o, st, b, t: s == "standard" and st == "river", lambda s, o, st, b, t: "%s | %s" % (o, t)))
show("V3.4 facing FLOP/TURN bets by opponent truth (standard, all opps)",
     agg(lambda s, o, st, b, t: s == "standard" and st != "river", lambda s, o, st, b, t: "%s | %s %s" % (o, st, t)))
print("\n## preflop V3.4 action mix (standard)")
for k, v in sorted(pre.items()):
    if k[0] == "standard":
        n = sum(v.values()); print("  ", k[1:], dict(v), "n=%d" % n)
print("\n## V3.4 BB vs jam <=15bb (call?, Nash-call?)")
for k, v in sorted(short.items()):
    print("  ", k, dict(v))
print("\n## stage avg bb/hand for V3.4")
for k, v in sorted(net_stage.items()):
    if k[0] == "standard":
        print("  ", k[1:], "%+.3f bb/hand n=%d" % (v[0] / v[1], v[1]))

# ======================= river counterfactual: would calling a river bet have been +EV? =======================
print("\n## RIVER counterfactual (hindsight vs the opponent's actual hands; river is the last street so this is exact)")
cf = collections.defaultdict(lambda: {"n": 0, "w": 0.0, "pot": 0.0, "owed": 0.0, "ev": 0.0, "req": 0.0})
cf_rows = []
for block, setting, opp, f in load_runs():
    if setting != "standard":
        continue
    hands = parse(f)
    for hn, h in hands.items():
        if "board" not in h:
            continue
        hero = hero_of(h); villain = [b for b in h["hole"] if b != hero][0]
        for d in h["dec"]:
            if d["bot"] != hero or d["street"] != "river" or d["state"]["amount_owed"] <= 0:
                continue
            s = d["state"]; board = s["community_cards"]
            if len(board) != 5:
                continue
            hs = eval7.evaluate([eval7.Card(c) for c in h["hole"][hero] + board])
            vs = eval7.evaluate([eval7.Card(c) for c in h["hole"][villain] + board])
            w = 1.0 if hs > vs else 0.5 if hs == vs else 0.0
            P, O = s["pot"], s["amount_owed"]
            big = O / max(1, P - O)
            bkt = bucket(big)
            ev_call = w * P - (1 - w) * O if w != 0.5 else (P - O) / 2.0
            ev_call = (w == 1.0) * P + (w == 0.0) * (-O) + (w == 0.5) * ((P - O) / 2.0)
            k = (opp if opp.startswith("bluffer") else opp, bkt, d["applied"]["action"] if d["applied"]["action"] in ("fold", "call") else "raise")
            for kk in (k, ("ALL", bkt, k[2]), ("ALL", "ALL", k[2])):
                a = cf[kk]; a["n"] += 1; a["w"] += w; a["ev"] += ev_call / s["blinds"]["bb"]; a["req"] += O / (P + O)
            truth = htype(h["hole"][villain], board)
            if k[2] == "fold" and len(cf_rows) < 5000:
                cf_rows.append({"opp": opp, "hand": hn, "file": os.path.basename(f), "hero": h["hole"][hero], "opp_hand": h["hole"][villain],
                                "board": board, "pot": P, "owed": O, "opp_type": truth, "hero_would_win": w, "ev_call_bb": ev_call / s["blinds"]["bb"]})
print("  %-14s %-12s %-6s %5s  %8s %8s %10s" % ("opp", "size", "action", "n", "win%(hind)", "req eq%", "EV(call) bb/spot"))
for k in sorted(cf):
    a = cf[k]
    if a["n"] >= 20:
        print("  %-14s %-12s %-6s %5d  %8.1f %8.1f %10.2f" % (k[0], k[1], k[2], a["n"], 100 * a["w"] / a["n"], 100 * a["req"] / a["n"], a["ev"] / a["n"]))
dump("river_counterfactual.json", {"|".join(k): v for k, v in cf.items()})
dump("river_fold_rows.json", cf_rows[:400])
