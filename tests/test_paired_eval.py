"""Self-tests for benchmarks/paired_eval.py.

Run from the repo root (no pytest needed):
    python3 -m unittest tests.test_paired_eval -v        # if tests/ is importable
    python3 tests/test_paired_eval.py -v                  # always works

All tests except the last use synthetic data and never start a match. The last
one plays a single real match with bots/caller vs bots/template on seed 41 and
is skipped if the kit's libraries are missing.
"""

import json
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "benchmarks"))

import paired_eval as pe  # noqa: E402


def log_lines(names=("A_bot", "B_bot"), winner_idx=0, stopped="one_player_left", hands=57,
              errors=0, timeouts=0, with_end=True):
    """Synthetic play.py event log: match_start + match_end for two seats."""
    start = {"type": "match_start", "core_hash": "abc123",
             "seats": [{"name": names[0], "seat": 0}, {"name": names[1], "seat": 1}]}
    results = []
    for idx, name in enumerate(names):
        results.append({"bot": name, "place": 1 if idx == winner_idx else 2,
                        "final_stack": 20000 if idx == winner_idx else 0,
                        "decisions": 100, "avg_think_ms": 1.5, "max_think_ms": 9.0,
                        "timeouts": timeouts if idx == 1 else 0, "errors": errors if idx == 1 else 0,
                        "restarts": 0, "disabled": False})
    lines = ["garbage line", json.dumps(start)]
    if with_end:
        lines.append(json.dumps({"type": "match_end", "hands": hands, "stopped": stopped, "results": results}))
    return lines


def record(seed, order, winner_idx, **kw):
    item = {"seed": seed, "order": order, "first": "x", "second": "y"}
    start, end = pe.read_log(log_lines(winner_idx=winner_idx, **kw))
    return pe.make_record(item, "cmd", "standard", 10000, "botA", "botB", start, end, 0, 1.0)


class SeatSwapTests(unittest.TestCase):
    def test_second_match_swaps_the_seats_and_keeps_the_seed(self):
        plan = pe.plan_matches([41, 42], "botA", "botB")
        self.assertEqual(len(plan), 4)
        for seed in (41, 42):
            o1 = next(p for p in plan if p["seed"] == seed and p["order"] == 1)
            o2 = next(p for p in plan if p["seed"] == seed and p["order"] == 2)
            self.assertEqual((o1["first"], o1["second"]), ("botA", "botB"))
            self.assertEqual((o2["first"], o2["second"]), ("botB", "botA"))
            c1 = pe.build_command("py", "play.py", o1["first"], o1["second"], seed, "standard", 10000, "L")
            c2 = pe.build_command("py", "play.py", o2["first"], o2["second"], seed, "standard", 10000, "L")
            self.assertEqual(c1[c1.index("--seed") + 1], c2[c2.index("--seed") + 1])
            self.assertEqual(c1[2:4], c2[2:4][::-1])
            self.assertEqual(c1[4:], c2[4:])           # every other option identical

    def test_roles_follow_the_seat_not_the_engine_name(self):
        # Order 2: B sits in seat 0. The engine's winner is seat 0, which is B.
        rec = record(41, 2, winner_idx=0)
        self.assertEqual((rec["a_seat"], rec["winner"]), (1, "B"))
        self.assertEqual(rec["b_final_stack"], 20000)
        self.assertEqual(rec["a_final_stack"], 0)
        # Order 1: A sits in seat 0, so seat 0 winning means A.
        rec = record(41, 1, winner_idx=0)
        self.assertEqual((rec["a_seat"], rec["winner"]), (0, "A"))

    def test_identical_folder_names_do_not_confuse_roles(self):
        # play.py renames a duplicate folder name to name_2; roles come from seat order.
        rec = record(41, 1, winner_idx=1, names=("uo_monte", "uo_monte_2"))
        self.assertEqual(rec["winner"], "B")


