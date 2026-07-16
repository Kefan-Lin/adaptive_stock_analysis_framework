import copy
import datetime
import json
import pathlib
import subprocess
import sys
import unittest

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import sync_portfolio as sp  # noqa: E402
import validate_records as vr  # noqa: E402

D = datetime.date


class ParseDescriptionTests(unittest.TestCase):
    def test_bare_us_ticker(self):
        self.assertEqual(sp.parse_description("MU"),
                         {"asset": "stock", "ticker": "MU", "exchange": None})

    def test_ticker_with_exchange(self):
        self.assertEqual(sp.parse_description("BC8 @ASX"),
                         {"asset": "stock", "ticker": "BC8", "exchange": "ASX"})
        self.assertEqual(sp.parse_description("000660 @KRX"),
                         {"asset": "stock", "ticker": "000660", "exchange": "KRX"})

    def test_us_ticker_with_class_dot(self):
        self.assertEqual(sp.parse_description("BRK.B"),
                         {"asset": "stock", "ticker": "BRK.B", "exchange": None})

    def test_option_call_apostrophe_year(self):
        self.assertEqual(sp.parse_description("MSFT Jun16'28 450 CALL @AMEX"), {
            "asset": "option", "underlying": "MSFT", "expiry": D(2028, 6, 16),
            "strike": 450.0, "right": "CALL", "exchange": "AMEX"})

    def test_option_put(self):
        self.assertEqual(sp.parse_description("QQQ Aug31'26 700 PUT @AMEX"), {
            "asset": "option", "underlying": "QQQ", "expiry": D(2026, 8, 31),
            "strike": 700.0, "right": "PUT", "exchange": "AMEX"})

    def test_option_fractional_strike(self):
        parsed = sp.parse_description("XYZ Jan15'27 12.5 PUT")
        self.assertEqual(parsed["strike"], 12.5)
        self.assertIsNone(parsed["exchange"])

    def test_unparseable_returns_none(self):
        self.assertIsNone(sp.parse_description("SOMETHING WEIRD 123 XX"))
        self.assertIsNone(sp.parse_description(""))

    def test_non_string_input_returns_none(self):
        self.assertIsNone(sp.parse_description(None))

    def test_unknown_month_token_returns_none(self):
        # The regex month group accepts any capitalized triple; the _MONTHS
        # lookup is what rejects a non-month token.
        self.assertIsNone(sp.parse_description("MU Zzz16'28 450 CALL"))

    def test_impossible_calendar_date_returns_none(self):
        self.assertIsNone(sp.parse_description("MU Feb30'28 450 CALL"))


class CanonicalForTests(unittest.TestCase):
    def test_bare_ticker_is_us(self):
        self.assertEqual(sp.canonical_for(sp.parse_description("MU"), set()), "MU")

    def test_asx_suffix(self):
        self.assertEqual(sp.canonical_for(sp.parse_description("BC8 @ASX"), set()), "BC8.AX")

    def test_krx_adopts_existing_suffix(self):
        parsed = sp.parse_description("000660 @KRX")
        self.assertEqual(sp.canonical_for(parsed, {"000660.KS", "MU"}), "000660.KS")
        self.assertEqual(sp.canonical_for(parsed, {"000660.KQ"}), "000660.KQ")

    def test_krx_without_existing_row_is_unresolvable(self):
        self.assertIsNone(sp.canonical_for(sp.parse_description("011790 @KRX"), {"MU"}))

    def test_sehk_zero_pads_to_hk(self):
        self.assertEqual(sp.canonical_for(sp.parse_description("700 @SEHK"), set()), "0700.HK")
        self.assertEqual(sp.canonical_for(sp.parse_description("83010 @SEHK"), set()), "83010.HK")

    def test_unknown_exchange_is_unresolvable(self):
        self.assertIsNone(sp.canonical_for(sp.parse_description("SAP @IBIS"), set()))

    def test_result_must_be_canonical(self):
        # A ticker that maps to a non-canonical string must not leak through.
        self.assertIsNone(sp.canonical_for(
            {"asset": "stock", "ticker": "TOOLONGTICKER", "exchange": None}, set()))

    def test_symbol_patterns_are_the_validate_records_object(self):
        self.assertIs(sp.SYMBOL_PATTERNS, vr.SYMBOL_PATTERNS)


