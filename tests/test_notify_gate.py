import datetime
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import notify_gate as ng  # noqa: E402


def _finding(symbol="ACME", kind="price_trigger", urgency="act", **evidence):
    evidence.setdefault("group", "trim_exit")
    evidence.setdefault("level", 185)
    return {"symbol": symbol, "kind": kind, "urgency": urgency,
            "detail": "d", "evidence": evidence}


def _sweep(findings=(), data_gaps=(), llm_todo=()):
    return {"as_of": "2026-07-13", "findings": list(findings),
            "data_gaps": list(data_gaps), "llm_todo": list(llm_todo)}


def _sync(changes=(), needs_mapping=(), uncovered=(), blocked=None):
    return {"as_of": "2026-07-13", "account": "U200", "changes": list(changes),
            "needs_mapping": list(needs_mapping),
            "uncovered_accounts": list(uncovered), "blocked": blocked,
            "wrote": True}


NOW = datetime.datetime(2026, 7, 13, 8, 30)


class KeyTests(unittest.TestCase):
    def test_stable_keys_per_design(self):
        self.assertEqual(ng.finding_key(_finding()), "ACME|price_trigger|trim_exit|185")
        self.assertEqual(ng.finding_key({"symbol": "A", "kind": "drawdown",
                                         "urgency": "review", "evidence": {}}),
                         "A|drawdown")
        self.assertEqual(ng.finding_key(
            {"symbol": "A", "kind": "review_expiry", "urgency": "review",
             "evidence": {"review_by": "2026-07-01"}}), "A|review_expiry|2026-07-01")
        self.assertEqual(ng.finding_key(
            {"symbol": "A", "kind": "earnings_proximity", "urgency": "watch",
             "evidence": {"next_earnings": "2026-07-20"}}),
            "A|earnings_proximity|2026-07-20")
        self.assertEqual(ng.finding_key(
            {"symbol": "QQQ", "kind": "options_assignment", "urgency": "watch",
             "evidence": {"strike": 700, "expiry": "2026-08-31"}}),
            "QQQ|options_assignment|700|2026-08-31")
        self.assertEqual(ng.finding_key(
            {"account": "U100", "kind": "sync_staleness", "urgency": "review",
             "evidence": {}}), "U100|sync_staleness")
        self.assertEqual(ng.finding_key(
            {"contract_id": 4, "contract_description": "011790 @KRX",
             "reason": "r"}), "4|needs_mapping")

    def test_needs_mapping_none_contract_id_disambiguated(self):
        a = {"contract_id": None,
             "contract_description": "option_leg AMD 100 2026-08-31 put",
             "reason": "r"}
        b = {"contract_id": None,
             "contract_description": "option_leg AMD 120 2026-08-31 call",
             "reason": "r"}
        self.assertNotEqual(ng.finding_key(a), ng.finding_key(b))
        decision, _ = ng.decide(_sweep(), _sync(needs_mapping=[a, b]), {},
                                now=NOW, max_gap_hours=36.0)
        self.assertTrue(decision["notify"])
        self.assertEqual(len(decision["new"]), 2)