class PairScoringTests(unittest.TestCase):
    def test_pair_outcomes(self):
        self.assertEqual(pe.score_pair("A", "A"), "W")
        self.assertEqual(pe.score_pair("A", "B"), "D")
        self.assertEqual(pe.score_pair("B", "A"), "D")
        self.assertEqual(pe.score_pair("B", "B"), "L")

    def test_incomplete_match_makes_the_pair_incomplete_not_guessed(self):
        self.assertEqual(pe.score_pair("A", ""), "incomplete")
        self.assertEqual(pe.score_pair("", ""), "incomplete")

    def test_build_pairs_from_records(self):
        recs = [record(1, 1, 0), record(1, 2, 1),      # seed 1: A wins both
                record(2, 1, 0), record(2, 2, 0),      # seed 2: A wins as seat 0, B wins as seat 0 -> draw
                record(3, 1, 1), record(3, 2, 0)]      # seed 3: B wins both
        self.assertEqual(pe.build_pairs(recs), {1: "W", 2: "D", 3: "L"})

    def test_missing_second_match_is_incomplete(self):
        self.assertEqual(pe.build_pairs([record(7, 1, 0)]), {7: "incomplete"})

    def test_summary_counts(self):
        recs = [record(1, 1, 0), record(1, 2, 1), record(2, 1, 0), record(2, 2, 0)]
        s = pe.summarize(recs)
        self.assertEqual(s["pair_wdl_for_A"], {"W": 1, "D": 1, "L": 0})
        self.assertAlmostEqual(s["pair_score_for_A"], 0.75)
        self.assertEqual(s["match_wins_A"]["wins"], 3)
        self.assertEqual(s["match_wins_A"]["n"], 4)
        self.assertEqual(s["A_in_first_seat"]["wins"], 2)
        self.assertEqual(s["A_in_second_seat"]["wins"], 1)


class IncompleteAndErrorTests(unittest.TestCase):
    def test_hand_limit_is_incomplete(self):
        self.assertEqual(record(1, 1, 0, stopped="hand_limit")["status"], "incomplete:stopped=hand_limit")
        self.assertEqual(record(1, 1, 0, stopped="hand_limit")["winner"], "")

    def test_missing_match_end_is_incomplete(self):
        self.assertEqual(record(1, 1, 0, with_end=False)["status"], "incomplete:no_match_end")

    def test_engine_error_stop_is_incomplete(self):
        self.assertTrue(record(1, 1, 0, stopped="error: ValueError()")["status"].startswith("incomplete"))

    def test_timeout_note_is_incomplete(self):
        item = {"seed": 1, "order": 1, "first": "x", "second": "y"}
        rec = pe.make_record(item, "cmd", "standard", 10000, "a", "b", None, None, "", 5.0, note="timeout")
        self.assertEqual(rec["status"], "incomplete:timeout")

    def test_bot_errors_are_reported_but_the_match_still_counts(self):
        rec = record(1, 1, 0, errors=2, timeouts=1)
        self.assertEqual(rec["status"], "ok")
        s = pe.summarize([rec])
        self.assertEqual(s["problem_counts_both_bots"], {"timeouts": 1, "errors": 2, "restarts": 0})

    def test_incomplete_matches_are_excluded_from_win_rates(self):
        s = pe.summarize([record(1, 1, 0), record(1, 2, 1, stopped="hand_limit")])
        self.assertEqual(s["matches_complete"], 1)
        self.assertEqual(s["pairs_incomplete"], 1)
        self.assertEqual(s["match_wins_A"]["n"], 1)


class StatisticsTests(unittest.TestCase):
    def test_wilson_known_values(self):
        lo, hi = pe.wilson_interval(20, 40)
        self.assertAlmostEqual(lo, 0.352, places=3)
        self.assertAlmostEqual(hi, 0.648, places=3)
        lo, hi = pe.wilson_interval(31, 40)
        self.assertAlmostEqual(lo, 0.625, places=3)
        self.assertAlmostEqual(hi, 0.877, places=3)

    def test_wilson_edges(self):
        self.assertEqual(pe.wilson_interval(0, 0), (0.0, 1.0))
        lo, hi = pe.wilson_interval(0, 10)
        self.assertEqual(lo, 0.0)
        self.assertGreater(hi, 0.2)
        lo, hi = pe.wilson_interval(10, 10)
        self.assertLess(lo, 0.8)
        self.assertEqual(hi, 1.0)

    def test_bootstrap_is_reproducible_and_brackets_the_mean(self):
        values = [1.0, 0.5, 0.0, 1.0, 0.5, 0.5, 1.0, 0.0]
        first, second = pe.bootstrap_mean_ci(values), pe.bootstrap_mean_ci(values)
        self.assertEqual(first, second)
        self.assertLessEqual(first[0], sum(values) / len(values))
        self.assertGreaterEqual(first[1], sum(values) / len(values))
        self.assertIsNone(pe.bootstrap_mean_ci([]))