class DefaultKindTests(unittest.TestCase):
    def test_signs_and_rights(self):
        self.assertEqual(sp.default_kind("CALL", 15), "long-call")
        self.assertEqual(sp.default_kind("CALL", -2), "short-call")
        self.assertEqual(sp.default_kind("PUT", 13), "long-put")
        self.assertEqual(sp.default_kind("PUT", -13), "short-put")


AS_OF = D(2026, 7, 13)
ACCT = "U200"
OTHER = "U100"


def _portfolio():
    return {
        "schema": "portfolio/v1", "as_of": "2026-07-05", "base_currency": "USD",
        "cash": {"USD": 100.0},
        "accounts": {OTHER: {"last_synced": "2026-07-05"},
                     ACCT: {"last_synced": "2026-07-05"}},
        "holdings": [
            {"symbol": "GOOG", "qty": 200, "avg_cost": 358.59, "currency": "USD",
             "account": OTHER},
            {"symbol": "MU", "qty": 30, "avg_cost": 902.08, "currency": "USD",
             "account": ACCT},
            {"symbol": "000660.KS", "qty": 80, "avg_cost": 2335525, "currency": "KRW",
             "account": ACCT},
            {"symbol": "BOXX", "qty": 3860, "avg_cost": 117.01, "currency": "USD",
             "account": ACCT},
        ],
        "option_legs": [
            {"kind": "long-put", "underlying": "QQQ", "strike": 700,
             "expiry": D(2026, 7, 31), "qty": 5, "currency": "USD",
             "multiplier": 100, "account": ACCT, "combo": "bear-put"},
            {"kind": "short-put", "underlying": "QQQ", "strike": 665,
             "expiry": D(2026, 7, 31), "qty": -5, "currency": "USD",
             "multiplier": 100, "account": ACCT, "combo": "bear-put"},
            {"kind": "cash-secured-put", "underlying": "ACME", "strike": 90,
             "expiry": D(2026, 9, 18), "qty": -1, "premium": 3.5,
             "currency": "USD", "multiplier": 100, "account": ACCT},
        ],
    }


def _pos(cid, desc, qty, avg, cur="USD", price=10.0, asset="STK"):
    return {"contract_id": cid, "contract_description": desc, "position": qty,
            "market_price": price, "market_value": price * qty, "currency": cur,
            "average_price": avg, "unrealized_pnl": 0, "daily_pnl": 0,
            "asset_class": asset}


def _merge(portfolio, positions, **kw):
    kw.setdefault("account", ACCT)
    kw.setdefault("as_of", AS_OF)
    return sp.merge(portfolio, {"positions": positions}, **kw)


def _changes(report, kind=None):
    out = report["changes"]
    if kind:
        out = [c for c in out if c["kind"] == kind]
    return out


