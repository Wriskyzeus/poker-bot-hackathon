#!/usr/bin/env python3
"""Paired-seat (duplicate) benchmark harness for the Fullhouse poker kit.

Runs two bots head to head with the official ``play.py``. Every seed is played
TWICE: once with bot A in the first seat, once with bot B in the first seat.
The engine derives each hand's cards from the match seed and the hand number
only, so both matches deal the same cards per seat and only the seating
changes. That is the organiser's duplicate pairing (docs/official-starter-kit.md):
winning both matches wins the pairing, one each is a draw.

This is a development tool. It never touches hidden cards, never patches the
engine, and never changes a bot. It only launches ``play.py`` and reads the
JSON-lines event log that ``play.py --log`` writes.

Example:
    python3 benchmarks/paired_eval.py my_bots/uo_monte bots/caller --seeds 41-43

See benchmarks/README.md for the output format, scoring and limitations.
"""

import argparse
import csv
import hashlib
import json
import math
import platform
import random
import shlex
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

# Seeds reserved for the final release-candidate evaluation. Using them for
# tuning would turn them into development data, so the tool refuses by default.
SEALED_SEEDS = range(1001, 1201)

LOG_PLACEHOLDER = "<LOG>"

# One row per match. Column order is fixed so output is byte-stable.
CSV_COLUMNS = [
    "seed", "a_seat", "bot_a", "bot_b", "blinds", "starting_stack",
    "status", "winner", "stopped", "hands",
    "a_final_stack", "b_final_stack",
    "a_decisions", "b_decisions",
    "a_timeouts", "b_timeouts", "a_errors", "b_errors",
    "a_restarts", "b_restarts", "a_disabled", "b_disabled",
    "a_avg_think_ms", "b_avg_think_ms", "a_max_think_ms", "b_max_think_ms",
    "duration_s", "exit_code", "core_hash", "command",
]

# Columns that depend on machine speed or process health rather than on the
# cards and the bots' decisions. They are excluded from the determinism digest.
RUNTIME_COLUMNS = {
    "a_timeouts", "b_timeouts", "a_errors", "b_errors", "a_restarts", "b_restarts",
    "a_disabled", "b_disabled", "a_avg_think_ms", "b_avg_think_ms",
    "a_max_think_ms", "b_max_think_ms", "duration_s", "exit_code",
}

UNAVAILABLE_FIELDS = [
    "p95/p99 decision time (the runner reports only average and maximum per bot)",
    "per-decision latency (only in the optional --keep-logs event logs)",
    "bb/100 is not recorded: duplicate scoring uses match winners, not chip counts",
]

ASSUMPTIONS = [
    "Seeds are the unit of analysis: the two matches of one seed share the same cards, so they are NOT "
    "independent. Every interval resamples whole seeds (pairs) with replacement and treats different seeds as "
    "independent and identically distributed.",
    "Match win-rate intervals (overall and per seat) are percentile cluster-bootstrap intervals over pairs "
    "(2000 resamples, fixed RNG seed). No claim is made that they are conservative or anti-conservative; "
    "they are only as good as the i.i.d.-seeds assumption.",
    "Pair-score intervals are percentile bootstrap over pairs with the same settings. With fewer than "
    "20 pairs, or when every pair has the same outcome, the interval is degenerate or unreliable and is flagged.",
    "Only matches with status 'ok' are scored. A nonzero play.py exit code (status 'error:exit_code=N'), an "
    "inconsistent log or a missing match_end makes the match, and therefore its pair, excluded and visible.",
    "Team pair score = (wins + 0.5 x draws) / pairs is OUR comparison convention. The organiser's documented "
    "rule only defines a win/draw/loss per pairing; how draws are weighted in the final ranking is not stated "
    "in the source, so this number is not the organiser's ranking score.",
]

MIN_PAIRS_FOR_CI = 20

# Typed columns, used when archived matches.csv files are loaded back.
INT_COLUMNS = {
    "seed", "a_seat", "starting_stack", "hands", "a_final_stack", "b_final_stack",
    "a_decisions", "b_decisions", "a_timeouts", "b_timeouts", "a_errors", "b_errors",
    "a_restarts", "b_restarts", "exit_code",
}
FLOAT_COLUMNS = {"a_avg_think_ms", "b_avg_think_ms", "a_max_think_ms", "b_max_think_ms", "duration_s"}
BOOL_COLUMNS = {"a_disabled", "b_disabled"}
REQUIRED_COLUMNS = {"seed", "a_seat", "bot_a", "bot_b", "status", "winner"}


