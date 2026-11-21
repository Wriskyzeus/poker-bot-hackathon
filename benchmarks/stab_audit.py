#!/usr/bin/env python3
"""Observed "bet after the opponent checks" (stab) statistics for one run_suite.sh output folder. Benchmark-only.

    python3 benchmarks/stab_audit.py <suite_out_dir> [<suite_out_dir_2> ...]

Per opponent: checked-to opportunities, how often the hero bet, the opponent's reply (fold / call / raise), the realised
result of each bet measured from the decision point (final stack minus stack before the bet, in big blinds), the same
split for the first 20 hands of a match (cold start), and how often the hero later folded after being raised.
Uses public actions and realised chips only; no hole cards are read.
"""
import collections, csv, glob, json, os, sys


def audit(d):
    rows = {}
    for opp in sorted(n for n in os.listdir(d) if os.path.isfile(os.path.join(d, n, "matches.csv"))):
        first = next(csv.DictReader(open(os.path.join(d, opp, "matches.csv"))))
        hero = os.path.basename(first["bot_a"].rstrip("/"))
        c = collections.Counter(); ev = collections.defaultdict(float)
        for f in sorted(glob.glob(os.path.join(d, opp, "logs", "*.jsonl"))):
            st, hands, en = {}, collections.defaultdict(list), {}
            for line in open(f):
                r = json.loads(line)
                if r["type"] == "hand_start": st[r["hand"]] = r
                elif r["type"] == "decision": hands[r["hand"]].append(r)
                elif r["type"] == "hand_end": en[r["hand"]] = r
            for hn, ds in hands.items():
                if hn not in en or hero not in st[hn]["stacks"]: continue
                final = st[hn]["stacks"][hero] + en[hn]["deltas"][hero]; bb = st[hn]["blinds"]["bb"]
                post = [x for x in ds if x["street"] != "preflop"]
                for i, x in enumerate(post):
                    s = x["state"]
                    if x["bot"] != hero or s["amount_owed"] != 0: continue
                    if not any(e["street"] == x["street"] and e["seat"] != s["seat_to_act"] and e["action"] == "check" for e in s["action_log"]): continue
                    stage = "early" if hn < 20 else "later"
                    c["opp"] += 1; c["opp_" + x["street"]] += 1
                    if x["applied"]["action"] not in ("raise", "all_in"): continue
                    c["stab"] += 1; c["stab_" + x["street"]] += 1; c["stab_" + stage] += 1
                    g = (final - s["your_stack"]) / bb; ev["all"] += g; ev[stage] += g
                    nxt = post[i + 1] if i + 1 < len(post) else None
                    if nxt is not None and nxt["bot"] != hero and nxt["street"] == x["street"]:
                        a = nxt["applied"]["action"]; a = "fold" if a == "fold" else "call" if a == "call" else "raise"
                        c["reply_" + a] += 1
                        if a == "raise":
                            me2 = post[i + 2] if i + 2 < len(post) else None
                            if me2 is not None and me2["bot"] == hero: c["hero_%s_vs_raise" % ("fold" if me2["applied"]["action"] == "fold" else "continue")] += 1
        rows[opp] = (hero, c, ev)
    return rows


def main(dirs):
    for d in dirs:
        print("== %s" % d)
        print("%-12s %6s %6s %6s | %-17s | %-22s | %10s %10s | %s" % ("opponent", "chk-to", "stabs", "stab%", "flop/turn/river %", "reply fold/call/raise", "bb per stab", "early(<20)", "hero vs raise fold/cont"))
        for opp, (hero, c, ev) in audit(d).items():
            n = max(1, c["opp"]); s = c["stab"]; rep = max(1, c["reply_fold"] + c["reply_call"] + c["reply_raise"])
            pct = lambda st: "%.0f" % (100.0 * c["stab_" + st] / max(1, c["opp_" + st]))
            print("%-12s %6d %6d %5.1f%% | %5s/%5s/%5s | %5.0f%%/%4.0f%%/%4.0f%% (n=%d) | %+10.2f %+10.2f | %d/%d" % (
                opp, c["opp"], s, 100.0 * s / n, pct("flop"), pct("turn"), pct("river"),
                100.0 * c["reply_fold"] / rep, 100.0 * c["reply_call"] / rep, 100.0 * c["reply_raise"] / rep, rep,
                ev["all"] / max(1, s), ev["early"] / max(1, c["stab_early"]), c["hero_fold_vs_raise"], c["hero_continue_vs_raise"]))


if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    main(sys.argv[1:])
