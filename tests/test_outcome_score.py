import datetime
import json
import pathlib
import subprocess
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import outcome_score as os_  # noqa: E402
import validate_records as vr  # noqa: E402

FIXTURE_HOME = REPO_ROOT / "tests" / "fixtures" / "scoring-home"
SCRIPT = REPO_ROOT / "scripts" / "outcome_score.py"
CLOSES = REPO_ROOT / "tests" / "fixtures" / "scoring-closes.yaml"

D = datetime.date


def _closes():
    return {
        "GAINR": {"2026-01-05": 100.0, "2026-04-05": 118.0,
                  "2026-07-04": 135.0, "2027-01-05": 160.0},
        "FADE": {"2026-01-10": 200.0, "2026-04-10": 180.0,
                 "2026-07-09": 165.0, "2027-01-10": 150.0},
        "HOLDR": {"2026-02-01": 50.0, "2026-05-02": 52.0,
                  "2026-07-31": 48.0, "2027-02-01": 58.0},
    }


# --------------------------- Task 1: price history ---------------------------

class PriceHistoryTests(unittest.TestCase):
    def _hist(self):
        return os_.FileHistory({"ACME": {
            "2026-01-05": 100.0, "2026-04-03": 118.0, "2026-07-03": 135.0,
        }})

    def test_close_on_exact_date(self):
        self.assertEqual(self._hist().close_on("ACME", D(2026, 1, 5)), 100.0)

    def test_close_on_nearest_prior_trading_day_within_lookback(self):
        # 2026-04-05 is a weekend; the 04-03 close is 2 days prior.
        self.assertEqual(self._hist().close_on("ACME", D(2026, 4, 5)), 118.0)

    def test_close_on_returns_none_beyond_lookback(self):
        self.assertIsNone(self._hist().close_on("ACME", D(2026, 6, 1)))

    def test_close_on_unknown_symbol_is_none(self):
        self.assertIsNone(self._hist().close_on("MISSING", D(2026, 1, 5)))

    def test_low_high_over_window(self):
        lo, hi = self._hist().low_high("ACME", D(2026, 1, 1), D(2026, 7, 4))
        self.assertEqual((lo, hi), (100.0, 135.0))

    def test_low_high_empty_window_is_none_pair(self):
        self.assertEqual(self._hist().low_high("ACME", D(2025, 1, 1), D(2025, 2, 1)),
                         (None, None))

    def test_symbol_patterns_are_the_validate_records_object(self):
        self.assertIs(os_.SYMBOL_PATTERNS, vr.SYMBOL_PATTERNS)


# --------------------------- Task 2: record loading ---------------------------

class LoadRecordsTests(unittest.TestCase):
    def test_loads_scorable_records_and_skips_malformed_and_index(self):
        metas = os_.load_all_records(FIXTURE_HOME)
        symbols = sorted(m["symbol"] for m in metas)
        self.assertEqual(symbols, ["FADE", "GAINR", "HOLDR"])  # NOPRICE skipped

    def test_missing_records_dir_returns_empty(self):
        empty = os_.load_all_records(REPO_ROOT / "tests" / "fixtures")
        self.assertEqual(empty, [])


# --------------------------- Task 3: direction hit ---------------------------

class DirectionHitTests(unittest.TestCase):
    def test_buy_hit_when_up(self):
        self.assertTrue(os_._direction_hit("Buy", 0.10, 110.0, None))

    def test_buy_miss_when_down(self):
        self.assertFalse(os_._direction_hit("Add", -0.05, 95.0, None))

    def test_reduce_hit_when_down(self):
        self.assertTrue(os_._direction_hit("Reduce", -0.08, 92.0, None))

    def test_avoid_miss_when_up(self):
        self.assertFalse(os_._direction_hit("Avoid", 0.03, 103.0, None))

    def test_hold_hit_inside_scenario_band(self):
        scenarios = {"bear": 40, "base": 50, "bull": 65}
        self.assertTrue(os_._direction_hit("Hold", 0.04, 52.0, scenarios))

    def test_hold_miss_outside_scenario_band(self):
        scenarios = {"bear": 40, "base": 50, "bull": 65}
        self.assertFalse(os_._direction_hit("Hold", 0.60, 80.0, scenarios))

    def test_hold_no_scenarios_uses_return_band(self):
        self.assertTrue(os_._direction_hit("Hold", 0.05, 105.0, None))
        self.assertFalse(os_._direction_hit("Hold", 0.20, 120.0, None))

    def test_no_stance_is_none(self):
        self.assertIsNone(os_._direction_hit(None, 0.10, 110.0, None))


# --------------------------- Task 4: WFV + scenario ---------------------------