# --------------------------------------------------------------------------- #
# Seeds and command planning
# --------------------------------------------------------------------------- #

def parse_seeds(text, allow_sealed=False):
    """'41-43,50' -> [41, 42, 43, 50]. Refuses sealed seeds unless allowed."""
    seeds = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = (int(x) for x in part.split("-", 1))
            if hi < lo:
                raise ValueError(f"bad seed range {part!r}")
            seeds.extend(range(lo, hi + 1))
        else:
            seeds.append(int(part))
    if not seeds:
        raise ValueError("no seeds given")
    if len(set(seeds)) != len(seeds):
        raise ValueError("duplicate seeds in list")
    blocked = [s for s in seeds if s in SEALED_SEEDS]
    if blocked and not allow_sealed:
        raise ValueError(
            f"seeds {blocked[0]}..{blocked[-1]} are in the sealed range "
            f"{SEALED_SEEDS.start}-{SEALED_SEEDS.stop - 1}; "
            "pass --allow-sealed only for the human-approved final run")
    return seeds


def build_command(python, play_py, first, second, seed, blinds, stack,
                  log_path, hands_cap=None, docker=False):
    """The exact play.py command. The first bot is seat 0."""
    cmd = [str(python), str(play_py), str(first), str(second), "--seed", str(seed),
           "--blinds", str(blinds), "--stack", str(stack), "--log", str(log_path)]
    if hands_cap is not None:
        cmd += ["--hands", str(hands_cap)]
    if docker:
        cmd.append("--docker")
    return cmd


def plan_matches(seeds, bot_a, bot_b):
    """Two matches per seed. order 1: A in seat 0. order 2: B in seat 0 (swapped)."""
    plan = []
    for seed in seeds:
        plan.append({"seed": seed, "order": 1, "first": bot_a, "second": bot_b})
        plan.append({"seed": seed, "order": 2, "first": bot_b, "second": bot_a})
    return plan


# --------------------------------------------------------------------------- #
# Reading play.py's event log
# --------------------------------------------------------------------------- #

def read_log(lines):
    """Return (match_start, match_end) events from JSON lines; ignores bad lines."""
    start = end = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "match_start":
            start = event
        elif event.get("type") == "match_end":
            end = event
    return start, end


def _blank_record():
    return {col: "" for col in CSV_COLUMNS}


