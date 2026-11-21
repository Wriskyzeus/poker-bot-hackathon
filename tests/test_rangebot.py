"""Self-tests for the TASK-007 independent opponent `rangebot` (benchmark-only). Run: python3 tests/test_rangebot.py -v"""
import ast, glob, importlib.util, json, time, unittest
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
BOT = REPO / "benchmarks" / "opponents" / "rangebot" / "bot.py"

def load(tag=""):
    spec = importlib.util.spec_from_file_location("rangebot" + tag, BOT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def real_states(limit=1500):
    out = []
    for f in sorted(glob.glob("/tmp/t006/results/*/logs/*.jsonl"))[::7]:
        for line in open(f):
            r = json.loads(line)
            if r["type"] == "decision" and r["state"].get("type") == "action_request":
                out.append(r["state"])
        if len(out) >= limit: break
    return out[:limit]

STATES = real_states()
M = load()

def raw(m, st):
    v = m._view(st)
    return m._preflop(st, v) if st["street"] == "preflop" else m._postflop(st, v)

def legal(st, rep):
    a = rep["action"]; cap = st["your_bet_this_street"] + st["your_stack"]
    if a in ("fold", "call", "all_in"): return True
    if a == "check": return st["can_check"]
    return a == "raise" and isinstance(rep["amount"], int) and st["min_raise_to"] <= rep["amount"] < cap

class TestSource(unittest.TestCase):
    def test_imports_and_forbidden_tokens(self):
        src = BOT.read_text(); tree = ast.parse(src); mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import): mods |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom): mods.add(n.module.split(".")[0])
        self.assertLessEqual(mods, {"random", "zlib", "eval7"})
        for bad in ("eval(", "exec(", "open(", "subprocess", "socket", "threading", "hole_cards", "print("):
            self.assertNotIn(bad, src)
    def test_independent_of_task006_source(self):
        self.assertNotIn("_adversary_src", BOT.read_text())
        self.assertFalse(hasattr(M, "made_strength"))

@unittest.skipUnless(STATES, "TASK-006 logs not available")
class TestReal(unittest.TestCase):
    def test_legal_actions_and_no_exceptions(self):
        for st in STATES:
            self.assertTrue(legal(st, raw(M, st)), (raw(M, st), st["street"], st["your_stack"], st["min_raise_to"]))
    def test_deterministic_and_ignores_opponent_hole_field(self):
        m2 = load("_b")
        for st in STATES[:150]:
            alt = json.loads(json.dumps(st))
            for p in alt["players"]:
                if p["seat"] != alt["seat_to_act"]: p["hole_cards"] = ["As", "Ah"]
            self.assertEqual(M.decide(st), m2.decide(alt))
    def test_latency_and_action_variety(self):
        worst = 0; kinds = set()
        for st in STATES[:300]:
            t = time.perf_counter(); r = M.decide(st); worst = max(worst, time.perf_counter() - t); kinds.add(r["action"])
        self.assertLess(worst, 0.25); self.assertTrue({"fold", "call", "raise"} <= kinds, kinds)

class TestUnits(unittest.TestCase):
    def test_mdf_formula(self):
        self.assertAlmostEqual(M._mdf_vs_steal(2.2, 0.0), 1.5 / 3.2, places=6)       # 46.9%
        self.assertAlmostEqual(M._mdf_vs_steal(2.0, 0.0), 0.5, places=6)
    def test_pf_rank_order(self):
        self.assertGreater(M._pf_rank(["As", "Ah"]), M._pf_rank(["Ks", "Kh"]))
        self.assertGreater(M._pf_rank(["Ks", "Qs"]), M._pf_rank(["7c", "2d"]))
        self.assertLess(M._pf_rank(["7c", "2d"]), 0.1)
    def test_warmup(self):
        self.assertEqual(M.decide({"type": "warmup"}), {"action": "check"})
    def test_short_stack_jam_fold(self):
        base = lambda cards: {"type": "action_request", "hand_id": "h", "street": "preflop", "seat_to_act": 0, "pot": 150,
            "community_cards": [], "current_bet": 100, "min_raise_to": 200, "amount_owed": 50, "can_check": False,
            "your_cards": cards, "your_stack": 650, "your_bet_this_street": 50,
            "players": [{"seat": 0, "bot_id": "x", "stack": 650, "bet_this_street": 50, "hole_cards": None},
                        {"seat": 1, "bot_id": "y", "stack": 700, "bet_this_street": 100, "hole_cards": None}],
            "action_log": [], "hand_num": 1, "blinds": {"sb": 50, "bb": 100, "ante": 0}, "button_seat": 0, "sb_seat": 0, "bb_seat": 1}
        self.assertEqual(M.decide(base(["Ah", "As"]))["action"], "all_in")
        self.assertEqual(M.decide(base(["7c", "2d"]))["action"], "fold")

if __name__ == "__main__":
    unittest.main()