class WfvAndScenarioTests(unittest.TestCase):
    def test_wfv_converges_toward_fair_value(self):
        # P0 100, WFV 140 (undervalued); exit 118 moved toward WFV.
        gap_closed, converged = os_._wfv(100.0, 118.0, 140)
        self.assertAlmostEqual(gap_closed, 0.45, places=2)  # (40-22)/40
        self.assertTrue(converged)

    def test_wfv_moves_away_is_not_converged(self):
        gap_closed, converged = os_._wfv(100.0, 90.0, 140)
        self.assertLess(gap_closed, 0)
        self.assertFalse(converged)

    def test_wfv_overshoot_wrong_direction_not_converged(self):
        # Overvalued call (WFV 80 < P0 100) but price rose: wrong direction.
        gap_closed, converged = os_._wfv(100.0, 110.0, 80)
        self.assertFalse(converged)

    def test_wfv_none_when_absent(self):
        self.assertIsNone(os_._wfv(100.0, 118.0, None))

    def test_wfv_none_when_price_equals_fair_value(self):
        self.assertIsNone(os_._wfv(140.0, 150.0, 140))

    def test_scenario_landing_bands(self):
        s = {"bear": 80, "base": 130, "bull": 190}
        self.assertEqual(os_._scenario_landing(70, s), "below_bear")
        self.assertEqual(os_._scenario_landing(100, s), "bear_base")
        self.assertEqual(os_._scenario_landing(160, s), "base_bull")
        self.assertEqual(os_._scenario_landing(200, s), "above_bull")

    def test_scenario_landing_none_when_incomplete(self):
        self.assertIsNone(os_._scenario_landing(100, {"bear": 80}))


# --------------------------- Task 5: trigger touch ---------------------------

class TriggerTouchTests(unittest.TestCase):
    def test_trim_exit_above_touched_by_window_high(self):
        triggers = {"trim_exit": [{"type": "price", "level": 130, "direction": "above"}]}
        touches = os_._trigger_touches(triggers, low=100.0, high=135.0)
        self.assertEqual(touches, [{"group": "trim_exit", "level": 130,
                                    "direction": "above", "touched": True}])

    def test_add_on_below_not_touched(self):
        triggers = {"add_on": [{"type": "price", "level": 85, "direction": "below"}]}
        touches = os_._trigger_touches(triggers, low=100.0, high=135.0)
        self.assertEqual(touches[0]["touched"], False)

    def test_non_price_trigger_ignored(self):
        triggers = {"add_on": [{"type": "kpi", "text": "x"}]}
        self.assertEqual(os_._trigger_touches(triggers, 100.0, 135.0), [])

    def test_touched_is_none_when_range_unavailable(self):
        triggers = {"trim_exit": [{"type": "price", "level": 130, "direction": "above"}]}
        self.assertIsNone(os_._trigger_touches(triggers, None, None)[0]["touched"])


# --------------------------- Task 6: evaluate_home ---------------------------

class EvaluateHomeTests(unittest.TestCase):
    def test_all_windows_pending_before_maturity(self):
        result = os_.evaluate_home(FIXTURE_HOME, os_.FileHistory(_closes()),
                                   as_of=D(2026, 3, 1))
        self.assertEqual(result["scored"], [])
        pending_syms = {p["symbol"] for p in result["pending"]}
        self.assertEqual(pending_syms, {"GAINR", "FADE", "HOLDR"})

    def test_matured_windows_scored(self):
        result = os_.evaluate_home(FIXTURE_HOME, os_.FileHistory(_closes()),
                                   as_of=D(2027, 7, 1))
        by_symbol = {r["symbol"]: r for r in result["scored"]}
        self.assertEqual(set(by_symbol), {"GAINR", "FADE", "HOLDR"})
        gainr90 = by_symbol["GAINR"]["windows"]["90"]
        self.assertAlmostEqual(gainr90["return"], 0.18, places=4)
        self.assertTrue(gainr90["direction_hit"])
        self.assertTrue(gainr90["converged"])
        self.assertEqual(gainr90["scenario_landing"], "bear_base")
        fade90 = by_symbol["FADE"]["windows"]["90"]
        self.assertTrue(fade90["direction_hit"])   # Reduce, price fell
        hold90 = by_symbol["HOLDR"]["windows"]["90"]
        self.assertTrue(hold90["direction_hit"])    # inside band

    def test_missing_close_is_data_gap(self):
        closes = _closes()
        del closes["GAINR"]["2027-01-05"]  # drop the +365d close
        result = os_.evaluate_home(FIXTURE_HOME, os_.FileHistory(closes),
                                   as_of=D(2027, 7, 1))
        gaps = [g for g in result["data_gaps"]
                if g["symbol"] == "GAINR" and g["window"] == 365]
        self.assertEqual(len(gaps), 1)


# --------------------------- Task 7: calibration ---------------------------