def _as_int(value):
    """int(value) for ints and integral numbers; None for anything else (bool excluded)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def make_record(item, command_text, blinds, stack, bot_a, bot_b,
                start, end, exit_code, wall_s, note=""):
    """Build one CSV row from a parsed log. Never raises on missing data.

    Status is 'ok' only when the process exited 0 AND the log is complete and
    self-consistent. Otherwise it is 'incomplete:<why>' or 'error:exit_code=N';
    those matches are excluded from scoring but stay visible in every report.
    """
    rec = _blank_record()
    rec.update({
        "seed": item["seed"], "a_seat": 0 if item["order"] == 1 else 1,
        "bot_a": bot_a, "bot_b": bot_b, "blinds": blinds, "starting_stack": stack,
        "command": command_text, "exit_code": exit_code, "duration_s": round(wall_s, 2),
    })
    if start:
        rec["core_hash"] = start.get("core_hash", "")
    if note:
        rec["status"] = f"incomplete:{note}"
        return rec

    problem = ""
    if exit_code not in ("", 0):
        problem = f"error:exit_code={exit_code}"
    if not start or not end:
        rec["status"] = problem or "incomplete:no_match_end"
        return rec

    seats = start.get("seats") or []
    names = [s.get("name") for s in seats]
    if len(names) != 2 or names[0] == names[1] or None in names:
        rec["status"] = problem or "incomplete:expected_two_distinct_seats"
        return rec
    role_of_seat = ["A", "B"] if item["order"] == 1 else ["B", "A"]

    rec["stopped"] = end.get("stopped", "")
    rec["hands"] = end.get("hands", "")
    winner, places, stacks, seen = "", [], [], set()
    for result in end.get("results") or []:
        if result.get("bot") not in names:
            continue
        seen.add(result["bot"])
        role = role_of_seat[names.index(result["bot"])]
        prefix = role.lower() + "_"
        rec[prefix + "final_stack"] = result.get("final_stack", "")
        stacks.append(result.get("final_stack"))
        places.append(result.get("place"))
        for key in ("decisions", "timeouts", "errors", "restarts", "avg_think_ms", "max_think_ms"):
            value = result.get(key)
            rec[prefix + key] = "" if value is None else value
        rec[prefix + "disabled"] = "" if result.get("disabled") is None else result.get("disabled")
        if result.get("place") == 1:
            winner = role

    inconsistent = ""
    logged_seed = start.get("seed")
    if logged_seed is not None and _as_int(logged_seed) != item["seed"]:
        inconsistent = "seed_mismatch"
    elif seen != set(names) or len(stacks) != 2:
        inconsistent = "results_do_not_match_seats"
    elif any(_as_int(x) is None for x in stacks) or _as_int(end.get("hands")) is None:
        inconsistent = "non_numeric_fields"
    elif sum(_as_int(x) for x in stacks) != 2 * _as_int(stack):
        inconsistent = "chips_not_conserved"      # freezeout: the two stacks must add to 2 x start
    elif rec["stopped"] == "one_player_left" and sorted(places) != [1, 2]:
        inconsistent = "places_not_1_and_2"
    elif rec["stopped"] == "one_player_left" and min(_as_int(x) for x in stacks) != 0:
        inconsistent = "loser_has_chips"

    if problem:
        rec["status"] = problem
    elif inconsistent:
        rec["status"] = f"incomplete:inconsistent_log:{inconsistent}"
    elif rec["stopped"] != "one_player_left":
        rec["status"] = f"incomplete:stopped={rec['stopped']}"
    elif winner not in ("A", "B"):
        rec["status"] = "incomplete:no_winner"
    else:
        rec["status"] = "ok"
        rec["winner"] = winner
    return rec


def run_match(item, settings):
    """Launch one official play.py match and return its CSV record."""
    with tempfile.TemporaryDirectory(prefix="paired_eval_") as tmp:
        log_path = Path(tmp) / "match.jsonl"
        cmd = build_command(settings["python"], settings["play_py"], item["first"], item["second"],
                            item["seed"], settings["blinds"], settings["stack"], log_path,
                            settings["hands_cap"], settings["docker"])
        shown = [LOG_PLACEHOLDER if part == str(log_path) else part for part in cmd]
        # Show the play.py invocation relative to the repo, without the interpreter path.
        command_text = shlex.join(["python3", "play.py"] + shown[2:])
        t0 = time.time()
        note, exit_code = "", ""
        try:
            proc = subprocess.run(cmd, cwd=settings["repo_root"], capture_output=True,
                                  text=True, timeout=settings["match_timeout"])
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            note = "timeout"
        except OSError as exc:
            note = f"launch_failed:{type(exc).__name__}"
        wall = time.time() - t0
        lines = []
        if log_path.exists():
            lines = log_path.read_text(errors="replace").splitlines()
            if settings["keep_logs"]:
                dest = settings["out_dir"] / "logs"
                dest.mkdir(parents=True, exist_ok=True)
                (dest / f"seed{item['seed']}_order{item['order']}.jsonl").write_text("\n".join(lines) + "\n")
        start, end = read_log(lines)
    return make_record(item, command_text, settings["blinds"], settings["stack"],
                       settings["bot_a"], settings["bot_b"], start, end, exit_code, wall, note)


# --------------------------------------------------------------------------- #
# Scoring and statistics
# --------------------------------------------------------------------------- #

def score_pair(winner_order1, winner_order2):
    """Outcome for A. A won both = W, one each = D, B won both = L.
    Either match unfinished = 'incomplete' (never guessed)."""
    if winner_order1 not in ("A", "B") or winner_order2 not in ("A", "B"):
        return "incomplete"
    a_wins = (winner_order1 == "A") + (winner_order2 == "A")
    return {2: "W", 1: "D", 0: "L"}[a_wins]


def _typed_key(rec):
    """(seed, order) with strict typing. Accepts ints or digit strings (raw csv rows), never guesses."""
    try:
        seed = int(rec["seed"])
        seat = int(rec["a_seat"])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"record has unusable seed/a_seat: {rec.get('seed')!r}/{rec.get('a_seat')!r}") from None
    if seat not in (0, 1):
        raise ValueError(f"a_seat must be 0 or 1, got {seat} (seed {seed})")
    return seed, (1 if seat == 0 else 2)


def build_pairs(records):
    """Group records by seed -> {seed: outcome}. A seed missing a match is incomplete.

    Seats are converted to integers first (a raw csv string '0' would otherwise
    never equal 0 and silently scramble pairs). Two rows for the same seed and
    seat raise instead of one overwriting the other. Only status 'ok' rows count."""
    by_seed = {}
    for rec in records:
        seed, order = _typed_key(rec)
        slot = by_seed.setdefault(seed, {})
        if order in slot:
            raise ValueError(f"duplicate record for seed {seed}, a_seat {0 if order == 1 else 1}")
        slot[order] = rec
    pairs = {}
    for seed in sorted(by_seed):
        pair = by_seed[seed]
        winners = [(pair[o].get("winner", "") if o in pair and pair[o].get("status") == "ok" else "")
                   for o in (1, 2)]
        pairs[seed] = score_pair(*winners)
    return pairs


def wilson_interval(k, n, z=1.96):
    """Wilson score interval for a proportion of INDEPENDENT trials. n == 0 gives (0, 1).

    Not used for match win rates: the two matches of a seed are correlated, so those
    use cluster_bootstrap_rate. Kept as a utility for independent counts."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def bootstrap_mean_ci(values, reps=2000, seed=12345, alpha=0.05):
    """Percentile bootstrap CI for a mean, with a fixed RNG so it is reproducible."""
    if not values:
        return None
    rng = random.Random(seed)
    n = len(values)
    means = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(reps))
    lo = means[int((alpha / 2) * reps)]
    hi = means[min(reps - 1, int((1 - alpha / 2) * reps) - 1)]
    return (lo, hi)


