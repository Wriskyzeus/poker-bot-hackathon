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
              errors=0, timeouts=0, with_end=True, log_seed=None, stacks=None, places=None,
              result_names=None):
    """Synthetic play.py event log: match_start + match_end for two seats."""
    start = {"type": "match_start", "core_hash": "abc123",
             "seats": [{"name": names[0], "seat": 0}, {"name": names[1], "seat": 1}]}
    if log_seed is not None:
        start["seed"] = log_seed
    results = []
    for idx, name in enumerate(result_names or names):
        results.append({"bot": name,
                        "place": places[idx] if places else (1 if idx == winner_idx else 2),
                        "final_stack": stacks[idx] if stacks else (20000 if idx == winner_idx else 0),
                        "decisions": 100, "avg_think_ms": 1.5, "max_think_ms": 9.0,
                        "timeouts": timeouts if idx == 1 else 0, "errors": errors if idx == 1 else 0,
                        "restarts": 0, "disabled": False})
    lines = ["garbage line", json.dumps(start)]
    if with_end:
        lines.append(json.dumps({"type": "match_end", "hands": hands, "stopped": stopped, "results": results}))
    return lines


def record(seed, order, winner_idx, exit_code=0, **kw):
    item = {"seed": seed, "order": order, "first": "x", "second": "y"}
    start, end = pe.read_log(log_lines(winner_idx=winner_idx, **kw))
    return pe.make_record(item, "cmd", "standard", 10000, "botA", "botB", start, end, exit_code, 1.0)


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


class CsvLoaderTests(unittest.TestCase):
    """QA issue 1: archived matches.csv must be re-scored with correctly typed seed and a_seat."""

    def setUp(self):
        # seed 1: A wins both (W); seed 2: one each (D); seed 3: B wins both (L)
        self.recs = [record(1, 1, 0), record(1, 2, 1), record(2, 1, 0), record(2, 2, 0),
                     record(3, 1, 1), record(3, 2, 0)]
        self.text = pe.csv_text(self.recs)

    def test_naive_string_seats_give_a_wrong_answer_and_the_loader_fixes_it(self):
        import csv as csvmod
        import io
        raw = list(csvmod.DictReader(io.StringIO(self.text)))
        self.assertIsInstance(raw[0]["a_seat"], str)
        # The old logic compared the string to 0: "0" == 0 is False, so every row looked like
        # 'order 2', one row overwrote the other, and every pair came out incomplete.
        naive = {}
        for rec in raw:
            naive.setdefault(rec["seed"], {})[1 if rec["a_seat"] == 0 else 2] = rec
        self.assertTrue(all(1 not in slot for slot in naive.values()))
        # Typed loading gives the right answer.
        self.assertEqual(pe.build_pairs(pe.load_records_csv(self.text)), {1: "W", 2: "D", 3: "L"})
        # build_pairs itself no longer trusts types: raw strings give the same right answer.
        self.assertEqual(pe.build_pairs(raw), {1: "W", 2: "D", 3: "L"})

    def test_loaded_values_are_typed(self):
        rec = pe.load_records_csv(self.text)[0]
        self.assertIsInstance(rec["seed"], int)
        self.assertIsInstance(rec["a_seat"], int)
        self.assertIsInstance(rec["a_final_stack"], int)
        self.assertIsInstance(rec["a_avg_think_ms"], float)
        self.assertIs(rec["a_disabled"], False)

    def test_round_trip_is_byte_identical_and_keeps_the_digest(self):
        loaded = pe.load_records_csv(self.text)
        self.assertEqual(pe.csv_text(loaded), self.text)
        self.assertEqual(pe.deterministic_digest(loaded), pe.deterministic_digest(self.recs))
        self.assertEqual(pe.summarize(loaded)["pair_wdl_for_A"], {"W": 1, "D": 1, "L": 1})

    def test_corrupt_files_are_rejected_with_a_line_number(self):
        lines = self.text.rstrip("\n").split("\n")
        header = lines[0].split(",")
        col = {name: i for i, name in enumerate(header)}

        def edited(row_index, column, value):
            cells = lines[row_index].split(",")
            cells[col[column]] = value
            return "\n".join(lines[:row_index] + [",".join(cells)] + lines[row_index + 1:]) + "\n"

        cases = {
            "seat 2": edited(1, "a_seat", "2"),
            "text seed": edited(1, "seed", "abc"),
            "bad status": edited(1, "status", "fine"),
            "ok without winner": edited(1, "winner", ""),
            "winner on incomplete": edited(1, "status", "incomplete:timeout"),
            "text number": edited(1, "hands", "many"),
            "bad bool": edited(1, "a_disabled", "maybe"),
            "mixed bots": edited(2, "bot_a", "other"),
            "duplicate row": self.text + lines[1] + "\n",
        }
        for name, bad in cases.items():
            with self.subTest(name):
                with self.assertRaises(ValueError):
                    pe.load_records_csv(bad)
        with self.assertRaises(ValueError):
            pe.load_records_csv("seed,a_seat\n1,0\n")          # missing columns
        with self.assertRaises(ValueError):
            pe.load_records_csv(lines[0] + "\n")               # no rows

    def test_duplicate_seed_and_seat_never_silently_overwrites(self):
        with self.assertRaises(ValueError):
            pe.build_pairs([record(1, 1, 0), record(1, 1, 1)])

    def test_bad_seat_in_build_pairs_raises(self):
        bad = dict(record(1, 1, 0), a_seat="x")
        with self.assertRaises(ValueError):
            pe.build_pairs([bad])

    def test_rescore_command_matches_the_original_summary(self):
        import io
        import tempfile
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "matches.csv"
            path.write_text(self.text)
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = pe.main(["--rescore", str(path)])
            self.assertEqual(code, 0)
            self.assertIn("A: 1 won, 1 drawn, 1 lost", buf.getvalue())
            self.assertIn(pe.deterministic_digest(self.recs), buf.getvalue())
            self.assertEqual(pe.main(["--rescore", str(Path(tmp) / "missing.csv")]), 2)


