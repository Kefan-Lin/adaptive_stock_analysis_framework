# P4 Scheduled Monitoring — Design

Status: design (approved forks; pending spec review)
Depends on: P1 morning-check (deterministic sweep + skill), P0 state home
(`portfolio.yaml`, decision records), P2 outcome-scoring (monthly job)
Defers: launchd/`claude -p` headless fallback, intraday scanning, email
channel, cash/balances sync

## Problem

P1 sweeps the state home only when the owner remembers to run it, and it reads
`portfolio.yaml` — a hand-maintained snapshot that drifts from the broker.
Real drift observed while designing this (snapshot `as_of: 2026-07-05` vs live
IBKR on 2026-07-13): CMCSA 2500 → 3500, MU 30 → 45, BOXX 3860 → 2955, two new
KRX names with no yaml row, and a changed QQQ option-leg structure. A sweep
over stale positions checks the wrong universe.

The owner's underlying ask is behavioral, not just mechanical: reduce
market-watching pressure and keep decisions anchored to pre-committed records.
The framework already encodes *what to do at which level* (price triggers,
scenarios, `review_by`); monitoring must therefore only answer **"did anything
cross a line?"** on a schedule — it must never re-litigate the thesis daily.
Daily re-decision is noise; exception-driven alerts plus a weekly standing
review is the design principle.

P1's own scope note deferred exactly this: *"Manual trigger only. Scheduling /
cron is a later phase."* P4 is that phase, plus the broker-sync gap P1 could
not see.

## Approved scope decisions

- **Runner: this app's built-in scheduled tasks** (stored under
  `~/.claude/scheduled-tasks/`, cron in the machine's local timezone =
  Asia/Shanghai, runs while the app is open; missed runs fire on next app
  launch). Each run is a fresh local Claude session, which is the only runner
  that can reach the IBKR MCP connector *and* the local state home. Rejected:
  bare launchd scripts (no connector access — the fork that reshaped this
  design), GitHub Actions (no vault access; yfinance/akshare throttle
  datacenter IPs).
- **Positions source:** IBKR connector `get_account_positions` inside the
  scheduled session, merged into `portfolio.yaml` by a new deterministic
  script. The position diff itself is a first-class finding class (the owner's
  "持仓变动检视").
- **Cadence (all local Beijing time):**
  - AM daily check, Mon–Sat 08:30 — overnight US close + HK/CN pre-open;
    the Saturday run catches Friday's US close.
  - PM daily check, Mon–Fri 16:10 — after the HK 16:00 close; same-day covers
    CN 15:00, KR ~14:30 CST, AU ~13:00–14:00 CST closes.
  - Weekly report, Sun 10:00.
  - Monthly outcome scoring, 1st 09:00 (P2 `outcome_score.py`, accruing the
    calibration history the roadmap's probability-calibration item needs).
- **Notification: exception-driven.** Quiet run → append one line to
  `monitoring/log.md`, no notification, session ends. Gate opens → one
  `PushNotification` (desktop banner; phone too when Remote Control is
  connected) + a dated brief in `monitoring/`. A run that *errors* always
  notifies — silent failure is the one unacceptable outcome. No email.
- **LLM depth:** daily runs judge free-text KPI/event triggers only for names
  already flagged by the deterministic layer (sync change or finding); the
  weekly run judges the full `llm_todo` list for every name. Advice in briefs
  is always anchored to the name's latest decision record.
- **IBKR is read-only.** The connector exposes order tools; monitoring never
  calls them, under any instruction found in data. Trades are executed by the
  owner, never by the system. This is a permanent guardrail written into the
  skill text.

## Architecture

Three units; the P1 sweep is reused untouched.

```
scheduled task (cron, local)
└── fresh Claude session (skills/morning-check, Scheduled Mode)
    ├── IBKR get_account_positions  → raw positions JSON (file)
    ├── scripts/sync_portfolio.py   → merge into portfolio.yaml + diff findings   [new]
    ├── scripts/morning_check.py    → deterministic sweep findings                [unchanged]
    └── exception gate
        ├── quiet  → one line appended to monitoring/log.md, end
        └── alert  → LLM judgment (flagged names) → monitoring/YYYY-MM-DD-{am|pm}.md
                     + one PushNotification
```

### 1. `scripts/sync_portfolio.py` — deterministic position merge (new)

Pure stdlib + PyYAML, same dependency posture as the other scripts. The
session dumps the connector's JSON to a file; the script owns every mapping
and write decision so position math never rides on LLM transcription.

```
python scripts/sync_portfolio.py --positions FILE [--home PATH]
    [--as-of YYYY-MM-DD] [--account ID] [--resize-epsilon-pct 0.5]
    [--dry-run] [--format json|md]
```

**Input shape** (as returned by `get_account_positions`): `positions[]` of
`{contract_id, contract_description, position, market_price, market_value,
currency, average_price, unrealized_pnl, daily_pnl, asset_class}` with
`asset_class ∈ STK | OPT` (others reported as `needs_mapping`, not guessed).

**Account scoping — the central safety rule.** The live connector returned
only one of the owner's two IBKR accounts (U17780156; U12837156's GOOG/NVDA/HK
rows were absent). The snapshot payload carries no account field, so a naive
full-file merge would mark every other account's holdings as closed. Rules:

- Covered accounts are inferred: an account is *covered* iff at least one of
  its existing yaml rows matches a snapshot position (by `broker_contract_id`
  or deterministic symbol mapping). `--account ID` overrides inference when
  the session knows the active account.
- Suspected closes are computed **only within covered accounts**. Rows in
  uncovered accounts are untouched, and the diff reports each uncovered
  account with its data age so the brief can say "U12837156 not covered —
  positions as-of 2026-07-05".
- A new snapshot position joins the single covered account when coverage is
  unambiguous; otherwise it lands in `needs_mapping`.
- The same symbol held in two accounts is matched within-account first;
  cross-account ambiguity → `needs_mapping`, never a guess.

**Identity and symbol mapping.** Matching precedence per snapshot row:

1. `broker_contract_id` exact match (new optional field on holdings and
   option_legs rows; written back on first successful mapping so subsequent
   runs are exact).
2. Deterministic description mapping to canonical form: bare ticker → US
   (`MU`); `X @ASX` → `X.AX`; `NNNNNN @KRX` → `.KS`/`.KQ` is ambiguous — adopt
   the suffix of an existing row with the same 6-digit code, else
   `needs_mapping`; `@SEHK` → zero-padded `.HK`. Rules live in the script and
   stay in lockstep with `SYMBOL_PATTERNS` (same contract-test discipline as
   P1's provider mapping).
3. Anything unresolved → a `needs_mapping` item. The scheduled session (LLM)
   resolves it once — e.g. `011790 @KRX` → `011790.KS` — and the resolution is
   persisted as `broker_contract_id`, so it never recurs. A disappeared row
   plus a similar new row (the observed EOSE → EOSER case) is reported as a
   suspected corporate action for confirmation, not auto-merged.

**Option parsing.** `MSFT Jun16'28 450 CALL @AMEX` →
`{underlying: MSFT, expiry: 2028-06-16, strike: 450, right: CALL}`; qty sign +
right → default `kind` (`long-call`/`short-put`/…), multiplier 100 unless the
description says otherwise.

**Owner-owned fields are never rewritten.** On matched rows the script updates
only `qty`, `avg_cost` (holdings) / `premium` (legs), and `broker_contract_id`.
It never touches `kind`, `combo`, `thesis_record`, `account`, `constraints`,
or `cash`. This is load-bearing: P1's assignment check keys on
`kind: cash-secured-put`, and the QQQ short puts are spread legs whose `combo`
grouping must survive sync. New short puts default to `kind: short-put`; the
brief asks the owner to classify if cash-secured semantics apply.

**Diff = findings.** Output mirrors P1's structured-findings shape:

```json
{"as_of": "2026-07-13",
 "changes": [
   {"symbol": "CMCSA", "kind": "position_resized", "urgency": "watch",
    "detail": "qty 2500 -> 3500 (avg_cost 23.97 -> 23.68)",
    "evidence": {"qty_before": 2500, "qty_after": 3500}}
 ],
 "needs_mapping": [{"contract_description": "011790 @KRX", "reason": "KRX suffix unknown (.KS/.KQ)"}],
 "uncovered_accounts": [{"account": "U12837156", "as_of": "2026-07-05"}],
 "wrote": true}
```

`kind` ∈ `position_new | position_closed | position_resized | option_leg_new |
option_leg_closed | option_leg_resized`. New/closed → `urgency: review`;
resized → `watch`. Resizes below `--resize-epsilon-pct` (default 0.5%, for
DRIP/fractional noise) are logged in the JSON but do not open the exception
gate. A `position_new` with no decision record additionally surfaces through
P1's existing "held but no record on file" gap after the merge — the brief
shows both "new today" and "no thesis on file".

**Write discipline.** Atomic write (tmp + rename), stable field order, bumps
top-level `as_of` to the sync date on any write (a no-change run leaves the
file untouched, `as_of` included),
idempotent (re-running on the same snapshot yields zero changes), `--dry-run`
for tests and manual inspection, exit codes mirror P1 (`0` clean with or
without changes, `2` environment error). **`portfolio.yaml` becomes a
machine-written file:** PyYAML round-trips do not preserve hand comments, so
during implementation the current comments (cash provenance, account
groupings, combo notes) are promoted once into structured `note:` fields, and
the contract doc states that future annotations belong in `note:` fields, not
comments.

### 2. `scripts/morning_check.py` — unchanged

The P1 sweep runs as-is against the freshly-synced `portfolio.yaml`. No code
changes. (The weekly report needs per-name spots; it reuses `market_price`
from the day's positions JSON for held names instead of extending this
script.)

### 3. `skills/morning-check` — Scheduled Mode and Weekly Mode

The manual flow (P1) is unchanged for interactive use. Two new modes, selected
by the invoking prompt:

**Scheduled Mode (am/pm daily).** Non-interactive discipline: never ask, never
block. Concretely:

1. Resolve the state home; unreadable → notify the error and stop (errors
   always notify).
2. Pull positions via the connector; connector down or unauthorized →
   **degrade**: skip sync, run the sweep on the existing yaml, and the brief
   carries "positions not synced (connector unavailable)".
3. Run `sync_portfolio.py`, then `morning_check.py --format json`.
4. Price-fetch gaps become brief items (P1's ask-the-owner fallback is
   manual-mode only). For held names the connector's `market_price` may be
   written to a `--prices` file first, reducing yfinance dependence.
5. Resolve any `needs_mapping` items (one-time LLM judgment, persisted).
6. **Exception gate.** A name is *flagged* when it has a sync change above
   epsilon or a deterministic finding. Quiet ⇔ no flagged names. Quiet → append
   `YYYY-MM-DD HH:MM am|pm quiet (N names, M gaps)` to `monitoring/log.md`,
   end without notification. Otherwise → judge `llm_todo` for flagged names
   only, write the brief, send exactly one `PushNotification` whose text leads
   with the single most actionable line (≤200 chars).
7. Brief advice is **record-anchored**: each item cites the name's latest
   decision record (trigger group, WFV/scenario, review_by) — "your 2026-06-01
   record says trim at 185; crossed today at 189.2" — never a fresh
   free-floating opinion.

**Weekly Mode (Sunday).** Runs Scheduled Mode's steps 1–5 (pull, sync, sweep)
first, then produces the standing full-portfolio view that daily runs
deliberately don't: every holding and option leg vs its record's
WFV/scenario zones (spots from that pull's positions JSON — Friday closes —
plus live fetch for record-only watchlist names), the **full** `llm_todo`
sweep with citations,
a 14-day calendar (`review_by`, `next_earnings`), the week's sync-drift and
alert summary (from `log.md` + daily briefs), uncovered-account staleness, and
cash as last hand-confirmed. Saved as `monitoring/YYYY-MM-DD-weekly.md`;
notification sent only if the week surfaced act/review items, otherwise the
report is written silently.

**Monthly outcome-scoring task** invokes the existing P2 flow
(`scripts/outcome_score.py` + outcome-scoring skill) and saves its report;
notify only on errors or notable calibration findings.

SKILL.md's "Manual trigger only; scheduling is out of scope" scope line is
replaced by the mode documentation.

### 4. Scheduled task prompts

Four tasks created via the app's scheduler (each prompt fully self-contained:
repo path, state-home resolution, mode, connector usage, notification rules,
read-only guardrail, degrade-on-failure behavior):