def cluster_bootstrap_rate(clusters, reps=2000, seed=12345, alpha=0.05):
    """Percentile bootstrap CI for a pooled win rate, resampling whole seeds.

    clusters: one (wins, matches) tuple per seed. The two matches of a seed share
    the same cards, so the seed, not the match, is the independent unit."""
    clusters = [c for c in clusters if c[1] > 0]
    if not clusters:
        return None
    rng = random.Random(seed)
    n = len(clusters)
    rates = []
    for _ in range(reps):
        wins = games = 0
        for _ in range(n):
            w, g = clusters[rng.randrange(n)]
            wins += w
            games += g
        rates.append(wins / games)
    rates.sort()
    return (rates[int((alpha / 2) * reps)], rates[min(reps - 1, int((1 - alpha / 2) * reps) - 1)])


def _rate(clusters):
    wins = sum(c[0] for c in clusters)
    n = sum(c[1] for c in clusters)
    ci = cluster_bootstrap_rate(clusters)
    return {"wins": wins, "n": n, "seeds": sum(1 for c in clusters if c[1] > 0),
            "rate": (wins / n) if n else None, "ci95": list(ci) if ci else None,
            "ci_method": "cluster bootstrap over seeds"}


def _clusters(records, want_seat=None):
    """(A wins, complete matches) per seed, optionally for one seat only."""
    per_seed = {}
    for r in records:
        if r["status"] != "ok":
            continue
        if want_seat is not None and int(r["a_seat"]) != want_seat:
            continue
        w, g = per_seed.get(int(r["seed"]), (0, 0))
        per_seed[int(r["seed"])] = (w + (r["winner"] == "A"), g + 1)
    return [per_seed[k] for k in sorted(per_seed)]