class MergeStockTests(unittest.TestCase):
    def test_matched_update_qty_and_avg_cost(self):
        snap = [_pos(9939, "MU", 45, 943.81),
                _pos(1, "000660 @KRX", 80, 2335525.475, cur="KRW"),
                _pos(2, "BOXX", 3860, 117.0066)]
        new, report = _merge(_portfolio(), snap)
        mu = [h for h in new["holdings"] if h["symbol"] == "MU"][0]
        self.assertEqual(mu["qty"], 45)
        self.assertAlmostEqual(mu["avg_cost"], 943.81)
        self.assertEqual(mu["broker_contract_id"], 9939)
        resized = _changes(report, "position_resized")
        self.assertEqual([c["symbol"] for c in resized if not
                          c["evidence"].get("below_epsilon")], ["MU"])

    def test_below_epsilon_resize_is_logged_but_gated_off(self):
        snap = [_pos(2, "BOXX", 3861, 117.01),
                _pos(9939, "MU", 30, 902.08),
                _pos(1, "000660 @KRX", 80, 2335525, cur="KRW")]
        new, report = _merge(_portfolio(), snap)
        boxx = _changes(report, "position_resized")
        self.assertTrue(all(c["evidence"]["below_epsilon"] for c in boxx))
        row = [h for h in new["holdings"] if h["symbol"] == "BOXX"][0]
        self.assertEqual(row["qty"], 3861)  # file stays true even below epsilon

    def test_fractional_quantities_survive(self):
        p = _portfolio()
        p["holdings"].append({"symbol": "IBKR", "qty": 16.4331, "avg_cost": 42.6,
                              "currency": "USD", "account": ACCT})
        snap = [_pos(5, "IBKR", 16.4331, 42.6), _pos(9939, "MU", 30, 902.08),
                _pos(1, "000660 @KRX", 80, 2335525, cur="KRW"),
                _pos(2, "BOXX", 3860, 117.01)]
        _, report = _merge(p, snap)
        self.assertEqual(_changes(report, "position_resized"), [])

    def test_new_position_joins_pinned_account(self):
        snap = [_pos(3, "VST", 200, 144.85), _pos(9939, "MU", 30, 902.08),
                _pos(1, "000660 @KRX", 80, 2335525, cur="KRW"),
                _pos(2, "BOXX", 3860, 117.01)]
        new, report = _merge(_portfolio(), snap)
        vst = [h for h in new["holdings"] if h["symbol"] == "VST"][0]
        self.assertEqual(vst["account"], ACCT)
        self.assertEqual([c["symbol"] for c in _changes(report, "position_new")],
                         ["VST"])

    def test_new_krx_code_needs_mapping(self):
        snap = [_pos(4, "011790 @KRX", 200, 96557.9, cur="KRW"),
                _pos(9939, "MU", 30, 902.08),
                _pos(1, "000660 @KRX", 80, 2335525, cur="KRW"),
                _pos(2, "BOXX", 3860, 117.01)]
        _, report = _merge(_portfolio(), snap)
        self.assertEqual([n["contract_id"] for n in report["needs_mapping"]], [4])

    def test_resolve_map_pins_new_krx_code(self):
        snap = [_pos(4, "011790 @KRX", 200, 96557.9, cur="KRW"),
                _pos(9939, "MU", 30, 902.08),
                _pos(1, "000660 @KRX", 80, 2335525, cur="KRW"),
                _pos(2, "BOXX", 3860, 117.01)]
        new, report = _merge(_portfolio(), snap, resolve_map={4: "011790.KS"})
        self.assertEqual(report["needs_mapping"], [])
        row = [h for h in new["holdings"] if h["symbol"] == "011790.KS"][0]
        self.assertEqual(row["broker_contract_id"], 4)

    def test_cross_account_symbol_never_touches_other_account(self):
        # GOOG exists only in OTHER; buying GOOG in the pinned account must
        # create a new pinned row, not rewrite OTHER's row (design C2).
        snap = [_pos(6, "GOOG", 50, 400.0), _pos(9939, "MU", 30, 902.08),
                _pos(1, "000660 @KRX", 80, 2335525, cur="KRW"),
                _pos(2, "BOXX", 3860, 117.01)]
        new, report = _merge(_portfolio(), snap)
        other = [h for h in new["holdings"]
                 if h["symbol"] == "GOOG" and h["account"] == OTHER][0]
        self.assertEqual(other["qty"], 200)  # untouched
        pinned = [h for h in new["holdings"]
                  if h["symbol"] == "GOOG" and h["account"] == ACCT]
        self.assertEqual(len(pinned), 1)

    def test_currency_mismatch_is_needs_mapping(self):
        snap = [_pos(9939, "MU", 30, 902.08, cur="HKD"),
                _pos(1, "000660 @KRX", 80, 2335525, cur="KRW"),
                _pos(2, "BOXX", 3860, 117.01)]
        new, report = _merge(_portfolio(), snap)
        self.assertTrue(any(n["contract_id"] == 9939 for n in report["needs_mapping"]))
        mu = [h for h in new["holdings"] if h["symbol"] == "MU"][0]
        self.assertEqual(mu["qty"], 30)  # not updated

    def test_broker_contract_id_is_write_once(self):
        # Stored id 1234 + payload cid 9999 for the same symbol: numerics
        # still update via the symbol match, the stored id is never rewritten.
        p = _portfolio()
        mu = [h for h in p["holdings"] if h["symbol"] == "MU"][0]
        mu["broker_contract_id"] = 1234
        snap = [_pos(9999, "MU", 45, 943.81),
                _pos(1, "000660 @KRX", 80, 2335525, cur="KRW"),
                _pos(2, "BOXX", 3860, 117.01)]
        new, _ = _merge(p, snap)
        row = [h for h in new["holdings"] if h["symbol"] == "MU"][0]
        self.assertEqual(row["broker_contract_id"], 1234)
        self.assertEqual(row["qty"], 45)
        self.assertAlmostEqual(row["avg_cost"], 943.81)