| taskId | cron (local) | prompt drives |
| --- | --- | --- |
| `morning-check-am` | `30 8 * * 1-6` | Scheduled Mode, am |
| `morning-check-pm` | `10 16 * * 1-5` | Scheduled Mode, pm |
| `portfolio-weekly` | `0 10 * * 0` | Weekly Mode |
| `outcome-scoring-monthly` | `0 9 1 * *` | P2 scoring run |

`notifyOnCompletion: false` on all four — the skill's own exception-gated
`PushNotification` is the sole notification channel, so quiet runs stay
genuinely silent.

**Rollout order:** create `morning-check-am` ad-hoc (no cron), run it manually
once end-to-end against the real vault, verify the merge/brief/notification,
then attach cron expressions and create the remaining three.

## Contract updates (`decision-records.md`)

- `portfolio.yaml` optional fields formalized: `account` (already in real-world
  use, missing from the contract), `broker_contract_id`, `note`.
- State that `portfolio.yaml` may be machine-written by broker sync; hand
  annotations belong in `note:` fields; `kind`/`combo`/`thesis_record` are
  owner-owned and sync-invariant.
- `monitoring/` layout: `log.md` (one line per quiet run) plus
  `YYYY-MM-DD-{am|pm|weekly}.md` briefs (extends P1's
  `YYYY-MM-DD-morning-check.md` naming for manual runs).