def summarize(records):
    """All headline numbers. Only complete matches ('ok') count toward win rates."""
    complete = [r for r in records if r["status"] == "ok"]
    pairs = build_pairs(records)
    wdl = {"W": 0, "D": 0, "L": 0}
    for outcome in pairs.values():
        if outcome in wdl:
            wdl[outcome] += 1
    scored = [{"W": 1.0, "D": 0.5, "L": 0.0}[o] for o in pairs.values() if o in wdl]
    ci = bootstrap_mean_ci(scored)
    ci_note = ""
    if scored and len(scored) < MIN_PAIRS_FOR_CI:
        ci_note = f"fewer than {MIN_PAIRS_FOR_CI} complete pairs: interval is unreliable"
    elif ci and ci[0] == ci[1]:
        ci_note = "all pairs identical: interval is degenerate, not proof of certainty"
    problems = {"timeouts": 0, "errors": 0, "restarts": 0}
    for rec in records:
        for key in problems:
            for side in ("a_", "b_"):
                value = rec.get(side + key)
                problems[key] += int(value) if value not in ("", None) else 0
    return {
        "pairs_total": len(pairs),
        "pairs_complete": sum(o in wdl for o in pairs.values()),
        "pairs_incomplete": sum(o == "incomplete" for o in pairs.values()),
        "pair_wdl_for_A": wdl,
        "pair_score_for_A": (sum(scored) / len(scored)) if scored else None,
        "pair_score_ci95": list(ci) if ci else None,
        "pair_score_ci_note": ci_note,
        "matches_total": len(records),
        "matches_complete": len(complete),
        "matches_incomplete": len(records) - len(complete),
        "matches_error": sum(r["status"].startswith("error") for r in records),
        "match_wins_A": _rate(_clusters(records)),
        "A_in_first_seat": _rate(_clusters(records, 0)),
        "A_in_second_seat": _rate(_clusters(records, 1)),
        "problem_counts_both_bots": problems,
        "incomplete_reasons": sorted({r["status"] for r in records if r["status"] != "ok"}),
    }


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #

def _cell(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.2f}"
    return "" if value is None else str(value)


def sorted_records(records):
    return sorted(records, key=lambda r: (int(r["seed"]), int(r["a_seat"])))


def csv_text(records, columns=CSV_COLUMNS):
    """Byte-stable CSV: fixed columns, rows sorted by (seed, seat), LF endings."""
    import io
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(columns)
    for rec in sorted_records(records):
        writer.writerow([_cell(rec.get(col, "")) for col in columns])
    return buf.getvalue()


def deterministic_digest(records):
    """SHA-256 over the columns that depend only on cards and bot decisions.
    Re-running the same bots and seeds should reproduce it exactly."""
    columns = [c for c in CSV_COLUMNS if c not in RUNTIME_COLUMNS]
    return hashlib.sha256(csv_text(records, columns).encode()).hexdigest()


def _convert_cell(column, text, line_no):
    if text == "":
        return ""
    try:
        if column in INT_COLUMNS:
            return int(text)
        if column in FLOAT_COLUMNS:
            return float(text)
    except ValueError:
        raise ValueError(f"line {line_no}: column {column!r} expects a number, got {text!r}") from None
    if column in BOOL_COLUMNS:
        if text not in ("true", "false"):
            raise ValueError(f"line {line_no}: column {column!r} expects true/false, got {text!r}")
        return text == "true"
    return text


def load_records_csv(text):
    """Parse an archived matches.csv back into typed records, validating as it goes.

    seed and a_seat become ints (raw csv strings would scramble the pairing),
    numeric and boolean columns are converted, and obviously corrupt rows raise
    ValueError with a line number instead of producing a quietly wrong score."""
    import io
    reader = csv.DictReader(io.StringIO(text))
    missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
    if missing:
        raise ValueError(f"matches.csv is missing columns: {sorted(missing)}")
    records, seen, bots = [], set(), set()
    for line_no, row in enumerate(reader, start=2):
        rec = _blank_record()
        for column in CSV_COLUMNS:
            if column in row and row[column] is not None:
                rec[column] = _convert_cell(column, row[column], line_no)
        if not isinstance(rec["seed"], int) or rec["a_seat"] not in (0, 1):
            raise ValueError(f"line {line_no}: seed must be an integer and a_seat 0 or 1")
        status = rec["status"]
        if not (status == "ok" or status.startswith("incomplete") or status.startswith("error")):
            raise ValueError(f"line {line_no}: unknown status {status!r}")
        if status == "ok" and rec["winner"] not in ("A", "B"):
            raise ValueError(f"line {line_no}: status ok needs winner A or B")
        if status != "ok" and rec["winner"] != "":
            raise ValueError(f"line {line_no}: a non-ok match must not carry a winner")
        key = (rec["seed"], rec["a_seat"])
        if key in seen:
            raise ValueError(f"line {line_no}: duplicate row for seed {key[0]}, a_seat {key[1]}")
        seen.add(key)
        bots.add((rec["bot_a"], rec["bot_b"]))
        records.append(rec)
    if not records:
        raise ValueError("matches.csv has no rows")
    if len(bots) != 1:
        raise ValueError(f"rows mix different bot pairs: {sorted(bots)}")
    return records


def pairs_text(records):
    import io
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["seed", "outcome_for_A"])
    for seed, outcome in build_pairs(records).items():
        writer.writerow([seed, outcome])
    return buf.getvalue()