class MergeCloseTests(unittest.TestCase):
    def test_absent_pinned_row_moves_to_suspected_closed(self):
        snap = [_pos(9939, "MU", 30, 902.08),
                _pos(1, "000660 @KRX", 80, 2335525, cur="KRW")]  # BOXX absent
        new, report = _merge(_portfolio(), snap)
        self.assertEqual([c["symbol"] for c in _changes(report, "position_closed")],
                         ["BOXX"])
        self.assertEqual([r["symbol"] for r in new["suspected_closed"]], ["BOXX"])
        self.assertEqual(new["suspected_closed"][0]["suspected_closed_on"],
                         AS_OF.isoformat())
        self.assertNotIn("BOXX", [h["symbol"] for h in new["holdings"]])

    def test_other_account_rows_never_suspected(self):
        snap = [_pos(9939, "MU", 30, 902.08),
                _pos(1, "000660 @KRX", 80, 2335525, cur="KRW"),
                _pos(2, "BOXX", 3860, 117.01)]
        new, report = _merge(_portfolio(), snap)
        self.assertNotIn("GOOG", [c["symbol"] for c in _changes(report)])

    def test_all_positions_sold_closes_cleanly(self):
        # Non-empty snapshot with zero pinned matches is legitimate only when
        # the pinned account really sold everything; guard handles empty.
        snap = [_pos(9939, "MU", 45, 943.81)]
        new, report = _merge(_portfolio(), snap)
        closed = {c["symbol"] for c in _changes(report, "position_closed")}
        self.assertEqual(closed, {"000660.KS", "BOXX"})

    def test_empty_snapshot_guard_degrades(self):
        new, report = _merge(_portfolio(), [])
        self.assertTrue(report["guard_triggered"])
        material = [c for c in _changes(report) if c["kind"] != "sync_staleness"]
        self.assertEqual(material, [])  # staleness accounting still runs
        self.assertEqual(new, _portfolio())  # untouched

    def test_stk_only_snapshot_never_closes_option_legs(self):
        # OPT wholly absent from the snapshot is ambiguous (partial dump vs
        # sold-all), so the legs close pass must not run at all.
        snap = [_pos(9939, "MU", 30, 902.08),
                _pos(1, "000660 @KRX", 80, 2335525, cur="KRW"),
                _pos(2, "BOXX", 3860, 117.01)]
        new, report = _merge(_portfolio(), snap)
        self.assertEqual(new["option_legs"], _portfolio()["option_legs"])
        self.assertNotIn("suspected_closed", new)
        self.assertEqual(_changes(report, "option_leg_closed"), [])

    def test_opt_only_snapshot_never_closes_holdings(self):
        snap = [_pos(10, "QQQ Jul31'26 700 PUT @AMEX", 5, 27.38, asset="OPT"),
                _pos(11, "QQQ Jul31'26 665 PUT @AMEX", -5, 15.37, asset="OPT"),
                _pos(12, "ACME Sep18'26 90 PUT", -1, 3.5, asset="OPT")]
        new, report = _merge(_portfolio(), snap)
        self.assertEqual(new["holdings"], _portfolio()["holdings"])
        self.assertNotIn("suspected_closed", new)
        self.assertEqual(_changes(report, "position_closed"), [])