class GateTests(unittest.TestCase):
    def _decide(self, state, findings=(), changes=(), needs=(), blocked=None,
                now=NOW):
        return ng.decide(_sweep(findings), _sync(changes, needs, blocked=blocked),
                         state, now=now, max_gap_hours=36.0)

    def test_new_finding_notifies(self):
        decision, state = self._decide({}, findings=[_finding()])
        self.assertTrue(decision["notify"])
        self.assertEqual(len(decision["new"]), 1)
        self.assertIn("ACME|price_trigger|trim_exit|185", state["findings"])

    def test_standing_finding_is_suppressed(self):
        _, state = self._decide({}, findings=[_finding()])
        decision, _ = self._decide(state, findings=[_finding()],
                                   now=NOW + datetime.timedelta(hours=8))
        self.assertFalse(decision["notify"])
        self.assertEqual([s["key"] for s in decision["standing"]],
                         ["ACME|price_trigger|trim_exit|185"])

    def test_urgency_escalation_notifies(self):
        _, state = self._decide({}, findings=[_finding(urgency="watch")])
        decision, _ = self._decide(state, findings=[_finding(urgency="act")],
                                   now=NOW + datetime.timedelta(hours=8))
        self.assertTrue(decision["notify"])
        self.assertEqual(len(decision["escalated"]), 1)

    def test_cleared_then_recrossed_notifies_again(self):
        _, state = self._decide({}, findings=[_finding()])
        decision, state = self._decide(state, findings=[],
                                       now=NOW + datetime.timedelta(hours=8))
        self.assertFalse(decision["notify"])
        self.assertEqual([c["key"] for c in decision["cleared"]],
                         ["ACME|price_trigger|trim_exit|185"])
        decision, _ = self._decide(state, findings=[_finding()],
                                   now=NOW + datetime.timedelta(hours=16))
        self.assertTrue(decision["notify"])

    def test_sync_changes_always_notify_except_below_epsilon(self):
        change = {"symbol": "MU", "kind": "position_resized", "urgency": "watch",
                  "detail": "d", "evidence": {"below_epsilon": False}}
        quiet = {"symbol": "BOXX", "kind": "position_resized", "urgency": "watch",
                 "detail": "d", "evidence": {"below_epsilon": True}}
        decision, _ = self._decide({}, changes=[change, quiet])
        self.assertTrue(decision["notify"])
        self.assertEqual([c["item"]["symbol"] for c in decision["new"]], ["MU"])

    def test_sync_staleness_dedupes_like_standing(self):
        stale = {"account": "U100", "kind": "sync_staleness", "urgency": "review",
                 "detail": "d", "evidence": {}}
        _, state = self._decide({}, changes=[stale])
        decision, _ = self._decide(state, changes=[stale],
                                   now=NOW + datetime.timedelta(hours=8))
        self.assertFalse(decision["notify"])

    def test_needs_mapping_dedupes(self):
        need = {"contract_id": 4, "contract_description": "011790 @KRX",
                "reason": "r"}
        _, state = self._decide({}, needs=[need])
        decision, _ = self._decide(state, needs=[need],
                                   now=NOW + datetime.timedelta(hours=8))
        self.assertFalse(decision["notify"])

    def test_blocked_always_notifies(self):
        decision, _ = self._decide({}, blocked="comments present")
        self.assertTrue(decision["notify"])
        _, state = self._decide({}, blocked="comments present")
        decision, _ = self._decide(state, blocked="comments present",
                                   now=NOW + datetime.timedelta(hours=8))
        self.assertTrue(decision["notify"])  # blocked is never suppressed

    def test_watchdog_flags_gap_over_max(self):
        _, state = self._decide({})
        late = NOW + datetime.timedelta(hours=60)
        decision, _ = self._decide(state, now=late)
        self.assertTrue(decision["notify"])
        self.assertAlmostEqual(decision["missed_gap_hours"], 60.0)

    def test_state_round_trip_through_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            (tmp / "sweep.json").write_text(json.dumps(_sweep([_finding()])))
            (tmp / "sync.json").write_text(json.dumps(_sync()))
            state_path = tmp / "state.json"
            cmd = [sys.executable, str(REPO_ROOT / "scripts" / "notify_gate.py"),
                   "--findings", str(tmp / "sweep.json"),
                   "--changes", str(tmp / "sync.json"),
                   "--state", str(state_path),
                   "--now", "2026-07-13T08:30:00", "--run-id", "2026-07-13 am"]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(json.loads(proc.stdout)["notify"])
            proc2 = subprocess.run(
                cmd[:-4] + ["--now", "2026-07-13T16:10:00",
                            "--run-id", "2026-07-13 pm"],
                capture_output=True, text=True)
            self.assertFalse(json.loads(proc2.stdout)["notify"])
            state = json.loads(state_path.read_text())
            self.assertEqual(len(state["runs"]), 2)

    def test_corrupted_state_is_tolerated(self):
        # findings is the wrong top-level shape (a list, not a dict).
        d1, _ = ng.decide(_sweep([_finding()]), _sync(),
                          {"findings": ["garbage"], "runs": []},
                          now=NOW, max_gap_hours=36.0)
        self.assertTrue(d1["notify"])
        self.assertEqual(len(d1["new"]), 1)
        # findings is a dict but a value is a non-dict string.
        corrupt = {"findings": {"ACME|price_trigger|trim_exit|185": "nope"},
                   "runs": []}
        d2, _ = ng.decide(_sweep([_finding()]), _sync(), corrupt,
                          now=NOW, max_gap_hours=36.0)
        self.assertTrue(d2["notify"])
        self.assertEqual(len(d2["new"]), 1)

    def test_normal_gap_reports_no_missed_hours(self):
        _, state = self._decide({})
        decision, _ = self._decide(state,
                                   now=NOW + datetime.timedelta(hours=8))
        self.assertIsNone(decision["missed_gap_hours"])

    def test_de_escalation_is_silent_but_tracked(self):
        _, state = self._decide({}, findings=[_finding(urgency="act")])
        decision, new_state = self._decide(
            state, findings=[_finding(urgency="watch")],
            now=NOW + datetime.timedelta(hours=8))
        self.assertFalse(decision["notify"])
        self.assertEqual(
            new_state["findings"]["ACME|price_trigger|trim_exit|185"]["urgency"],
            "watch")

    def test_main_creates_missing_state_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            (tmp / "sweep.json").write_text(json.dumps(_sweep([_finding()])))
            (tmp / "sync.json").write_text(json.dumps(_sync()))
            state_path = tmp / "nested" / "deeper" / "state.json"
            cmd = [sys.executable, str(REPO_ROOT / "scripts" / "notify_gate.py"),
                   "--findings", str(tmp / "sweep.json"),
                   "--changes", str(tmp / "sync.json"),
                   "--state", str(state_path),
                   "--now", "2026-07-13T08:30:00"]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(state_path.exists())
            # R1 atomic write cleans up its temp file on success.
            self.assertEqual(list(state_path.parent.glob(".state-*")), [])


if __name__ == "__main__":
    unittest.main()