def _pct(x):
    return "n/a" if x is None else f"{100 * x:.1f}%"


def _rate_line(label, block):
    if not block["ci95"]:
        return f"  {label:<22} {block['wins']}/{block['n']}  n/a"
    lo, hi = block["ci95"]
    return (f"  {label:<22} {block['wins']}/{block['n']}  {_pct(block['rate'])}"
            f"  (95% cluster bootstrap over seeds {100 * lo:.1f}%-{100 * hi:.1f}%)")


def format_report(summary, bot_a, bot_b):
    wdl = summary["pair_wdl_for_A"]
    lines = [f"Paired-seat results: A = {bot_a}   B = {bot_b}", ""]
    lines.append(f"Duplicate pairs ({summary['pairs_complete']} complete, "
                 f"{summary['pairs_incomplete']} incomplete, {summary['pairs_total']} total)")
    lines.append(f"  A: {wdl['W']} won, {wdl['D']} drawn, {wdl['L']} lost")
    if summary["pair_score_for_A"] is not None and summary["pair_score_ci95"]:
        lo, hi = summary["pair_score_ci95"]
        lines.append(f"  pair score {summary['pair_score_for_A']:.3f} "
                     f"(bootstrap over pairs, 95% {lo:.3f}-{hi:.3f}; 0.5 = even; "
                     "team convention W+0.5D, not the organiser's ranking rule)")
        if summary["pair_score_ci_note"]:
            lines.append(f"  WARNING: {summary['pair_score_ci_note']}")
    lines += ["", f"Single matches ({summary['matches_complete']} complete of {summary['matches_total']})",
              _rate_line("A wins, overall", summary["match_wins_A"]),
              _rate_line("A wins, seat 0", summary["A_in_first_seat"]),
              _rate_line("A wins, seat 1", summary["A_in_second_seat"])]
    if summary["matches_error"]:
        lines.append(f"  {summary['matches_error']} match(es) had a nonzero runner exit code: "
                     "excluded from win rates and their pairs are incomplete")
    problems = summary["problem_counts_both_bots"]
    lines += ["", f"Runner-reported problems (both bots): {problems['timeouts']} timeouts, "
                  f"{problems['errors']} errors, {problems['restarts']} restarts"]
    if summary["incomplete_reasons"]:
        lines.append("Incomplete matches: " + ", ".join(summary["incomplete_reasons"]))
    lines += ["", "Intervals resample whole seeds; small samples give wide or unreliable intervals. "
                  "See benchmarks/README.md."]
    return "\n".join(lines) + "\n"


def _git(repo_root, *args):
    try:
        out = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True, timeout=20)
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _bot_file_hash(path, repo_root):
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = Path(repo_root) / candidate
    target = candidate / "bot.py" if candidate.is_dir() else candidate
    if target.suffix == ".py" and target.exists():
        return hashlib.sha256(target.read_bytes()).hexdigest()
    return None


def build_manifest(args, settings, records, summary):
    repo_root = settings["repo_root"]
    status = _git(repo_root, "status", "--short")
    core_hashes = sorted({r["core_hash"] for r in records if r["core_hash"]})
    return {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "invocation": [sys.argv[0]] + list(sys.argv[1:]),
        "python": sys.version.split()[0], "platform": platform.platform(),
        "git_head": _git(repo_root, "rev-parse", "HEAD"),
        "git_branch": _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD"),
        "git_status_short": status.splitlines()[:50] if status else [],
        "core_hashes_seen": core_hashes,
        "bot_a": {"path": args.bot_a, "bot_py_sha256": _bot_file_hash(args.bot_a, repo_root)},
        "bot_b": {"path": args.bot_b, "bot_py_sha256": _bot_file_hash(args.bot_b, repo_root)},
        "blinds": settings["blinds"], "starting_stack": settings["stack"],
        "docker": settings["docker"], "seeds": sorted({r["seed"] for r in records}),
        "deterministic_digest_sha256": deterministic_digest(records),
        "unavailable_fields": UNAVAILABLE_FIELDS, "assumptions": ASSUMPTIONS,
        "summary": summary,
    }


# --------------------------------------------------------------------------- #
# Command line
# --------------------------------------------------------------------------- #

