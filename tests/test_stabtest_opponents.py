"""Self-tests for the TASK-010 stab-regression opponents (benchmark-only). Run: python3 tests/test_stabtest_opponents.py -v"""
import ast, gzip, importlib.util, json, sys, unittest
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
OPP = REPO / "benchmarks" / "opponents"
NAMES = ["checkfold90", "checkcall50", "checktrap", "shifter"]

def load(name, tag=""):
    spec = importlib.util.spec_from_file_location("stab_%s%s" % (name, tag), OPP / name / "bot.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def states():
    fx = REPO / "tests" / "fixtures" / "engine_states.json.gz"
    if not fx.exists(): return []
    with gzip.open(fx, "rt") as g: return json.load(g)

STATES = states()

def legal(st, rep):
    a = rep["action"]; cap = st["your_bet_this_street"] + st["your_stack"]
    if a in ("fold", "call", "all_in"): return True
    if a == "check": return st["can_check"]
    return a == "raise" and isinstance(rep["amount"], int) and st["min_raise_to"] <= rep["amount"] < cap

def stab_state(i, cards, board, pot=600, bet=300, stack=9000, bb=100):
    """Opponent (seat 1, big blind, out of position) checked; hero (seat 0) bet `bet`; opponent to act."""
    street = {3: "flop", 4: "turn", 5: "river"}[len(board)]
    log = [{"seat": 1, "bot_id": "opp", "action": "check", "amount": 0, "street": street},
           {"seat": 0, "bot_id": "hero", "action": "raise", "amount": bet, "street": street}]
    return {"type": "action_request", "hand_id": "any_h%04d" % i, "street": street, "seat_to_act": 1, "your_bot_id": "opp",
            "pot": pot + bet, "community_cards": list(board), "current_bet": bet, "min_raise_to": 2 * bet, "amount_owed": bet,
            "can_check": False, "your_cards": list(cards), "your_stack": stack, "your_bet_this_street": 0,
            "players": [{"seat": 0, "bot_id": "hero", "stack": stack - bet, "bet_this_street": bet, "hole_cards": None},
                        {"seat": 1, "bot_id": "opp", "stack": stack, "bet_this_street": 0, "hole_cards": None}],
            "action_log": log, "hand_num": i, "blinds": {"sb": bb // 2, "bb": bb, "ante": 0}, "button_seat": 0, "sb_seat": 0, "bb_seat": 1}

WEAK = (["7c", "2d"], ["Ah", "Kd", "9s"])
STRONG = (["Ah", "Kc"], ["As", "Kd", "9s"])

def rates(mod, hand, n=400):
    c = {"fold": 0, "call": 0, "raise": 0}
    for i in range(n):
        a = mod.decide(stab_state(i, *hand))["action"]; c["raise" if a in ("raise", "all_in") else a] += 1
    return {k: v / n for k, v in c.items()}

class TestSource(unittest.TestCase):
    def test_imports_and_tokens(self):
        for n in NAMES:
            src = (OPP / n / "bot.py").read_text(); mods = set()
            for node in ast.walk(ast.parse(src)):
                if isinstance(node, ast.Import): mods |= {a.name.split(".")[0] for a in node.names}
                elif isinstance(node, ast.ImportFrom): mods.add(node.module.split(".")[0])
            self.assertLessEqual(mods, {"zlib", "eval7"}, n)
            for bad in ("eval(", "exec(", "open(", "socket", "threading", "hole_cards", "print(", "hand_id"):
                self.assertNotIn(bad, src, (n, bad))
    def test_rendered_matches_source(self):
        sys.path.insert(0, str(OPP)); import build_stabtests as b
        for n in NAMES: self.assertEqual((OPP / n / "bot.py").read_text(), b.render(n), n)

@unittest.skipUnless(STATES, "engine-state fixture not available")
class TestLegal(unittest.TestCase):
    def test_legal_on_real_engine_states_without_fallback(self):
        for n in NAMES:
            m = load(n, "_l")
            for st in STATES:
                rep = m._preflop(st) if st["street"] == "preflop" else m._postflop(st)
                self.assertTrue(legal(st, rep), (n, rep, st["street"], st["your_stack"], st["min_raise_to"]))
    def test_deterministic_and_independent_of_ids_and_names(self):
        for n in NAMES:
            a, b = load(n, "_a"), load(n, "_b")
            for st in STATES[:300]:
                alt = json.loads(json.dumps(st)); alt["hand_id"] = "v6_stab_candidate_h%04d" % st["hand_num"]
                for p in alt["players"]: p["bot_id"] = "renamed%d" % p["seat"]; p["hole_cards"] = ["As", "Ah"] if p["seat"] != alt["seat_to_act"] else None
                self.assertEqual(a.decide(st), b.decide(alt), n)

class TestStabResponses(unittest.TestCase):
    def test_checkfold90_folds_about_90_percent(self):
        r = rates(load("checkfold90", "_r"), WEAK); self.assertGreater(r["fold"], 0.85); self.assertEqual(r["raise"], 0)
    def test_checkcall50_continues_about_half(self):
        r = rates(load("checkcall50", "_r"), WEAK); self.assertTrue(0.40 < r["fold"] < 0.60, r)
    def test_checktrap_raises_strong_and_sometimes_bluffs(self):
        m = load("checktrap", "_r"); s = rates(m, STRONG); w = rates(m, WEAK)
        self.assertGreater(s["raise"], 0.6); self.assertEqual(s["fold"], 0); self.assertTrue(0.08 < w["raise"] < 0.25, w); self.assertLess(w["fold"], 0.75)
    def test_checktrap_checks_strong_hands_often(self):
        m = load("checktrap", "_c"); n = 0
        for i in range(300):
            st = stab_state(i, *STRONG); st.update(amount_owed=0, can_check=True, current_bet=0, min_raise_to=100, pot=600, action_log=[])
            st["players"][0].update(stack=9000, bet_this_street=0); n += m.decide(st)["action"] == "check"
        self.assertTrue(0.5 < n / 300 < 0.8, n)
    def test_shifter_changes_after_repeated_stabs_and_resets_per_match(self):
        m = load("shifter", "_s")
        first = [m.decide(stab_state(i, *STRONG))["action"] for i in range(m.SHIFT_AFTER)]
        self.assertTrue(all(a in ("fold", "call") for a in first), first)           # baited: never raises early
        later = [m.decide(stab_state(100 + i, *STRONG))["action"] for i in range(60)]
        self.assertGreater(sum(a in ("raise", "all_in") for a in later) / 60, 0.6)  # now traps
        fresh = load("shifter", "_s2")
        self.assertEqual(len(fresh._STABS_SEEN), 0)
        self.assertIn(fresh.decide(stab_state(0, *STRONG))["action"], ("fold", "call"))
    def test_same_stab_counted_once(self):
        m = load("shifter", "_d"); st = stab_state(7, *WEAK)
        for _ in range(10): m.decide(st)
        self.assertEqual(len(m._STABS_SEEN), 1)
    def test_all_in_and_short_stack_boundaries(self):
        for n in NAMES:
            m = load(n, "_b")
            for stack in (1, 50, 299, 300, 301, 650):
                st = stab_state(3, *STRONG, stack=stack); st["players"][1]["stack"] = stack
                self.assertTrue(legal(st, m.decide(st)), (n, stack))
    def test_warmup(self):
        for n in NAMES: self.assertEqual(load(n, "_w").decide({"type": "warmup"}), {"action": "check"})

if __name__ == "__main__":
    unittest.main()