class MergeOptionTests(unittest.TestCase):
    SNAP_BASE = [
        _pos(9939, "MU", 30, 902.08),
        _pos(1, "000660 @KRX", 80, 2335525, cur="KRW"),
        _pos(2, "BOXX", 3860, 117.01),
    ]

    def test_matched_leg_updates_qty_preserves_kind_and_combo(self):
        snap = self.SNAP_BASE + [
            _pos(10, "QQQ Jul31'26 700 PUT @AMEX", 3, 27.38, asset="OPT"),
            _pos(11, "QQQ Jul31'26 665 PUT @AMEX", -3, 15.37, asset="OPT"),
            _pos(12, "ACME Sep18'26 90 PUT", -1, 3.5, asset="OPT"),
        ]
        new, report = _merge(_portfolio(), snap)
        long700 = [l for l in new["option_legs"]
                   if l["underlying"] == "QQQ" and l["strike"] == 700][0]
        self.assertEqual(long700["qty"], 3)
        self.assertEqual(long700["kind"], "long-put")   # owner-owned, preserved
        self.assertEqual(long700["combo"], "bear-put")  # preserved
        self.assertNotIn("premium", long700)            # never added when absent
        csp = [l for l in new["option_legs"] if l["underlying"] == "ACME"][0]
        self.assertEqual(csp["kind"], "cash-secured-put")
        self.assertAlmostEqual(csp["premium"], 3.5)     # present -> updated

    def test_new_leg_gets_default_kind_and_premium(self):
        snap = self.SNAP_BASE + [
            _pos(10, "QQQ Jul31'26 700 PUT @AMEX", 5, 27.38, asset="OPT"),
            _pos(11, "QQQ Jul31'26 665 PUT @AMEX", -5, 15.37, asset="OPT"),
            _pos(12, "ACME Sep18'26 90 PUT", -1, 3.5, asset="OPT"),
            _pos(13, "QQQ Sep18'26 720 PUT @AMEX", 1, 34.64, asset="OPT"),
        ]
        new, report = _merge(_portfolio(), snap)
        leg = [l for l in new["option_legs"] if l.get("broker_contract_id") == 13][0]
        self.assertEqual(leg["kind"], "long-put")
        self.assertAlmostEqual(leg["premium"], 34.64)  # per-share, no 100x
        self.assertEqual(leg["multiplier"], 100)
        self.assertEqual([c["kind"] for c in _changes(report, "option_leg_new")],
                         ["option_leg_new"])

    def test_multi_row_contract_sum_match_is_no_change(self):
        p = _portfolio()
        p["option_legs"].append(
            {"kind": "long-put", "underlying": "QQQ", "strike": 700,
             "expiry": D(2026, 7, 31), "qty": 2, "currency": "USD",
             "multiplier": 100, "account": ACCT})  # 5 + 2 = 7 across two rows
        snap = self.SNAP_BASE + [
            _pos(10, "QQQ Jul31'26 700 PUT @AMEX", 7, 27.38, asset="OPT"),
            _pos(11, "QQQ Jul31'26 665 PUT @AMEX", -5, 15.37, asset="OPT"),
            _pos(12, "ACME Sep18'26 90 PUT", -1, 3.5, asset="OPT"),
        ]
        new, report = _merge(p, snap)
        self.assertEqual(_changes(report, "option_leg_resized"), [])
        self.assertFalse(any(n["contract_id"] == 10 for n in report["needs_mapping"]))

    def test_multi_row_contract_sum_mismatch_is_needs_mapping(self):
        p = _portfolio()
        p["option_legs"].append(
            {"kind": "long-put", "underlying": "QQQ", "strike": 700,
             "expiry": D(2026, 7, 31), "qty": 2, "currency": "USD",
             "multiplier": 100, "account": ACCT})
        snap = self.SNAP_BASE + [
            _pos(10, "QQQ Jul31'26 700 PUT @AMEX", 3, 27.38, asset="OPT"),
            _pos(11, "QQQ Jul31'26 665 PUT @AMEX", -5, 15.37, asset="OPT"),
            _pos(12, "ACME Sep18'26 90 PUT", -1, 3.5, asset="OPT"),
        ]
        new, report = _merge(p, snap)
        self.assertTrue(any(n["contract_id"] == 10 for n in report["needs_mapping"]))
        rows = [l for l in new["option_legs"]
                if l["underlying"] == "QQQ" and l["strike"] == 700]
        self.assertEqual(sorted(l["qty"] for l in rows), [2, 5])  # untouched

    def test_absent_leg_is_suspected_closed(self):
        snap = self.SNAP_BASE + [
            _pos(10, "QQQ Jul31'26 700 PUT @AMEX", 5, 27.38, asset="OPT"),
            _pos(11, "QQQ Jul31'26 665 PUT @AMEX", -5, 15.37, asset="OPT"),
        ]  # ACME csp absent
        new, report = _merge(_portfolio(), snap)
        self.assertEqual([c["symbol"] for c in _changes(report, "option_leg_closed")],
                         ["ACME"])
        self.assertEqual(new["suspected_closed"][0]["underlying"], "ACME")

    def test_unsupported_asset_class_is_needs_mapping(self):
        snap = self.SNAP_BASE + [_pos(99, "ESZ6", 1, 5000.0, asset="FUT")]
        _, report = _merge(_portfolio(), snap)
        self.assertTrue(any(n["contract_id"] == 99 for n in report["needs_mapping"]))

    def test_unkeyable_leg_is_left_in_place_not_quarantined(self):
        # kind='synthetic' derives no PUT/CALL right and the leg has no
        # broker_contract_id, so it can never match any payload row. It must
        # stay in option_legs untouched, surface in needs_mapping, never enter
        # suspected_closed — and the payload row for that contract must not
        # create a default-kind duplicate.
        p = _portfolio()
        p["option_legs"].append(
            {"kind": "synthetic", "underlying": "QQQ", "strike": 720,
             "expiry": D(2026, 9, 18), "qty": 1, "currency": "USD",
             "multiplier": 100, "account": ACCT})
        snap = self.SNAP_BASE + [
            _pos(10, "QQQ Jul31'26 700 PUT @AMEX", 5, 27.38, asset="OPT"),
            _pos(11, "QQQ Jul31'26 665 PUT @AMEX", -5, 15.37, asset="OPT"),
            _pos(12, "ACME Sep18'26 90 PUT", -1, 3.5, asset="OPT"),
            _pos(13, "QQQ Sep18'26 720 PUT @AMEX", 1, 34.64, asset="OPT"),
        ]
        new, report = _merge(p, snap)
        synth = [l for l in new["option_legs"] if l.get("kind") == "synthetic"]
        self.assertEqual(len(synth), 1)                    # left in place
        self.assertEqual(synth[0], p["option_legs"][-1])   # all fields untouched
        self.assertNotIn("suspected_closed", new)
        self.assertEqual(_changes(report, "option_leg_closed"), [])
        self.assertTrue(any("not indexable" in n["reason"]
                            for n in report["needs_mapping"]))
        self.assertEqual([l for l in new["option_legs"]
                          if l.get("broker_contract_id") == 13], [])  # no dup
        self.assertEqual(len(new["option_legs"]), 4)