class RunnerFailureTests(unittest.TestCase):
    """QA issue 2: a crash or inconsistent log must never count as a clean match."""

    def test_nonzero_exit_code_is_an_error_even_with_a_complete_log(self):
        rec = record(1, 1, 0, exit_code=1)
        self.assertEqual(rec["status"], "error:exit_code=1")
        self.assertEqual(rec["winner"], "")
        s = pe.summarize([rec, record(1, 2, 1)])
        self.assertEqual(s["matches_error"], 1)
        self.assertEqual(s["pairs_incomplete"], 1)
        self.assertEqual(s["matches_complete"], 1)
        self.assertIn("error:exit_code=1", s["incomplete_reasons"])
        self.assertIn("nonzero runner exit code", pe.format_report(s, "a", "b"))

    def test_nonzero_exit_code_without_any_log_is_an_error(self):
        item = {"seed": 1, "order": 1, "first": "x", "second": "y"}
        rec = pe.make_record(item, "cmd", "standard", 10000, "a", "b", None, None, 137, 1.0)
        self.assertEqual(rec["status"], "error:exit_code=137")

    def test_zero_exit_with_no_log_is_incomplete(self):
        self.assertEqual(record(1, 1, 0, with_end=False)["status"], "incomplete:no_match_end")

    def test_inconsistent_logs_are_flagged_not_trusted(self):
        cases = {
            "chips_not_conserved": dict(stacks=[20000, 500]),
            "loser_has_chips": dict(stacks=[15000, 5000]),
            "places_not_1_and_2": dict(places=[1, 1]),
            "results_do_not_match_seats": dict(result_names=("A_bot", "someone_else")),
            "seed_mismatch": dict(log_seed=99),
            "non_numeric_fields": dict(stacks=["lots", 0]),
        }
        for reason, kwargs in cases.items():
            with self.subTest(reason):
                rec = record(1, 1, 0, **kwargs)
                self.assertEqual(rec["status"], f"incomplete:inconsistent_log:{reason}")
                self.assertEqual(rec["winner"], "")

    def test_matching_seed_in_the_log_is_accepted(self):
        self.assertEqual(record(7, 1, 0, log_seed=7)["status"], "ok")

    def test_duplicate_bot_names_in_one_log_are_flagged(self):
        item = {"seed": 1, "order": 1, "first": "x", "second": "y"}
        start, end = pe.read_log(log_lines(names=("same", "same")))
        rec = pe.make_record(item, "cmd", "standard", 10000, "a", "b", start, end, 0, 1.0)
        self.assertEqual(rec["status"], "incomplete:expected_two_distinct_seats")


