import importlib.util
import random
import unittest
from pathlib import Path
from unittest.mock import patch

import eval7


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


class RiverDefenseTests(unittest.TestCase):
    def river(self, owed=650, **overrides):
        values = {
            "street": "river", "hand_num": 20,
            "your_cards": ["Kc", "5d"],
            "community_cards": ["3s", "Qd", "Ks", "Ts", "7s"],
            "pot": 1100 + owed, "amount_owed": owed, "current_bet": owed,
            "min_raise_to": 2 * owed, "your_stack": 4000,
            "action_log": [{"bot_id": "opponent", "street": "river", "action": "raise"}],
        }
        values.update(overrides)
        return state(**values)

    def history(self, actions):
        return [{"bot_id": "opponent", "street": "river", "hand_num": hand, "action": action}
                for hand, action in enumerate(actions)]

    def test_rare_value_bet_folds_the_same_hand_that_catches_frequent_bluffs(self):
        selective = self.history(["check"] * 11 + ["raise"])
        frequent = self.history(["raise"] * 10 + ["check"] * 2)
        self.assertEqual(BOT.decide(self.river(match_action_log=selective)), {"action": "fold"})
        self.assertEqual(BOT.decide(self.river(match_action_log=frequent)), {"action": "call"})

    def test_large_bet_after_multiple_barrels_folds_a_marginal_bluff_catcher(self):
        history = self.history(["raise"] * 3)
        self.assertEqual(BOT.decide(self.river(match_action_log=history)), {"action": "call"})
        actions = [{"bot_id": "opponent", "street": street, "action": "raise"}
                   for street in ("flop", "turn", "river")]
        self.assertEqual(BOT.decide(self.river(owed=1600, action_log=actions,
                                              match_action_log=history)), {"action": "fold"})

    def test_missing_history_and_repeated_actions_use_a_conservative_prior(self):
        self.assertEqual(BOT.decide(self.river()), {"action": "fold"})
        history = self.history(["raise"])
        self.assertEqual(BOT._river_aggression(self.river(match_action_log=history * 20),
                                               "opponent"),
                         BOT._river_aggression(self.river(match_action_log=history), "opponent"))

    def test_nut_flush_can_reraise_without_history(self):
        action = BOT.decide(self.river(your_cards=["As", "Js"]))
        self.assertEqual(action, {"action": "raise", "amount": 1560})

    def test_covered_call_uses_only_contestable_chips(self):
        with patch.object(BOT, "_river_range_equity", return_value=(0.28, 0.0)):
            action = BOT.decide(self.river(owed=800, pot=1200, your_stack=200))
        self.assertEqual(action, {"action": "call"})

    def test_river_checked_to_hero_keeps_v2_value_bet(self):
        with patch.object(BOT, "estimate_equity", return_value=0.90):
            action = BOT.decide(self.river(owed=0, can_check=True))
        self.assertEqual(action, {"action": "raise", "amount": 660})


class StackCommitmentTests(unittest.TestCase):
    def facing(self, **overrides):
        values = {
            "street": "flop", "hand_num": 20, "your_cards": ["7h", "Ah"],
            "community_cards": ["Ad", "5s", "Qd"],
            "pot": 1740, "amount_owed": 640, "current_bet": 940,
            "your_bet_this_street": 300, "min_raise_to": 1580, "your_stack": 9280,
            "players": [{"bot_id": "me", "stack": 9280},
                        {"bot_id": "opponent", "stack": 8980}],
            "action_log": [{"bot_id": bot, "street": "flop", "action": "raise", "amount": amount}
                           for bot, amount in (("me", 300), ("opponent", 940))],
        }
        values.update(overrides)
        return state(**values)

    def test_made_hand_classes_distinguish_hole_card_strength(self):
        for hole, board, expected in (
            ("Ah 7h", "Ad 5s Qd", "top pair"),
            ("As Ac", "Kd 5s Qd", "overpair"),
            ("Ah Qh", "Ad 5s Qd", "two pair"),
            ("Ah Ad", "Ac 5s Qd", "set"),
            ("Ah 7h", "Ad Ac Qd", "trips"),
            ("Ah 7h", "Ad 5s 5d", "top pair"),
            ("8h 9h", "Td Js Qd", "straight"),
            ("Ah 7h", "Jh 5h Qh", "flush"),
        ):
            with self.subTest(hole=hole, board=board):
                cards = hole.split() + board.split()
                score = eval7.evaluate([eval7.Card(card) for card in cards])
                self.assertEqual(BOT._commitment_hand(hole.split(), board.split(), score), expected)

    def test_live_draw_requires_a_hole_card_contribution(self):
        self.assertTrue(BOT._live_draw(["Ah", "7h"], ["Jh", "5h", "Qc"]))
        self.assertTrue(BOT._live_draw(["8h", "9h"], ["Td", "Js", "2c"]))
        self.assertFalse(BOT._live_draw(["Ah", "2c"], ["5d", "6d", "7d", "8d"]))

    def test_original_deep_top_pair_reraise_turns_into_a_call(self):
        self.assertEqual(BOT.decide(self.facing()), {"action": "call"})

    def test_set_can_reraise_for_value(self):
        self.assertEqual(BOT.decide(self.facing(your_cards=["5h", "5c"])),
                         {"action": "raise", "amount": 1580})

    def test_low_effective_spr_allows_top_pair_value_raise(self):
        state = self.facing(your_cards=["Ah", "Kh"], your_bet_this_street=0, pot=2300,
                            amount_owed=400, current_bet=400, min_raise_to=800,
                            action_log=[{"bot_id": "opponent", "street": "flop", "action": "raise"}],
                            players=[{"bot_id": "me", "stack": 9280},
                                     {"bot_id": "opponent", "stack": 500}])
        with patch.object(BOT, "_commitment_equity", return_value=(0.72, 0.65)):
            self.assertEqual(BOT.decide(state), {"action": "raise", "amount": 900})

    def test_historical_aggression_keeps_a_borderline_bluff_catcher(self):
        def history(action):
            return [{"bot_id": "opponent", "hand_num": hand, "street": street, "action": action}
                    for hand in range(16) for street in ("flop", "turn", "river")]

        state = self.facing(pot=1300, amount_owed=640, your_stack=750,
                            players=[{"bot_id": "me", "stack": 750},
                                     {"bot_id": "opponent", "stack": 110}])
        with patch.object(BOT, "_commitment_equity", return_value=(0.43, 0.32)):
            self.assertEqual(BOT.decide(dict(state, match_action_log=history("check"))),
                             {"action": "fold"})
            self.assertEqual(BOT.decide(dict(state, match_action_log=history("raise"))),
                             {"action": "call"})

    def test_covered_weak_hand_can_fold_and_strong_hand_calls(self):
        state = self.facing(your_stack=640)
        self.assertEqual(BOT.decide(dict(state, your_cards=["2h", "7c"])), {"action": "fold"})
        self.assertEqual(BOT.decide(dict(state, your_cards=["5h", "5c"])), {"action": "call"})

    def test_value_raise_with_a_short_hero_stack_is_a_legal_all_in(self):
        state = self.facing(your_stack=900, your_cards=["5h", "5c"])
        self.assertEqual(BOT.decide(state), {"action": "all_in"})

    def test_value_hand_calls_when_the_only_opponent_is_already_all_in(self):
        state = self.facing(your_cards=["5h", "5c"],
                            players=[{"bot_id": "me", "stack": 9280},
                                     {"bot_id": "opponent", "stack": 0}])
        self.assertEqual(BOT.decide(state), {"action": "call"})


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