class MergeAccountingTests(unittest.TestCase):
    def test_last_synced_bumped_for_pinned_account_only(self):
        snap = [_pos(9939, "MU", 30, 902.08),
                _pos(1, "000660 @KRX", 80, 2335525, cur="KRW"),
                _pos(2, "BOXX", 3860, 117.01)]
        new, _ = _merge(_portfolio(), snap)
        self.assertEqual(new["accounts"][ACCT]["last_synced"], AS_OF.isoformat())
        self.assertEqual(new["accounts"][OTHER]["last_synced"], "2026-07-05")

    def test_stale_account_yields_sync_staleness_finding(self):
        snap = [_pos(9939, "MU", 30, 902.08),
                _pos(1, "000660 @KRX", 80, 2335525, cur="KRW"),
                _pos(2, "BOXX", 3860, 117.01)]
        _, report = _merge(_portfolio(), snap)  # OTHER last synced 8d ago
        stale = [c for c in report["changes"] if c["kind"] == "sync_staleness"]
        self.assertEqual([c["account"] for c in stale], [OTHER])
        self.assertEqual(stale[0]["urgency"], "review")

    def test_uncovered_accounts_reported_with_age(self):
        snap = [_pos(9939, "MU", 30, 902.08),
                _pos(1, "000660 @KRX", 80, 2335525, cur="KRW"),
                _pos(2, "BOXX", 3860, 117.01)]
        _, report = _merge(_portfolio(), snap)
        self.assertEqual(report["uncovered_accounts"],
                         [{"account": OTHER, "last_synced": "2026-07-05"}])

    def test_idempotent_rerun_yields_zero_changes(self):
        snap = [_pos(9939, "MU", 45, 943.81),
                _pos(1, "000660 @KRX", 80, 2335525, cur="KRW"),
                _pos(2, "BOXX", 2955, 117.0066)]
        first, _ = _merge(_portfolio(), snap)
        second, report = _merge(copy.deepcopy(first), snap)
        material = [c for c in _changes(report)
                    if c["kind"] != "sync_staleness"
                    and not c["evidence"].get("below_epsilon")]
        self.assertEqual(material, [])
        self.assertEqual(second, first)