def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("bot_a", nargs="?", help="first bot (folder, bot.py or .zip); results are reported from A's view")
    p.add_argument("bot_b", nargs="?", help="second bot")
    p.add_argument("--seeds", default=None, help="e.g. 41-43 or 41,42,50-55 (required unless --rescore)")
    p.add_argument("--rescore", metavar="MATCHES_CSV", default=None,
                   help="re-score an archived matches.csv without playing anything")
    p.add_argument("--blinds", default="standard", help="standard (default), turbo, slow, or flat like 50/100")
    p.add_argument("--stack", type=int, default=10_000, help="starting stack (default 10000)")
    p.add_argument("--hands-cap", type=int, default=None, help="safety cap on hands per match (play.py default 2000)")
    p.add_argument("--out-dir", default=None, help="default: benchmarks/results/<A>_vs_<B>")
    p.add_argument("--jobs", type=int, default=1, help="parallel matches (default 1; more jobs distort timing)")
    p.add_argument("--match-timeout", type=float, default=900, help="seconds before a match counts as incomplete")
    p.add_argument("--keep-logs", action="store_true", help="keep each match's full JSON-lines event log")
    p.add_argument("--docker", action="store_true", help="pass --docker to play.py (needs 'make sandbox' first)")
    p.add_argument("--allow-sealed", action="store_true",
                   help="allow sealed seeds 1001-1200; only for the human-approved final run")
    p.add_argument("--dry-run", action="store_true", help="print the planned commands and exit")
    p.add_argument("--python", default=sys.executable, help="interpreter used to launch play.py")
    p.add_argument("--play-py", default=None, help="path to play.py (default: <repo>/play.py)")
    return p.parse_args(argv)


def rescore(args):
    """Load an archived matches.csv, validate it and print the same report. Plays nothing."""
    try:
        records = sorted_records(load_records_csv(Path(args.rescore).read_text()))
        summary = summarize(records)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    report = format_report(summary, records[0]["bot_a"], records[0]["bot_b"])
    print(report)
    print(f"Deterministic digest: {deterministic_digest(records)}")
    if args.out_dir:
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "pairs.csv").write_text(pairs_text(records))
        (out_dir / "summary.txt").write_text(report)
        print(f"Wrote pairs.csv and summary.txt to {out_dir}")
    return 0 if summary["matches_incomplete"] == 0 else 2


def main(argv=None):
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    if args.rescore:
        return rescore(args)
    if not (args.bot_a and args.bot_b and args.seeds):
        print("error: give bot_a, bot_b and --seeds (or use --rescore MATCHES_CSV)", file=sys.stderr)
        return 2
    try:
        seeds = parse_seeds(args.seeds, args.allow_sealed)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    play_py = Path(args.play_py) if args.play_py else repo_root / "play.py"
    if not play_py.exists():
        print(f"error: play.py not found at {play_py}", file=sys.stderr)
        return 2

    label = f"{Path(args.bot_a).resolve().name}_vs_{Path(args.bot_b).resolve().name}"
    out_dir = Path(args.out_dir) if args.out_dir else repo_root / "benchmarks" / "results" / label
    settings = {
        "python": args.python, "play_py": play_py, "repo_root": repo_root, "blinds": args.blinds,
        "stack": args.stack, "hands_cap": args.hands_cap, "docker": args.docker,
        "match_timeout": args.match_timeout, "keep_logs": args.keep_logs, "out_dir": out_dir,
        "bot_a": args.bot_a, "bot_b": args.bot_b,
    }
    plan = plan_matches(seeds, args.bot_a, args.bot_b)

    if args.dry_run:
        for item in plan:
            cmd = build_command("python3", "play.py", item["first"], item["second"], item["seed"],
                                args.blinds, args.stack, LOG_PLACEHOLDER, args.hands_cap, args.docker)
            print(shlex.join(cmd))
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        records = list(pool.map(lambda item: run_match(item, settings), plan))
    records = sorted_records(records)

    summary = summarize(records)
    (out_dir / "matches.csv").write_text(csv_text(records))
    (out_dir / "pairs.csv").write_text(pairs_text(records))
    manifest = build_manifest(args, settings, records, summary)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    report = format_report(summary, args.bot_a, args.bot_b)
    (out_dir / "summary.txt").write_text(report)
    print(report)
    print(f"Wrote matches.csv, pairs.csv, manifest.json, summary.txt to {out_dir}")
    print(f"Deterministic digest: {manifest['deterministic_digest_sha256']}")
    return 0 if summary["matches_incomplete"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
