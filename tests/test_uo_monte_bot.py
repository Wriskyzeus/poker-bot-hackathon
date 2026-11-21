import importlib.util
import random
import unittest
from pathlib import Path
from unittest.mock import patch


BOT_PATH = Path(__file__).parents[1] / "my_bots" / "uo_monte" / "bot.py"
SPEC = importlib.util.spec_from_file_location("uo_monte_bot", BOT_PATH)
BOT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BOT)


def state(**overrides):
    result = {
        "type": "action_request",
        "street": "preflop",
        "your_cards": ["As", "Kd"],
        "community_cards": [],
        "blinds": {"sb": 50, "bb": 100, "ante": 0},
        "your_stack": 100,
        "your_bet_this_street": 0,
        "amount_owed": 100,
        "current_bet": 100,
        "min_raise_to": 200,
        "pot": 200,
        "can_check": False,
        "your_bot_id": "me",
        "seat_to_act": 0,
        "button_seat": 0,
        "action_log": [],
        "match_action_log": [],
        "players": [{"bot_id": "me"}, {"bot_id": "opponent"}],
    }
    result.update(overrides)
    return result


class RespondTests(unittest.TestCase):
    def test_fold_is_preserved_when_bet_covers_stack(self):
        self.assertEqual(BOT._respond("fold", state()), {"action": "fold"})

    def test_call_is_preserved_when_call_is_all_in(self):
        self.assertEqual(BOT._respond("call", state()), {"action": "call"})

    def test_check_is_preserved_with_short_stack(self):
        self.assertEqual(
            BOT._respond("check", state(amount_owed=0, current_bet=0, can_check=True)),
            {"action": "check"},
        )

    def test_short_stack_raise_becomes_all_in(self):
        self.assertEqual(
            BOT._respond(100, state(amount_owed=0, current_bet=0,
                                    min_raise_to=100, can_check=True)),
            {"action": "all_in"},
        )


class PostflopTests(unittest.TestCase):
    def postflop(self, **overrides):
        values = {
            "street": "flop",
            "your_cards": ["As", "Ad"],
            "community_cards": ["Ah", "7c", "2d"],
            "pot": 1000,
            "amount_owed": 0,
            "current_bet": 0,
            "min_raise_to": 100,
            "your_stack": 5000,
            "your_bet_this_street": 0,
            "can_check": True,
        }
        values.update(overrides)
        return state(**values)

    def test_no_cost_weak_hand_checks(self):
        with patch.object(BOT, "estimate_equity", return_value=0.30):
            self.assertEqual(BOT.decide(self.postflop()), {"action": "check"})

    def test_no_cost_strong_hand_value_bets(self):
        with patch.object(BOT, "estimate_equity", return_value=0.90):
            action = BOT.decide(self.postflop())
        self.assertEqual(action, {"action": "raise", "amount": 600})

    def test_facing_bet_calls_at_favorable_price(self):
        with patch.object(BOT, "estimate_equity", return_value=0.65):
            action = BOT.decide(self.postflop(amount_owed=200, pot=1000,
                                              current_bet=200, can_check=False))
        self.assertEqual(action, {"action": "call"})

    def test_facing_bet_folds_at_unfavorable_price(self):
        with patch.object(BOT, "estimate_equity", return_value=0.35):
            action = BOT.decide(self.postflop(amount_owed=800, pot=1000,
                                              current_bet=800, can_check=False))
        self.assertEqual(action, {"action": "fold"})

    def test_postflop_can_fold_when_bet_covers_stack(self):
        with patch.object(BOT, "estimate_equity", return_value=0.10):
            action = BOT.decide(self.postflop(street="river", your_cards=["2c", "3d"],
                                              community_cards=["Ks", "9d", "4h", "2s", "7c"],
                                              pot=4000, amount_owed=2000,
                                              current_bet=2000, your_stack=2000,
                                              can_check=False))
        self.assertEqual(action, {"action": "fold"})

    def test_short_stack_call_remains_call(self):
        with patch.object(BOT, "estimate_equity", return_value=0.80):
            action = BOT.decide(self.postflop(amount_owed=500, pot=1000,
                                              current_bet=500, your_stack=500,
                                              can_check=False))
        self.assertEqual(action, {"action": "call"})


class EquityTests(unittest.TestCase):
    def test_strong_and_weak_equity(self):
        strong = BOT.estimate_equity(["As", "Ad"], ["Ah", "7c", "2d"], 320, 11)
        weak = BOT.estimate_equity(["2c", "3d"], ["As", "Kd", "7h"], 320, 11)
        self.assertGreater(strong, 0.75)
        self.assertLess(weak, 0.35)

    def test_ties_count_as_half(self):
        equity = BOT.estimate_equity(
            ["2c", "3d"], ["Ts", "Js", "Qs", "Ks", "As"], 64, 3
        )
        self.assertEqual(equity, 0.5)

    def test_runouts_are_unique_and_reproducible(self):
        hero = ["As", "Kd"]
        board = ["2c", "7h", "Jd"]
        opponent, runout = BOT._sample_runout(hero, board, random.Random(9))
        self.assertEqual(len(opponent), 2)
        self.assertEqual(len(runout), 5)
        self.assertEqual(len(set(opponent + runout)), 7)
        self.assertTrue(set(hero).isdisjoint(opponent + runout))
        first = BOT.estimate_equity(hero, board, 64, 19)
        second = BOT.estimate_equity(hero, board, 64, 19)
        self.assertEqual(first, second)

    def test_flop_turn_and_river_are_supported(self):
        for board in (["2c", "7h", "Jd"], ["2c", "7h", "Jd", "4s"],
                      ["2c", "7h", "Jd", "4s", "9c"]):
            equity = BOT.estimate_equity(["As", "Kd"], board, 8, 5)
            self.assertGreaterEqual(equity, 0.0)
            self.assertLessEqual(equity, 1.0)


if __name__ == "__main__":
    unittest.main()