SCRIPT = REPO_ROOT / "scripts" / "sync_portfolio.py"
FIXTURE_HOME = REPO_ROOT / "tests" / "fixtures" / "sync-home"
POSITIONS = REPO_ROOT / "tests" / "fixtures" / "sync-positions.json"


def _run(*args, home=None):
    cmd = [sys.executable, str(SCRIPT), "--home", str(home or FIXTURE_HOME),
           "--as-of", "2026-07-13", "--format", "json", *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def _copy_home(tmpdir):
    import shutil
    dst = pathlib.Path(tmpdir) / "home"
    shutil.copytree(FIXTURE_HOME, dst)
    return dst


class CliTests(unittest.TestCase):
    def test_dry_run_reports_and_leaves_file_byte_identical(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            home = _copy_home(tmp)
            before = (home / "portfolio.yaml").read_bytes()
            proc = _run("--positions", str(POSITIONS), "--account", "U200",
                        "--dry-run", home=home)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            report = json.loads(proc.stdout)
            self.assertFalse(report["wrote"])
            self.assertTrue(report["changes"])
            self.assertEqual((home / "portfolio.yaml").read_bytes(), before)

    def test_write_bumps_as_of_and_is_idempotent(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            home = _copy_home(tmp)
            proc = _run("--positions", str(POSITIONS), "--account", "U200",
                        home=home)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(json.loads(proc.stdout)["wrote"])
            data = yaml.safe_load((home / "portfolio.yaml").read_text())
            self.assertEqual(str(data["as_of"]), "2026-07-13")
            self.assertEqual(str(data["accounts"]["U200"]["last_synced"]),
                             "2026-07-13")
            mu = [h for h in data["holdings"] if h["symbol"] == "MU"][0]
            self.assertEqual(mu["qty"], 45)
            # BOXX resized; GOOG (U100) untouched; ACME leg matched.
            proc2 = _run("--positions", str(POSITIONS), "--account", "U200",
                         home=home)
            report2 = json.loads(proc2.stdout)
            material = [c for c in report2["changes"]
                        if c["kind"] != "sync_staleness"
                        and not c.get("evidence", {}).get("below_epsilon")]
            self.assertEqual(material, [])
            self.assertFalse(report2["wrote"])

    def test_resolve_round_trip_pins_contract_id(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            home = _copy_home(tmp)
            resolve = pathlib.Path(tmp) / "resolve.yaml"
            resolve.write_text("4: 011790.KS\n")
            proc = _run("--positions", str(POSITIONS), "--account", "U200",
                        "--resolve", str(resolve), home=home)
            report = json.loads(proc.stdout)
            self.assertEqual(report["needs_mapping"], [])
            data = yaml.safe_load((home / "portfolio.yaml").read_text())
            row = [h for h in data["holdings"] if h["symbol"] == "011790.KS"][0]
            self.assertEqual(row["broker_contract_id"], 4)

    def test_emit_prices_contains_stk_rows_only(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            home = _copy_home(tmp)
            out = pathlib.Path(tmp) / "spots.yaml"
            _run("--positions", str(POSITIONS), "--account", "U200",
                 "--resolve", str(pathlib.Path(tmp) / "nope.yaml"),
                 home=home)  # missing resolve file must not crash the next run
            proc = _run("--positions", str(POSITIONS), "--account", "U200",
                        "--emit-prices", str(out), home=home)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            prices = yaml.safe_load(out.read_text())
            self.assertEqual(prices.get("MU"), 921.51)
            self.assertEqual(prices.get("BOXX"), 117.4)
            self.assertNotIn("ACME", prices)  # OPT leg price must not leak

    def test_comment_guard_refuses_to_write(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            home = _copy_home(tmp)
            path = home / "portfolio.yaml"
            path.write_text("# hand note\n" + path.read_text())
            before = path.read_bytes()
            proc = _run("--positions", str(POSITIONS), "--account", "U200",
                        home=home)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            report = json.loads(proc.stdout)
            self.assertFalse(report["wrote"])
            self.assertIn("comment", report["blocked"])
            self.assertEqual(path.read_bytes(), before)

    def test_degraded_mode_emits_staleness_without_positions(self):
        proc = _run()  # no --positions, read-only fixture home
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertFalse(report["wrote"])
        stale = [c for c in report["changes"] if c["kind"] == "sync_staleness"]
        self.assertEqual({c["account"] for c in stale}, {"U100", "U200"})

    def test_no_account_with_positions_is_report_only(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            home = _copy_home(tmp)
            before = (home / "portfolio.yaml").read_bytes()
            proc = _run("--positions", str(POSITIONS), home=home)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            report = json.loads(proc.stdout)
            self.assertFalse(report["wrote"])
            self.assertEqual(report["inferred_account"], "U200")
            self.assertEqual((home / "portfolio.yaml").read_bytes(), before)

    def test_bad_home_is_exit_2(self):
        proc = _run(home="/nonexistent/nowhere")
        self.assertEqual(proc.returncode, 2)

    def test_bad_positions_json_is_exit_2(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            bad = pathlib.Path(tmp) / "bad.json"
            bad.write_text("{not json")
            proc = _run("--positions", str(bad), "--account", "U200")
            self.assertEqual(proc.returncode, 2)

    def test_post_write_file_passes_validate_records(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            home = _copy_home(tmp)
            _run("--positions", str(POSITIONS), "--account", "U200", home=home)
            proc = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "validate_records.py"),
                 "--home", str(home)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