class ClusterIntervalTests(unittest.TestCase):
    """QA issue 3: intervals resample whole seeds; Wilson is not claimed to be conservative."""

    def pair_records(self, outcomes):
        """outcomes: per seed, (winner_idx_order1, winner_idx_order2)."""
        out = []
        for seed, (w1, w2) in enumerate(outcomes, start=1):
            out += [record(seed, 1, w1), record(seed, 2, w2)]
        return out

    def test_cluster_bootstrap_is_reproducible_and_brackets_the_rate(self):
        clusters = [(2, 2), (0, 2), (1, 2), (2, 2), (1, 2), (0, 2)]
        first, second = pe.cluster_bootstrap_rate(clusters), pe.cluster_bootstrap_rate(clusters)
        self.assertEqual(first, second)
        rate = sum(c[0] for c in clusters) / sum(c[1] for c in clusters)
        self.assertLessEqual(first[0], rate)
        self.assertGreaterEqual(first[1], rate)
        self.assertIsNone(pe.cluster_bootstrap_rate([]))
        self.assertIsNone(pe.cluster_bootstrap_rate([(0, 0)]))

    def test_correlated_pairs_make_the_interval_wider_than_wilson(self):
        # Both matches of a seed always agree: A wins both or loses both.
        clusters = [(2, 2)] * 10 + [(0, 2)] * 10
        lo, hi = pe.cluster_bootstrap_rate(clusters)
        wlo, whi = pe.wilson_interval(20, 40)
        self.assertGreater(hi - lo, whi - wlo)

    def test_anti_correlated_pairs_make_it_narrower_so_wilson_is_not_always_conservative(self):
        # Every seed is split one each: the match rate is pinned at exactly 50%.
        clusters = [(1, 2)] * 20
        lo, hi = pe.cluster_bootstrap_rate(clusters)
        wlo, whi = pe.wilson_interval(20, 40)
        self.assertEqual((lo, hi), (0.5, 0.5))
        self.assertLess(hi - lo, whi - wlo)

    def test_summary_uses_cluster_intervals_and_labels_them(self):
        s = pe.summarize(self.pair_records([(0, 1), (0, 0), (1, 0)]))
        for key in ("match_wins_A", "A_in_first_seat", "A_in_second_seat"):
            self.assertEqual(s[key]["ci_method"], "cluster bootstrap over seeds")
        report = pe.format_report(s, "a", "b")
        self.assertIn("cluster bootstrap", report)
        self.assertNotIn("Wilson", report)

    def test_seat_strata_use_one_match_per_seed(self):
        s = pe.summarize(self.pair_records([(0, 1), (0, 0), (1, 0)]))
        self.assertEqual((s["A_in_first_seat"]["wins"], s["A_in_first_seat"]["n"]), (2, 3))
        self.assertEqual(s["A_in_first_seat"]["seeds"], 3)

    def test_small_or_degenerate_samples_are_flagged(self):
        small = pe.summarize(self.pair_records([(0, 1), (0, 0)]))
        self.assertIn("unreliable", small["pair_score_ci_note"])
        same = pe.summarize(self.pair_records([(0, 1)] * 25))      # 25 pairs, all wins
        self.assertIn("degenerate", same["pair_score_ci_note"])
        mixed = pe.summarize(self.pair_records([(0, 1)] * 13 + [(1, 0)] * 12))
        self.assertEqual(mixed["pair_score_ci_note"], "")
        self.assertIn("WARNING", pe.format_report(small, "a", "b"))

    def test_assumptions_distinguish_team_score_from_organiser_ranking(self):
        text = " ".join(pe.ASSUMPTIONS)
        self.assertIn("not the organiser's ranking score", text)
        self.assertIn("NOT independent", text)
        self.assertNotIn("they are conservative for head-to-head", text)


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
