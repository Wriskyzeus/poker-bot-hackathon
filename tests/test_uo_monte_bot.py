import importlib.util
import unittest
from pathlib import Path


BOT_PATH = Path(__file__).parents[1] / "my_bots" / "uo_monte" / "bot.py"
SPEC = importlib.util.spec_from_file_location("uo_monte_bot", BOT_PATH)
BOT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BOT)


def state(**overrides):
    result = {
        "type": "action_request",
        "street": "preflop",
        "your_cards": ["As", "Kd"],
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
    def test_postflop_can_fold_when_bet_covers_stack(self):
        self.assertEqual(
            BOT.decide(state(street="river", your_cards=["2c", "3d"], pot=4000,
                             amount_owed=2000, your_stack=2000, can_check=False)),
            {"action": "fold"},
        )


if __name__ == "__main__":
    unittest.main()