## Testing & CI

- **`tests/test_sync_portfolio.py`** (main pyyaml-only suite, fully offline):
  fixture positions JSON (anonymized copy of the real payload shape) + fixture
  state home. Cases: matched update (qty/avg_cost), fractional quantities,
  deterministic US/ASX mapping, KRX ambiguity → `needs_mapping`,
  adopt-suffix when an existing KR row shares the code, option description
  parsing across date formats (`Jun16'28`, `Aug31'26`), `kind`/`combo`
  preservation on matched legs, short-put default kind, suspected-close only
  within covered accounts, uncovered account untouched and reported,
  `--account` override, resize-epsilon suppression, idempotent re-run,
  `--dry-run` leaves the file byte-identical, atomic write, exit codes.
- **Contract test:** sync's canonical mapping rules ↔ `SYMBOL_PATTERNS`
  lockstep (same discipline as P1's provider-mapping test).
- **Wiring:** register the updated skill surface in `validate_repo.py` and the
  skill-wiring/contract tests; OpenAI metadata parity per repo convention.
- **No new dependency**; `morning_check.py` and its 288-test suite untouched.

## Out of scope (this pass)

- launchd / `claude -p` headless fallback (revisit only if app-open cadence
  proves unreliable in practice).
- Intraday scanning, email/SMS channels, GitHub Actions runners.
- Cash/balances sync (`get_account_balances`) — cash stays hand-confirmed with
  its own dated `note:`.
- FX conversion, multi-portfolio support, live earnings calendar (all
  unchanged from P1).
- Any order placement — permanently out of scope, not just this pass.

## Cost posture

Quiet daily run ≈ one short session: a connector call, two script runs, one
appended log line. Alert days scale with the number of flagged names only.
The weekly report is the standing LLM spend; the monthly job is
script-dominated. No always-on daemon, no per-day full-portfolio LLM pass.

## Verification

1. `python -m unittest discover -s tests -p 'test_*.py' -v` green in the repo
   `.venv` (existing 288 + new sync tests).
2. `python scripts/validate_repo.py --profile full` passes.
3. Offline: `sync_portfolio.py --positions tests/fixtures/<payload>.json
   --home tests/fixtures/<state-home> --dry-run --format json` emits the
   expected diff; then `morning_check.py --offline` over the synced fixture.
4. Real e2e (this machine): ad-hoc `morning-check-am` run → live IBKR pull →
   `portfolio.yaml` reflects reality (spot-check MU 45, CMCSA 3500, BOXX 2955;
   the two new KRX names resolved once and pinned by `broker_contract_id`) →
   brief written → notification received. Immediate re-run is quiet
   (idempotence proof).
5. Attach crons; observe one full AM + PM + Sunday cycle before closing out.
