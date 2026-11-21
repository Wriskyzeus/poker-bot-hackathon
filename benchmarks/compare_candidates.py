#!/usr/bin/env python3
"""Compare two run_suite.sh output folders (e.g. V3.4 vs a candidate) opponent by opponent. Benchmark-only.

    python3 benchmarks/compare_candidates.py <out_dir_baseline> <out_dir_candidate>

Reports, per opponent present in both: matches won, duplicate-pair W/D/L, runner problems, pairs that changed
outcome, and a MATCHED-DEAL check from the kept logs: for every (seed, seat order), each hand number played by
both runs must have the same hand_seed, the same canonical hand id and the same hole cards per seat.
Exit code 1 if any deal mismatch is found (the comparison would not be like-for-like).
"""
import csv, glob, json, os, sys


def load(d):
    ms = list(csv.DictReader(open(os.path.join(d, "matches.csv"))))
    ps = {r["seed"]: r["outcome_for_A"] for r in csv.DictReader(open(os.path.join(d, "pairs.csv")))}
    return ms, ps


def deals(path):
    out = {}
    for line in open(path):
        r = json.loads(line)
        if r["type"] == "hand_start":
            by_seat = {r["seats"][b]: tuple(c) for b, c in r["hole"].items()}
            out[r["hand"]] = (r["hand_seed"], by_seat.get(0), by_seat.get(1))
        elif r["type"] == "decision":
            hid = r["state"].get("hand_id", "")
            if not hid.endswith("_h%04d" % r["hand"]):
                out[("bad_id", r["hand"])] = hid
    return out


def main(a, b):
    bad = 0
    names = sorted(n for n in os.listdir(a) if os.path.isfile(os.path.join(a, n, "matches.csv"))
                   and os.path.isfile(os.path.join(b, n, "matches.csv")))
    print("%-13s %-22s %-22s %s" % ("opponent", "baseline wins  W/D/L", "candidate wins W/D/L", "pairs changed | deals checked"))
    tot = [0, 0, 0, 0]
    for n in names:
        (ma, pa), (mb, pb) = load(os.path.join(a, n)), load(os.path.join(b, n))
        def summ(ms, ps):
            ok = [m for m in ms if m["status"] == "ok"]
            w = sum(m["winner"] == "A" for m in ok)
            prob = sum(int(m[k]) for m in ms for k in ("a_timeouts", "a_errors", "a_restarts"))
            c = [sum(v == x for v in ps.values()) for x in "WDL"]
            return w, len(ok), c, prob, len(ms) - len(ok)
        wa, na, ca, pra, ia = summ(ma, pa); wb, nb, cb, prb, ib = summ(mb, pb)
        changed = ["%s:%s>%s" % (s, pa[s], pb[s]) for s in sorted(pa, key=int) if s in pb and pa[s] != pb[s]]
        checked = mism = 0
        for fa in sorted(glob.glob(os.path.join(a, n, "logs", "*.jsonl"))):
            fb = os.path.join(b, n, "logs", os.path.basename(fa))
            if not os.path.exists(fb):
                continue
            da, db = deals(fa), deals(fb)
            for h in set(da) & set(db):
                checked += 1
                mism += da[h] != db[h]
            mism += sum(1 for k in list(da) + list(db) if isinstance(k, tuple))
        bad += mism
        tot[0] += wa; tot[1] += na; tot[2] += wb; tot[3] += nb
        print("%-13s %3d/%-3d %2d/%2d/%-2d p%d i%d   %3d/%-3d %2d/%2d/%-2d p%d i%d   %d %s | %d hands, %d mismatches" % (
            n, wa, na, ca[0], ca[1], ca[2], pra, ia, wb, nb, cb[0], cb[1], cb[2], prb, ib,
            len(changed), " ".join(changed[:6]), checked, mism))
    print("TOTAL baseline %d/%d   candidate %d/%d   (p = hero timeouts+errors+restarts, i = incomplete matches)" % tuple(tot))
    if bad:
        print("DEAL MISMATCH: the two runs did not see identical deals/hand ids; do not compare them.")
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