class DeterministicOutputTests(unittest.TestCase):
    def setUp(self):
        self.recs = [record(s, o, (s + o) % 2) for s in (3, 1, 2) for o in (2, 1)]

    def test_csv_is_byte_identical_whatever_the_input_order(self):
        shuffled = list(self.recs)
        random.Random(1).shuffle(shuffled)
        self.assertEqual(pe.csv_text(self.recs), pe.csv_text(shuffled))
        self.assertEqual(pe.pairs_text(self.recs), pe.pairs_text(shuffled))

    def test_csv_has_fixed_header_sorted_rows_and_lf_endings(self):
        text = pe.csv_text(self.recs)
        lines = text.split("\n")
        self.assertEqual(lines[0], ",".join(pe.CSV_COLUMNS))
        self.assertNotIn("\r", text)
        keys = [tuple(line.split(",")[:2]) for line in lines[1:] if line]
        self.assertEqual(keys, sorted(keys))

    def test_digest_ignores_timing_but_not_results(self):
        base = pe.deterministic_digest(self.recs)
        slower = [dict(r, a_avg_think_ms=999.0, duration_s=50.0, exit_code=1) for r in self.recs]
        self.assertEqual(base, pe.deterministic_digest(slower))
        flipped = [dict(r) for r in self.recs]
        flipped[0]["winner"] = "B" if flipped[0]["winner"] == "A" else "A"
        self.assertNotEqual(base, pe.deterministic_digest(flipped))

    def test_unavailable_runner_fields_are_documented(self):
        self.assertTrue(any("p95" in text for text in pe.UNAVAILABLE_FIELDS))


class SeedGuardTests(unittest.TestCase):
    def test_parsing(self):
        self.assertEqual(pe.parse_seeds("41-43,50"), [41, 42, 43, 50])

    def test_sealed_seeds_are_refused_by_default(self):
        for text in ("1001", "1000-1002", "1200", "1-5,1100"):
            with self.assertRaises(ValueError):
                pe.parse_seeds(text)
        self.assertEqual(pe.parse_seeds("1001-1002", allow_sealed=True), [1001, 1002])
        self.assertEqual(pe.parse_seeds("1201"), [1201])
        self.assertEqual(pe.parse_seeds("1000"), [1000])

    def test_bad_input(self):
        for text in ("", "5-3", "1,1"):
            with self.assertRaises(ValueError):
                pe.parse_seeds(text)


@unittest.skipUnless((REPO / "play.py").exists(), "play.py not found")
class EndToEndSmokeTest(unittest.TestCase):
    """One real match through the official runner. Seed 41 only; not a strength claim."""

    def test_single_seed_runs_and_scores_a_pair(self):
        try:
            import eval7  # noqa: F401
        except ImportError:
            self.skipTest("eval7 not installed in this interpreter")
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            code = pe.main(["bots/caller", "bots/template", "--seeds", "41", "--out-dir", tmp])
            self.assertIn(code, (0, 2))
            self.assertTrue((Path(tmp) / "matches.csv").exists())
            self.assertTrue((Path(tmp) / "manifest.json").exists())
            rows = (Path(tmp) / "matches.csv").read_text().splitlines()
            self.assertEqual(len(rows), 3)          # header + 2 matches (both seatings)
            manifest = json.loads((Path(tmp) / "manifest.json").read_text())
            self.assertEqual(manifest["seeds"], [41])


if __name__ == "__main__":
    unittest.main()
