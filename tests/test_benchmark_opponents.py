"""Self-tests for the benchmark-only practice opponents (overfolder and trapper).

Run from the repo root:  python3 tests/test_benchmark_opponents.py -v
Every state here is synthetic and public-information only.
"""

import importlib.util
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OPP = REPO / "benchmarks" / "opponents"


def load(name):
    spec = importlib.util.spec_from_file_location(f"opp_{name}", OPP / name / "bot.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


overfolder, trapper = load("overfolder"), load("trapper")

DECK = [r + s for r in "23456789TJQKA" for s in "shdc"]


def state(cards, board=(), street=None, pot=400, owed=0, current_bet=None, stack=9000,
          bet_this=0, bb=100, min_raise=None):
    """A consistent synthetic game_state."""
    street = street or {0: "preflop", 3: "flop", 4: "turn", 5: "river"}[len(board)]
    if current_bet is None:
        current_bet = bet_this + owed
    return {
        "your_cards": list(cards), "community_cards": list(board), "street": street,
        "pot": pot, "amount_owed": owed, "can_check": owed == 0, "current_bet": current_bet,
        "your_stack": stack, "your_bet_this_street": bet_this,
        "min_raise_to": min_raise if min_raise is not None else current_bet + max(bb, owed),
        "blinds": {"sb": bb // 2, "bb": bb, "ante": 0}, "hand_num": 3,
    }


def is_legal(action, s):
    kind = action.get("action")
    if kind not in ("fold", "check", "call", "raise", "all_in"):
        return False
    if kind == "check" and not s["can_check"]:
        return False
    if kind == "raise":
        amount = action.get("amount")
        cap = s["your_bet_this_street"] + s["your_stack"]
        return isinstance(amount, int) and s["min_raise_to"] <= amount < cap
    return True


class HandReadingTests(unittest.TestCase):
    def test_made_hand_levels(self):
        for mod in (overfolder, trapper):
            ms = mod.made_strength
            self.assertEqual(ms(["As", "Kd"], ["2c", "7h", "9d"]), 0)             # air
            self.assertEqual(ms(["As", "Ad"], ["2c", "7h", "9d"]), 2)             # overpair
            self.assertEqual(ms(["9s", "3d"], ["9c", "7h", "2d"]), 2)             # top pair
            self.assertEqual(ms(["4s", "3d"], ["9c", "4h", "Kd"]), 1)             # weak pair
            self.assertEqual(ms(["9s", "7d"], ["9c", "7h", "2d"]), 3)             # two pair
            self.assertEqual(ms(["7s", "7d"], ["7c", "2h", "9d"]), 4)             # set
            self.assertEqual(ms(["8s", "9d"], ["5c", "6h", "7d"]), 4)             # straight
            self.assertEqual(ms(["As", "2s"], ["4s", "7s", "9s"]), 4)             # flush
            self.assertEqual(ms(["Ah", "5d"], ["2c", "3h", "4d"]), 4)             # wheel straight
            self.assertEqual(ms(["Ks", "Qd"], ["7c", "7h", "7d"]), 0)             # board trips only

    def test_preflop_tiers(self):
        for mod in (overfolder, trapper):
            self.assertEqual(mod.preflop_tier(["As", "Ah"]), 3)
            self.assertEqual(mod.preflop_tier(["As", "Kd"]), 3)
            self.assertEqual(mod.preflop_tier(["7s", "7d"]), 2)
            self.assertEqual(mod.preflop_tier(["Qs", "Jd"]), 2)
            self.assertEqual(mod.preflop_tier(["As", "3s"]), 2)
            self.assertEqual(mod.preflop_tier(["As", "3d"]), 1)
            self.assertEqual(mod.preflop_tier(["7s", "2d"]), 0)


class OverfolderTests(unittest.TestCase):
    def test_folds_air_and_pairs_to_a_half_pot_bet(self):
        board = ["2c", "7h", "9d"]
        for cards in (["As", "Kd"], ["9s", "3d"]):          # air, top pair
            s = state(cards, board, pot=600, owed=200, current_bet=200)
            self.assertEqual(overfolder.decide(s)["action"], "fold")

    def test_calls_two_pair_or_better(self):
        s = state(["9s", "7d"], ["9c", "7h", "2d"], pot=600, owed=200, current_bet=200)
        self.assertEqual(overfolder.decide(s)["action"], "call")

    def test_calls_a_tiny_bet_with_any_pair_but_folds_air(self):
        board = ["2c", "7h", "9d"]
        small = dict(pot=1000, owed=100, current_bet=100)      # 100 into 900 = 11% pressure
        self.assertEqual(overfolder.decide(state(["4s", "9d"], board, **small))["action"], "call")
        self.assertEqual(overfolder.decide(state(["As", "Kd"], board, **small))["action"], "fold")

    def test_bets_top_pair_when_checked_to_and_checks_air(self):
        board = ["2c", "7h", "9d"]
        bet = overfolder.decide(state(["9s", "3d"], board, pot=400))
        self.assertEqual(bet["action"], "raise")
        self.assertEqual(bet["amount"], 160)                    # 40% of the pot
        self.assertEqual(overfolder.decide(state(["As", "Kd"], board, pot=400))["action"], "check")

    def test_preflop_folds_weak_hands_to_a_raise_and_opens_strong_ones(self):
        facing = dict(street="preflop", pot=450, owed=250, current_bet=300, bet_this=0)
        self.assertEqual(overfolder.decide(state(["7s", "2d"], **facing))["action"], "fold")
        self.assertEqual(overfolder.decide(state(["Ts", "Td"], **facing))["action"], "call")
        first = state(["As", "Kd"], street="preflop", pot=150, owed=50, current_bet=100, bet_this=50)
        self.assertEqual(overfolder.decide(first), {"action": "raise", "amount": 250})


class TrapperTests(unittest.TestCase):
    def test_slowplays_a_set_on_the_flop(self):
        board = ["7c", "2h", "9d"]
        self.assertEqual(trapper.decide(state(["7s", "7d"], board, pot=400))["action"], "check")
        self.assertEqual(trapper.decide(state(["7s", "7d"], board, pot=600, owed=200, current_bet=200))["action"], "call")

    def test_springs_the_trap_on_the_turn_and_bets_big_on_the_river(self):
        turn = ["7c", "2h", "9d", "Kc"]
        raised = trapper.decide(state(["7s", "7d"], turn, pot=1000, owed=300, current_bet=300))
        self.assertEqual(raised, {"action": "raise", "amount": 900})   # 3x the bet
        river = ["7c", "2h", "9d", "Kc", "4s"]
        bet = trapper.decide(state(["7s", "7d"], river, pot=1000))
        self.assertEqual(bet, {"action": "raise", "amount": 900})      # 90% pot

    def test_never_bluffs_with_air(self):
        board = ["2c", "7h", "9d"]
        self.assertEqual(trapper.decide(state(["As", "Kd"], board, pot=400))["action"], "check")
        self.assertEqual(trapper.decide(state(["As", "Kd"], board, pot=600, owed=200, current_bet=200))["action"], "fold")

    def test_top_pair_bets_small_and_folds_to_a_big_river_bet(self):
        board = ["2c", "7h", "9d", "3s", "Jc"]
        self.assertEqual(trapper.decide(state(["Js", "5d"], board, pot=1000))["action"], "raise")
        big = state(["Js", "5d"], board, pot=1800, owed=800, current_bet=800)   # bet = 80% of the pot before it
        self.assertEqual(trapper.decide(big)["action"], "fold")

    def test_preflop_limp_trap_and_reraise(self):
        first = state(["As", "Ah"], street="preflop", pot=150, owed=50, current_bet=100, bet_this=50)
        self.assertEqual(trapper.decide(first)["action"], "call")                 # limp the aces
        facing = state(["As", "Ah"], street="preflop", pot=450, owed=250, current_bet=300, bet_this=0)
        self.assertEqual(trapper.decide(facing), {"action": "raise", "amount": 900})
        option = state(["As", "Ah"], street="preflop", pot=200, owed=0, current_bet=100, bet_this=100)
        self.assertEqual(trapper.decide(option), {"action": "raise", "amount": 300})


class SafetyAndDeterminismTests(unittest.TestCase):
    def test_warmup_call_is_harmless(self):
        for mod in (overfolder, trapper):
            self.assertEqual(mod.decide({"type": "warmup"}), {"action": "check"})

    def test_bad_input_falls_back_to_a_legal_action(self):
        for mod in (overfolder, trapper):
            self.assertEqual(mod.decide({"street": "flop", "can_check": True}), {"action": "check"})
            self.assertEqual(mod.decide({"street": "flop", "can_check": False}), {"action": "fold"})

    def test_short_stack_never_produces_an_illegal_raise(self):
        # Facing an all-in we cannot cover: a raise is impossible, so strong hands must just call.
        s = state(["7s", "7d"], ["7c", "2h", "9d", "Kc"], pot=3000, owed=2000, current_bet=2000, stack=1500)
        self.assertEqual(trapper.decide(s), {"action": "call"})
        # Bet that would exceed the stack becomes all-in.
        s = state(["7s", "7d"], ["7c", "2h", "9d", "Kc", "4s"], pot=5000, stack=1000)
        self.assertEqual(trapper.decide(s), {"action": "all_in"})

    def test_fuzz_actions_are_always_legal_and_deterministic(self):
        rng = random.Random(2024)
        for mod in (overfolder, trapper):
            for _ in range(3000):
                deck = DECK[:]
                rng.shuffle(deck)
                n_board = rng.choice([0, 3, 4, 5])
                bb = rng.choice([100, 200, 400, 1000])
                stack = rng.randint(0, 20000)
                bet_this = rng.choice([0, bb // 2, bb, rng.randint(0, 3000)])
                owed = rng.choice([0, 0, bb // 2, bb, rng.randint(1, 6000)])
                current_bet = bet_this + owed
                s = state(deck[:2], deck[2:2 + n_board], pot=rng.randint(2 * bb, 12000), owed=owed,
                          current_bet=current_bet, stack=stack, bet_this=bet_this, bb=bb,
                          min_raise=current_bet + max(bb, owed))
                first = mod.decide(s)
                self.assertEqual(first, mod.decide(dict(s)), "not deterministic")
                if s["your_stack"] == 0:
                    continue          # a bot with no chips is never asked to act
                self.assertTrue(is_legal(first, s), f"{mod.__name__}: illegal {first} for {s}")

    def test_modules_import_only_the_standard_library(self):
        import re
        for name in ("overfolder", "trapper"):
            text = (OPP / name / "bot.py").read_text()
            self.assertEqual(re.findall(r"^\s*(?:import|from)\s+(\w+)", text, re.M), [])
            for banned in ("open(", "eval(", "exec(", "subprocess", "socket", "random.", "print("):
                self.assertNotIn(banned, text, f"{name} uses {banned}")


if __name__ == "__main__":
    unittest.main()