class CalibrationTests(unittest.TestCase):
    def _cal(self):
        result = os_.evaluate_home(FIXTURE_HOME, os_.FileHistory(_closes()),
                                   as_of=D(2027, 7, 1))
        return result["calibration"]

    def test_overall_bucket_counts_all_scored_records(self):
        overall90 = self._cal()["overall"]["90"]
        self.assertEqual(overall90["n"], 3)               # GAINR, FADE, HOLDR
        self.assertAlmostEqual(overall90["hit_rate"], 1.0)  # all three hit at 90d

    def test_by_stance_buckets(self):
        by_stance = self._cal()["by_stance"]["90"]
        self.assertIn("Buy", by_stance)
        self.assertIn("Reduce", by_stance)
        self.assertEqual(by_stance["Buy"]["n"], 1)
        self.assertTrue(by_stance["Buy"]["low_n"])        # n < LOW_N

    def test_median_return_computed(self):
        overall90 = self._cal()["overall"]["90"]
        self.assertIn("median_return", overall90)

    def test_wfv_convergence_rate_over_records_with_wfv(self):
        by_stance = self._cal()["by_stance"]["90"]
        self.assertIsNotNone(by_stance["Buy"]["wfv_convergence"])


# --------------------------- Task 8: render + chain + CLI ---------------------------

class RenderTests(unittest.TestCase):
    def test_markdown_has_headline_and_tables(self):
        result = os_.evaluate_home(FIXTURE_HOME, os_.FileHistory(_closes()),
                                   as_of=D(2027, 7, 1))
        md = os_.render_markdown(result)
        self.assertIn("# Outcome Scoring — 2027-07-01", md)
        self.assertIn("## Window 90d", md)
        self.assertIn("By stance", md)


class ChainHistoryTests(unittest.TestCase):
    def test_file_close_wins_then_falls_through(self):
        chain = os_.ChainHistory(os_.FileHistory({"A": {"2026-01-01": 10.0}}),
                                 os_.FileHistory({"B": {"2026-01-01": 20.0}}))
        self.assertEqual(chain.close_on("A", D(2026, 1, 1)), 10.0)
        self.assertEqual(chain.close_on("B", D(2026, 1, 1)), 20.0)
        self.assertIsNone(chain.close_on("C", D(2026, 1, 1)))


class CliTests(unittest.TestCase):
    def _run(self, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--home", str(FIXTURE_HOME),
             "--as-of", "2027-07-01", "--offline", "--prices", str(CLOSES), *extra],
            capture_output=True, text=True,
        )

    def test_json_output(self):
        result = self._run("--format", "json")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["as_of"], "2027-07-01")
        self.assertEqual(payload["calibration"]["overall"]["90"]["n"], 3)

    def test_markdown_output(self):
        result = self._run("--format", "md")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("# Outcome Scoring — 2027-07-01", result.stdout)

    def test_custom_windows(self):
        result = self._run("--format", "json", "--windows", "90")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["windows"], [90])

    def test_missing_state_home_is_environment_error(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--home",
             str(REPO_ROOT / "tests" / "fixtures" / "nope"), "--offline"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)

    def test_bad_as_of_is_environment_error(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--home", str(FIXTURE_HOME),
             "--as-of", "not-a-date", "--offline"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


# --------------------------- Task 9: skill wiring ---------------------------

class SkillWiringTests(unittest.TestCase):
    def test_skill_and_openai_metadata_exist(self):
        self.assertTrue((REPO_ROOT / "skills" / "outcome-scoring" / "SKILL.md").exists())
        self.assertTrue((REPO_ROOT / "skills" / "outcome-scoring" / "agents" / "openai.yaml").exists())

    def test_skill_is_registered_in_validate_repo(self):
        text = (REPO_ROOT / "scripts" / "validate_repo.py").read_text(encoding="utf-8")
        self.assertIn("skills/outcome-scoring/SKILL.md", text)
        self.assertIn("skills/outcome-scoring/agents/openai.yaml", text)

    def test_skill_references_the_script_and_state_contract(self):
        skill = (REPO_ROOT / "skills" / "outcome-scoring" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("scripts/outcome_score.py", skill)
        self.assertIn("decision-records.md", skill)


# --------------------------- Task 10: live smoke (network-gated) ---------------------------

class LiveHistorySmokeTests(unittest.TestCase):
    def test_live_history_returns_a_close_or_none_never_raises(self):
        try:
            import yfinance  # noqa: F401
        except Exception:
            self.skipTest("yfinance not installed (pyyaml-only job)")
        hist = os_.LiveHistory()
        end = datetime.date.today()
        start = end - datetime.timedelta(days=30)
        hist.prefetch("AAPL", start, end)
        close = hist.close_on("AAPL", end)
        # Network may be unavailable; accept None but never an exception.
        self.assertTrue(close is None or (isinstance(close, float) and close > 0))


if __name__ == "__main__":
    unittest.main()
