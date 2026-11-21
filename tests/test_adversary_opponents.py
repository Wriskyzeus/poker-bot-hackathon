"""Self-tests for the TASK-006 adversarial practice opponents (benchmark-only).

Run from the repo root:  python3 tests/test_adversary_opponents.py -v
Replays REAL engine states from TASK-004 logs when present (skipped otherwise) plus synthetic states.
The decide() wrapper swallows exceptions, so legality tests call the raw _preflop/_postflop functions
to expose bugs instead of hiding them behind a fallback action.
"""

import ast
import importlib.util
import json
import sys
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OPP = REPO / "benchmarks" / "opponents"
NAMES = ["bluffer_low", "bluffer_mid", "bluffer_high", "pressure", "adaptive"]


def load(name, tag=""):
    spec = importlib.util.spec_from_file_location(f"adv_{name}{tag}", OPP / name / "bot.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MODS = {n: load(n) for n in NAMES}


def real_states(limit=2500):
    """Decision states produced by the official engine (portable compressed fixture in tests/fixtures)."""
    import gzip
    fx = REPO / "tests" / "fixtures" / "engine_states.json.gz"
    if not fx.exists():
        return []
    with gzip.open(fx, "rt") as g:
        return json.load(g)[:limit]


def raw_reply(mod, st):
    cfg = mod.PROFILES[mod.PROFILE]
    return mod._preflop(st, cfg) if st["street"] == "preflop" else mod._postflop(st, cfg)


def legal(st, reply):
    a = reply["action"]
    me_cap = st["your_bet_this_street"] + st["your_stack"]
    if a == "fold":
        return True
    if a == "check":
        return st["can_check"]
    if a in ("call", "all_in"):
        return True
    if a == "raise":
        return st["min_raise_to"] <= reply["amount"] < me_cap and isinstance(reply["amount"], int)
    return False


class TestSource(unittest.TestCase):
    def test_imports_are_stdlib_only(self):
        for n in NAMES:
            tree = ast.parse((OPP / n / "bot.py").read_text())
            mods = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    mods |= {a.name.split(".")[0] for a in node.names}
                elif isinstance(node, ast.ImportFrom):
                    mods.add(node.module.split(".")[0])
            self.assertLessEqual(mods, {"zlib"}, n)

    def test_no_forbidden_calls_or_hidden_card_keys(self):
        for n in NAMES:
            src = (OPP / n / "bot.py").read_text()
            for bad in ("eval(", "exec(", "open(", "subprocess", "socket", "threading", "hole_cards", "print(", "random"):
                self.assertNotIn(bad, src, (n, bad))

    def test_generated_files_match_source(self):
        sys.path.insert(0, str(OPP))
        import build_adversaries as b
        for n in NAMES:
            self.assertEqual((OPP / n / "bot.py").read_text(), b.render(n), n)


@unittest.skipUnless(real_states(1), "engine-state fixture not available")
class TestLegalityOnRealStates(unittest.TestCase):
    states = real_states()

    def test_raw_actions_are_legal_and_never_raise_exceptions(self):
        for n in NAMES:
            mod = load(n, "_fresh")
            for st in self.states:
                rep = raw_reply(mod, st)
                self.assertTrue(legal(st, rep), (n, rep, st["street"], st["your_stack"], st["min_raise_to"]))

    def test_every_profile_uses_every_main_action_type(self):
        kinds = {}
        for n in NAMES:
            mod = load(n, "_fresh2")
            kinds[n] = {mod.decide(st)["action"] for st in self.states}
        for n, k in kinds.items():
            self.assertTrue({"fold", "call", "raise"} <= k, (n, k))

    def test_decision_latency(self):
        for n in NAMES:
            mod = load(n, "_t")
            worst = 0.0
            for st in self.states[:400]:
                t = time.perf_counter()
                mod.decide(st)
                worst = max(worst, time.perf_counter() - t)
            self.assertLess(worst, 0.05, n)       # limit is 2 s; these are lookup-table bots

    def test_deterministic_same_state_same_action(self):
        for n in NAMES:
            a = load(n, "_a")
            b = load(n, "_b")
            for st in self.states[:300]:
                self.assertEqual(a.decide(st), b.decide(st), n)

    def test_ignores_opponent_hole_card_field(self):
        """The public state shows opponent hole_cards only as None; junk values must not matter."""
        for n in NAMES:
            mod = load(n, "_h")
            mod2 = load(n, "_h2")
            for st in self.states[:200]:
                alt = json.loads(json.dumps(st))
                for p in alt["players"]:
                    if p["seat"] != alt["seat_to_act"]:
                        p["hole_cards"] = ["As", "Ah"]
                self.assertEqual(mod.decide(st), mod2.decide(alt), n)


@unittest.skipUnless(real_states(1), "engine-state fixture not available")
class TestCanonicalHandIds(unittest.TestCase):
    """Opponent choices must not depend on the runner's match id or on bot names (hero version)."""
    states = real_states(400)

    def test_actions_invariant_to_match_id_and_bot_names(self):
        for n in NAMES:
            a, b = load(n, "_ca"), load(n, "_cb")
            for st in self.states:
                alt = json.loads(json.dumps(st))
                alt["hand_id"] = "uo_monte_v5r_candidate_seed861_h%04d" % st["hand_num"]
                alt["your_bot_id"] = "renamed_me"
                for p in alt["players"]:
                    p["bot_id"] = "hero_v5_r" if p["seat"] != alt["seat_to_act"] else "renamed_me"
                for e in alt["action_log"]:
                    e["bot_id"] = "x" + str(e["seat"])
                self.assertEqual(a.decide(st), b.decide(alt), n)

    def test_actions_do_depend_on_hand_number(self):
        m = load("bluffer_high", "_cc")
        st = self.states[0]
        self.assertNotEqual(m._canon_hand(st), m._canon_hand(dict(st, hand_num=st["hand_num"] + 1)))


class TestSyntheticBoundaries(unittest.TestCase):
    def mk(self, cards, board, street, pot, owed, stack, opp_stack, bb=100, bet_this=0, sb_seat=0, me=0, log=None):
        cur = bet_this + owed
        return {
            "type": "action_request", "hand_id": "h1", "street": street, "seat_to_act": me, "your_bot_id": "x",
            "pot": pot, "community_cards": list(board), "current_bet": cur,
            "min_raise_to": cur + max(bb, owed), "amount_owed": owed, "can_check": owed == 0,
            "your_cards": list(cards), "your_stack": stack, "your_bet_this_street": bet_this,
            "players": [{"seat": me, "bot_id": "x", "stack": stack, "bet_this_street": bet_this, "hole_cards": None},
                        {"seat": 1 - me, "bot_id": "y", "stack": opp_stack, "bet_this_street": cur, "hole_cards": None}],
            "action_log": log or [], "hand_num": 1, "blinds": {"sb": bb // 2, "bb": bb, "ante": 0},
            "button_seat": sb_seat, "sb_seat": sb_seat, "bb_seat": 1 - sb_seat,
        }

    def test_short_stack_never_returns_illegal_raise(self):
        for n in NAMES:
            mod = load(n, "_s")
            for stack in (150, 250, 399, 400, 700, 1000, 1500):
                st = self.mk(["As", "Kd"], [], "preflop", 150, 50, stack, 10000, bet_this=50, sb_seat=0,
                             log=[{"seat": 0, "bot_id": "x", "action": "small_blind", "amount": 50, "street": "preflop"},
                                  {"seat": 1, "bot_id": "y", "action": "big_blind", "amount": 100, "street": "preflop"}])
                st["current_bet"] = 100
                rep = raw_reply(mod, st)
                self.assertTrue(legal(st, rep), (n, stack, rep))

    def test_pressure_shoves_short_effective_stack_with_premium_and_folds_trash(self):
        mod = MODS["pressure"]
        log = [{"seat": 0, "bot_id": "x", "action": "small_blind", "amount": 50, "street": "preflop"},
               {"seat": 1, "bot_id": "y", "action": "big_blind", "amount": 100, "street": "preflop"}]
        top = self.mk(["Ah", "As"], [], "preflop", 150, 50, 700, 800, bet_this=50, log=log)
        top["current_bet"] = 100
        bad = self.mk(["7c", "2d"], [], "preflop", 150, 50, 700, 800, bet_this=50, log=log)
        bad["current_bet"] = 100
        self.assertEqual(mod.decide(top)["action"], "all_in")
        self.assertEqual(mod.decide(bad)["action"], "fold")

    def test_pressure_open_3bet_4bet_sizes_deep(self):
        mod = MODS["pressure"]
        base = [{"seat": 0, "bot_id": "x", "action": "small_blind", "amount": 50, "street": "preflop"},
                {"seat": 1, "bot_id": "y", "action": "big_blind", "amount": 100, "street": "preflop"}]
        st = self.mk(["Ah", "Ks"], [], "preflop", 150, 50, 9950, 9900, bet_this=50, log=base)
        st["current_bet"] = 100
        r = mod.decide(st)
        self.assertEqual(r["action"], "raise")
        self.assertEqual(r["amount"], max(220, st["min_raise_to"]))       # 2.2 bb open (total street bet)

    def test_check_not_returned_when_owing(self):
        for n in NAMES:
            mod = load(n, "_c")
            st = self.mk(["2c", "7d"], ["Ah", "Kd", "9s"], "flop", 600, 400, 9000, 9000, bet_this=0)
            self.assertNotEqual(mod.decide(st)["action"], "check", n)

    def test_warmup_state_ok(self):
        for n in NAMES:
            self.assertEqual(MODS[n].decide({"type": "warmup"}), {"action": "check"})

    def test_made_strength_and_draws(self):
        m = MODS["bluffer_mid"]
        self.assertEqual(m.made_strength(["As", "Ad"], ["2c", "7h", "9d"]), 2)
        self.assertEqual(m.made_strength(["As", "Kd"], ["2c", "7h", "9d"]), 0)
        self.assertEqual(m.made_strength(["7s", "7d"], ["7c", "2h", "9d"]), 4)
        self.assertEqual(m.draw_kind(["As", "Ks"], ["2s", "7s", "9d"]), "fd")
        self.assertEqual(m.draw_kind(["8s", "9d"], ["6c", "7h", "Ks"]), "oesd")
        self.assertEqual(m.draw_kind(["As", "Kd"], ["2c", "7h", "9d"]), "")

    def test_pf_pct_ordering(self):
        m = MODS["pressure"]
        self.assertGreater(m.pf_pct(["As", "Ah"]), m.pf_pct(["Ks", "Kh"]))
        self.assertGreater(m.pf_pct(["Ks", "Qs"]), m.pf_pct(["Ks", "Qd"]))
        self.assertLess(m.pf_pct(["7c", "2d"]), 0.1)


class TestAdaptiveTracker(unittest.TestCase):
    def setUp(self):
        self.m = load("adaptive", "_tr")        # fresh module = fresh match-local memory
        self.log = [{"seat": 1, "bot_id": "y", "action": "small_blind", "amount": 50, "street": "preflop"},
                    {"seat": 0, "bot_id": "x", "action": "big_blind", "amount": 100, "street": "preflop"}]

    def st(self, hand_id, log, **kw):
        t = TestSyntheticBoundaries().mk(["As", "Kd"], [], "preflop", 150, 0, 9900, 9900, bet_this=100, log=log, sb_seat=1)
        t["hand_id"] = hand_id
        t.update(kw)
        return t

    def test_dedup_visible_replies_counted_once(self):
        log = self.log + [{"seat": 0, "bot_id": "x", "action": "raise", "amount": 300, "street": "preflop"},
                          {"seat": 1, "bot_id": "y", "action": "call", "amount": 300, "street": "preflop"}]
        s = self.st("h1", log)
        ctx = self.m._ctx(s)
        for _ in range(5):
            self.m._TRACKER.observe(s, ctx)
        self.assertEqual(self.m._TRACKER.trials("pre_open"), 1.0)

    def test_fold_inferred_from_stack_when_hand_ends(self):
        T = self.m._TRACKER
        s1 = self.st("h1", self.log)
        ctx = self.m._ctx(s1)
        T.observe(s1, ctx)
        T.note_my_action(s1, ctx, {"action": "raise", "amount": 300}, pot_after=150 + 200, stack_after=9700, all_in=False)
        # next hand: we won the pot uncontested -> our stack = 9700 + 350, then blind/ante posts are deducted
        post = [{"seat": 0, "bot_id": "x", "action": "small_blind", "amount": 50, "street": "preflop"},
                {"seat": 1, "bot_id": "y", "action": "big_blind", "amount": 100, "street": "preflop"}]
        s2 = self.st("h2", post)
        s2["your_stack"] = 9700 + 350 - 50
        T.observe(s2, self.m._ctx(s2))
        self.assertEqual(T.stats["pre_open"][0] > 0.9, True)       # counted as a fold (decayed slightly)

    def test_no_fold_when_stack_shows_showdown(self):
        T = self.m._TRACKER
        s1 = self.st("h1", self.log)
        ctx = self.m._ctx(s1)
        T.observe(s1, ctx)
        T.note_my_action(s1, ctx, {"action": "raise", "amount": 300}, pot_after=350, stack_after=9700, all_in=False)
        post = [{"seat": 0, "bot_id": "x", "action": "small_blind", "amount": 50, "street": "preflop"}]
        s2 = self.st("h2", post)
        s2["your_stack"] = 9700 + 600 - 50                         # won a bigger (called) pot
        T.observe(s2, self.m._ctx(s2))
        self.assertLess(T.stats["pre_open"][0], 0.01)
        self.assertGreater(T.stats["pre_open"][1], 0.9)

    def test_adaptation_direction(self):
        T = self.m._TRACKER
        for _ in range(30):
            T._add("bet_flop", True)
        self.assertGreater(self.m._bluff_mult("bet_flop"), 1.3)
        m2 = load("adaptive", "_tr2")
        for _ in range(30):
            m2._TRACKER._add("bet_flop", False)
        self.assertLess(m2._bluff_mult("bet_flop"), 0.7)

    def test_memory_resets_with_new_process(self):
        self.m._TRACKER._add("bet_flop", True)
        fresh = load("adaptive", "_tr3")
        self.assertEqual(fresh._TRACKER.trials("bet_flop"), 0.0)


if __name__ == "__main__":
    unittest.main()
