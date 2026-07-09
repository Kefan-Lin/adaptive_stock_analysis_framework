import datetime
import json
import pathlib
import subprocess
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import morning_check as mc  # noqa: E402
import validate_records as vr  # noqa: E402

FIXTURE_HOME = REPO_ROOT / "tests" / "fixtures" / "morning-check-home"
SCRIPT = REPO_ROOT / "scripts" / "morning_check.py"
QUOTES = REPO_ROOT / "tests" / "fixtures" / "morning-check-quotes.yaml"
AS_OF = datetime.date(2026, 7, 9)


def _evaluate(prices=None, as_of=AS_OF):
    src = mc.FilePriceSource(prices if prices is not None else {
        "ACME": 189.20, "1234.HK": 480.0, "NVDA": 138.10,
    })
    return mc.evaluate_state(FIXTURE_HOME, src, as_of)


def _findings(result, symbol=None, kind=None):
    out = result["findings"]
    if symbol is not None:
        out = [f for f in out if f["symbol"] == symbol]
    if kind is not None:
        out = [f for f in out if f["kind"] == kind]
    return out


# --------------------------- Task 2: price sources ---------------------------

class ProviderMappingTests(unittest.TestCase):
    def test_us_symbol_passes_through_to_yfinance(self):
        self.assertEqual(mc.provider_for("NVDA"), ("yfinance", "NVDA"))

    def test_hk_symbol_passes_through_to_yfinance(self):
        self.assertEqual(mc.provider_for("0700.HK"), ("yfinance", "0700.HK"))

    def test_cn_symbol_routes_to_akshare_bare_code(self):
        self.assertEqual(mc.provider_for("600519.SH"), ("akshare", "600519"))
        self.assertEqual(mc.provider_for("300750.SZ"), ("akshare", "300750"))

    def test_kr_and_au_pass_through_to_yfinance(self):
        self.assertEqual(mc.provider_for("000660.KS"), ("yfinance", "000660.KS"))
        self.assertEqual(mc.provider_for("BC8.AX"), ("yfinance", "BC8.AX"))

    def test_symbol_patterns_are_the_validate_records_object(self):
        # Identity, not a copy: guarantees the two vocabularies cannot drift.
        self.assertIs(mc.SYMBOL_PATTERNS, vr.SYMBOL_PATTERNS)


class FilePriceSourceTests(unittest.TestCase):
    def test_returns_price_when_present_and_none_when_absent(self):
        src = mc.FilePriceSource({"ACME": 189.20})
        self.assertEqual(src.spot("ACME"), 189.20)
        self.assertIsNone(src.spot("MISSING"))

    def test_chain_falls_through_to_second_source(self):
        chain = mc.ChainSource(mc.FilePriceSource({"ACME": 1.0}),
                               mc.FilePriceSource({"NVDA": 2.0}))
        self.assertEqual(chain.spot("ACME"), 1.0)
        self.assertEqual(chain.spot("NVDA"), 2.0)
        self.assertIsNone(chain.spot("MISSING"))


# --------------------------- Task 3: state loading ---------------------------

class StateLoadingTests(unittest.TestCase):
    def test_loads_portfolio(self):
        portfolio = mc.load_portfolio(FIXTURE_HOME)
        self.assertEqual(portfolio["schema"], "portfolio/v1")
        self.assertEqual(len(portfolio["holdings"]), 2)

    def test_missing_portfolio_returns_empty_dict(self):
        portfolio = mc.load_portfolio(REPO_ROOT / "tests" / "fixtures")
        self.assertEqual(portfolio, {})

    def test_latest_record_per_symbol(self):
        latest = mc.load_latest_records(FIXTURE_HOME)
        self.assertEqual(set(latest), {"ACME", "1234.HK", "NVDA"})
        self.assertEqual(latest["ACME"]["mode"], "new-idea")

    def test_universe_is_union_of_holdings_options_and_records(self):
        portfolio = mc.load_portfolio(FIXTURE_HOME)
        latest = mc.load_latest_records(FIXTURE_HOME)
        universe = mc.build_universe(portfolio, latest)
        self.assertEqual(universe, {"ACME", "1234.HK", "NVDA"})


# --------------------------- Task 4: equity checks ---------------------------

class EquityCheckTests(unittest.TestCase):
    def test_trim_exit_price_trigger_fires_act(self):
        result = _evaluate()
        hits = _findings(result, "ACME", "price_trigger")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["urgency"], "act")
        self.assertEqual(hits[0]["evidence"]["level"], 185)

    def test_add_on_price_trigger_does_not_fire_above_level(self):
        # ACME add_on is 'below 90'; spot 189.20 must not trip it.
        result = _evaluate()
        levels = [f["evidence"]["level"] for f in _findings(result, "ACME", "price_trigger")]
        self.assertNotIn(90, levels)

    def test_add_on_price_trigger_fires_when_spot_below(self):
        result = _evaluate(prices={"ACME": 85.0, "1234.HK": 480.0, "NVDA": 138.10})
        levels = [f["evidence"]["level"] for f in _findings(result, "ACME", "price_trigger")]
        self.assertIn(90, levels)

    def test_review_by_passed_is_review(self):
        result = _evaluate()
        hits = _findings(result, "ACME", "review_expiry")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["urgency"], "review")

    def test_review_by_far_out_produces_no_finding(self):
        result = _evaluate()
        self.assertEqual(_findings(result, "1234.HK", "review_expiry"), [])

    def test_next_earnings_soon_is_watch(self):
        result = _evaluate()
        hits = _findings(result, "ACME", "earnings_proximity")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["urgency"], "watch")

    def test_null_next_earnings_is_a_data_gap(self):
        result = _evaluate()
        reasons = [g for g in result["data_gaps"] if g["symbol"] == "1234.HK"]
        self.assertTrue(any("earnings date unknown" in g["reason"] for g in reasons))

    def test_missing_price_becomes_data_gap(self):
        result = _evaluate(prices={"1234.HK": 480.0, "NVDA": 138.10})  # ACME absent
        self.assertTrue(any(g["symbol"] == "ACME" for g in result["data_gaps"]))


