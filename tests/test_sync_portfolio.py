import copy
import datetime
import json
import pathlib
import subprocess
import sys
import unittest

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
