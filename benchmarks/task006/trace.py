"""Print a readable action trace for one hand of a benchmark log (HINDSIGHT view: shows both hole cards; bots never see this)."""
import json, sys
def trace(path, hand):
    hole = None; out = []
    for l in open(path):
        r = json.loads(l)
        if r.get("hand") != hand: continue
        t = r["type"]
        if t == "hand_start":
            out.append("HAND %d blinds %s stacks %s  hole %s" % (hand, r["blinds"], r["stacks"], r["hole"]))
        elif t == "decision":
            s = r["state"]
            out.append("  %-8s %-14s pot %5d owed %5d board %-16s -> %s%s" % (
                s["street"], r["bot"], s["pot"], s["amount_owed"], " ".join(s["community_cards"]),
                r["applied"]["action"], (" to %s" % r["reply"].get("amount")) if r["reply"].get("amount") else ""))
        elif t == "hand_end":
            out.append("  END board %s deltas %s" % (" ".join(r["board"]), r["deltas"]))
    return "\n".join(out)
if __name__ == "__main__":
    print(trace(sys.argv[1], int(sys.argv[2])))