# --------------------------- Task 5: option assignment ---------------------------

class OptionAssignmentTests(unittest.TestCase):
    def test_itm_near_expiry_put_with_earnings_before_expiry_is_act(self):
        result = _evaluate()
        hits = _findings(result, "NVDA", "options_assignment")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["urgency"], "act")
        ev = hits[0]["evidence"]
        self.assertEqual(ev["strike"], 140)
        self.assertEqual(ev["reserve"], 14000.0)  # 140 * 100 * 1
        self.assertTrue(ev["in_the_money"])
        self.assertTrue(ev["earnings_before_expiry"])

    def test_far_otm_put_produces_no_finding(self):
        # Direct call with a synthetic leg: far OTM, far from expiry, and
        # earnings after expiry so none of the four risk conditions trip.
        portfolio = {"option_legs": [
            {"kind": "cash-secured-put", "underlying": "NVDA", "strike": 140,
             "expiry": "2026-09-18", "qty": -1, "multiplier": 100}]}
        latest = {"NVDA": {"next_earnings": "2026-09-30"}}  # after expiry
        src = mc.FilePriceSource({"NVDA": 300.0})
        gaps = []
        out = mc._option_findings(portfolio, latest, src, datetime.date(2026, 7, 9),
                                  0.03, 7, gaps)
        self.assertEqual(out, [])

    def test_missing_underlying_price_is_data_gap(self):
        result = _evaluate(prices={"ACME": 189.20, "1234.HK": 480.0})  # NVDA absent
        # NVDA already gaps on its equity price; the option check must not crash.
        self.assertTrue(any(g["symbol"] == "NVDA" for g in result["data_gaps"]))
        self.assertEqual(_findings(result, "NVDA", "options_assignment"), [])


# --------------------------- Task 6: CLI ---------------------------

class CliTests(unittest.TestCase):
    def _run(self, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--home", str(FIXTURE_HOME),
             "--as-of", "2026-07-09", "--offline", "--prices", str(QUOTES), *extra],
            capture_output=True, text=True,
        )

    def test_json_output_has_expected_findings(self):
        result = self._run("--format", "json")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["as_of"], "2026-07-09")
        kinds = {(f["symbol"], f["kind"]) for f in payload["findings"]}
        self.assertIn(("ACME", "price_trigger"), kinds)
        self.assertIn(("ACME", "review_expiry"), kinds)
        self.assertIn(("ACME", "earnings_proximity"), kinds)
        self.assertIn(("NVDA", "options_assignment"), kinds)
        self.assertTrue(any(g["symbol"] == "1234.HK" for g in payload["data_gaps"]))

    def test_markdown_output_groups_by_urgency(self):
        result = self._run("--format", "md")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("# Morning Check — 2026-07-09", result.stdout)
        self.assertIn("## Act now", result.stdout)
        self.assertIn("## Data gaps", result.stdout)

    def test_missing_state_home_is_environment_error(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--home",
             str(REPO_ROOT / "tests" / "fixtures" / "does-not-exist"), "--offline"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)


# --------------------------- Task 7: skill wiring ---------------------------

class SkillWiringTests(unittest.TestCase):
    def test_skill_and_openai_metadata_exist(self):
        self.assertTrue((REPO_ROOT / "skills" / "morning-check" / "SKILL.md").exists())
        self.assertTrue((REPO_ROOT / "skills" / "morning-check" / "agents" / "openai.yaml").exists())

    def test_skill_is_registered_in_validate_repo(self):
        text = (REPO_ROOT / "scripts" / "validate_repo.py").read_text(encoding="utf-8")
        self.assertIn("skills/morning-check/SKILL.md", text)
        self.assertIn("skills/morning-check/agents/openai.yaml", text)

    def test_skill_references_the_script_and_state_contract(self):
        skill = (REPO_ROOT / "skills" / "morning-check" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("scripts/morning_check.py", skill)
        self.assertIn("decision-records.md", skill)


# --------------------------- Task 8: live smoke (network-gated) ---------------------------

class LiveSourceSmokeTests(unittest.TestCase):
    def test_live_source_returns_a_price_for_a_liquid_name(self):
        try:
            import yfinance  # noqa: F401
        except Exception:
            self.skipTest("yfinance not installed (pyyaml-only job)")
        price = mc.LivePriceSource().spot("AAPL")
        # Network may be unavailable; accept None but never an exception.
        self.assertTrue(price is None or (isinstance(price, float) and price > 0))


if __name__ == "__main__":
    unittest.main()
