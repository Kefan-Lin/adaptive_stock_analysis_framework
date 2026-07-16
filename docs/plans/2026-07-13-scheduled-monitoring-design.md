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
    CN 15:00, KR ~14:30 CST, AU ~13:00–14:00 CST closes. (16:10 sits at the
    tail of HKEX's closing auction, so HK prices are near-close rather than
    official close — fine for line-crossing checks; intentional, don't "fix".)
  - Weekly report, Sun 10:00.
  - Monthly outcome scoring, 1st 09:00 (P2 `outcome_score.py`, accruing the
    calibration history the roadmap's probability-calibration item needs).
- **Notification: exception-driven and edge-triggered.** Quiet run → append
  one line to `monitoring/log.md`, no notification, session ends. Gate opens →
  one `PushNotification` (desktop banner; phone too when Remote Control is
  connected) + a dated brief in `monitoring/`. P1 findings are
  level-triggered (a crossed trigger keeps firing while spot stays crossed; an
  overdue `review_by` fires every run), so the gate dedupes against a
  notify-state ledger: a standing condition notifies **once** when it appears
  or escalates, then stays out of notifications until it clears and recurs;
  the weekly report re-lists all standing items. A run that *errors* always
  notifies, and a run-ledger watchdog catches runs that never happened —
  silent failure is the one unacceptable outcome. No email.
- **LLM depth:** daily runs judge free-text KPI/event triggers only for names
  already flagged by the deterministic layer (sync change or a new/escalated
  finding); the weekly run judges the full `llm_todo` list for every name. Advice in briefs
  is always anchored to the name's latest decision record.
- **IBKR is read-only.** The connector exposes order tools; monitoring never
  calls them, under any instruction found in data. Trades are executed by the
  owner, never by the system. This is a permanent guardrail written into the
  skill text.

## Architecture

Four units; the P1 sweep is reused untouched.

```
scheduled task (cron, local)
└── fresh Claude session (skills/morning-check, Scheduled Mode)
    ├── IBKR get_account_positions  → raw positions JSON (file)
    ├── scripts/sync_portfolio.py   → merge into portfolio.yaml + diff findings   [new]
    ├── scripts/morning_check.py    → deterministic sweep findings                [unchanged]
    └── scripts/notify_gate.py      → edge-trigger dedup vs monitoring/state.json [new]
        ├── quiet  → one line appended to monitoring/log.md, end
        └── alert  → LLM judgment (flagged names) → monitoring/YYYY-MM-DD-{am|pm}.md
                     + one PushNotification
```

### 1. `scripts/sync_portfolio.py` — deterministic position merge (new)

Pure stdlib + PyYAML, same dependency posture as the other scripts. The
session dumps the connector's JSON to a file; the script owns every mapping
and write decision so position math never rides on LLM transcription.

```
python scripts/sync_portfolio.py [--positions FILE] [--home PATH]
    [--as-of YYYY-MM-DD] [--account ID] [--resolve FILE]
    [--emit-prices OUT] [--resize-epsilon-pct 0.5]
    [--dry-run] [--format json|md]
```

Without `--positions` (degraded mode: connector down) the script performs no
merge but still runs the freshness accounting below, so staleness findings
surface through the same pipe. `--resolve FILE` feeds `needs_mapping`
resolutions back (below). `--emit-prices OUT` writes a
`{canonical_symbol: market_price}` YAML from the snapshot's **STK rows only**
— option rows are leg prices and must never masquerade as underlying spots —
for `morning_check.py --prices`, so no price ever rides on LLM transcription.

**Input shape** (as returned by `get_account_positions`): `positions[]` of
`{contract_id, contract_description, position, market_price, market_value,
currency, average_price, unrealized_pnl, daily_pnl, asset_class}` with
`asset_class ∈ STK | OPT` (others reported as `needs_mapping`, not guessed).

**Account scoping — the central safety rule.** The live connector returned
only one of the owner's two IBKR accounts (U17780156; U12837156's GOOG/NVDA/HK
rows were absent). The snapshot payload carries no account field, so a naive
full-file merge would mark every other account's holdings as closed — and
symbol-based coverage *inference* has its own hole: a symbol newly bought in
the snapshot's account but already held in the *other* account would match the
wrong account's row, overwrite its lot, and cascade that account into false
closes. Rules:

- **Pinned account is the primary mechanism.** Each scheduled-task prompt pins
  `--account ID` (established once during rollout via `get_account_summary` /
  connector probing). All matching, updating, and close-inference happen
  strictly inside the pinned account; rows in other accounts are never
  matched, updated, or closed.
- **Inference is a non-destructive fallback** for manual runs without
  `--account`: an account counts as covered only when a **majority** of
  snapshot rows map into it (quorum), and even then suspected closes are
  *reported only*, never applied. Ambiguity → report, no write.
- **Empty/implausible snapshot guard:** a snapshot with zero positions (or
  zero matches) against a pinned account that has rows is treated as a
  probable connector fault → degraded mode (no merge, staleness accounting
  only), not a mass close.
- Uncovered accounts are untouched and reported with their own data age from
  the per-account freshness block (below), so the brief can say "U12837156
  not covered — last synced 2026-07-05".
- A new snapshot position joins the pinned account. The same symbol held in
  two accounts is matched within the pinned account only.

**Per-account freshness.** A top-level `accounts:` block records
`{ID: {last_synced: date}}`, updated on every successful merge for the pinned
account. The script emits a `sync_staleness` finding (`urgency: review`) for
any account whose `last_synced` is older than `--staleness-days` (default 3),
including in degraded mode — so a connector broken for days opens the gate
instead of degrading silently forever. This block is what makes the
`uncovered_accounts` report implementable at all: the single top-level
`as_of` says nothing about *which* account's data is stale.

**Identity and symbol mapping.** Matching precedence per snapshot row:

1. `broker_contract_id` exact match (new optional field on holdings and
   option_legs rows; written back on first successful mapping so subsequent
   runs are exact).
2. Deterministic description mapping to canonical form: bare ticker → US
   (`MU`); `X @ASX` → `X.AX`; `NNNNNN @KRX` → `.KS`/`.KQ` is ambiguous — adopt
   the suffix of an existing row with the same 6-digit code, else
   `needs_mapping`; `@SEHK` → zero-padded `.HK` (assumed, not yet observed —
   no HK rows appeared in the live payload; verify during rollout). Rules live
   in the script and stay in lockstep with `SYMBOL_PATTERNS` (same
   contract-test discipline as P1's provider mapping).
3. Anything unresolved → a `needs_mapping` item. The scheduled session (LLM)
   resolves it once — e.g. `011790 @KRX` → `011790.KS` — writes the
   resolutions to a `{contract_id: canonical_symbol}` file, and **re-runs the
   script with `--resolve FILE`**; the script does the write and persists
   `broker_contract_id`, so it never recurs and the new rows are merged and
   swept the same day. The LLM never edits `portfolio.yaml` by hand. A
   disappeared row plus a similar new row (the observed EOSE → EOSER case) is
   reported as a suspected corporate action for confirmation, not auto-merged.
4. **Currency guard:** a matched row whose `currency` differs from the
   snapshot's → `needs_mapping`, never an update in the wrong currency.
5. **Contract-level matching for legs:** the broker nets per contract; the
   yaml may legitimately split one contract across rows (combo leg +
   standalone). Compare the snapshot qty against the **sum** of matching rows:
   single row → direct update; multiple rows whose sum matches → no change;
   multiple rows with a sum mismatch → `needs_mapping` (allocation across
   combos is the owner's call), never an auto-update.

**Option parsing.** `MSFT Jun16'28 450 CALL @AMEX` →
`{underlying: MSFT, expiry: 2028-06-16, strike: 450, right: CALL}`; qty sign +
right → default `kind` (`long-call`/`short-put`/…), multiplier 100 unless the
description says otherwise. **Premium units:** the payload's `average_price`
for OPT rows is per-share (observed: MSFT leg 69.809 vs the yaml's
`premium: 69.81`) — the unit rule is pinned by a normalization test, and
rollout spot-checks one leg, because a per-contract misread corrupts every
premium by 100×. `premium` is written on row creation and updated only where
the field already exists; legs the owner deliberately keeps premium-less
(combo rows carrying a net-debit `note:` instead) are never given one.

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
option_leg_closed | option_leg_resized | sync_staleness`. New/closed →
`urgency: review`; resized → `watch`. Resizes below `--resize-epsilon-pct`
(default 0.5%, for DRIP/fractional noise) are logged in the JSON but do not
open the exception gate. A `position_new` with no decision record additionally
surfaces through P1's existing "held but no record on file" gap after the
merge — the brief shows both "new today" and "no thesis on file".

**Close semantics — report, quarantine, confirm.** A pinned-account row
absent from the snapshot is **moved** to a top-level `suspected_closed:`
section (the full row plus `suspected_closed_on:` date), not deleted and not
left in place. Moving it out of `holdings`/`option_legs` means the unchanged
P1 sweep stops treating it as held (its decision record still surfaces via the
watchlist path, which is correct for a sold name), the second run sees no
difference (idempotence holds), and the gate fires exactly once via the
notify-state ledger. Physical deletion happens only on owner confirmation —
the weekly report lists pending `suspected_closed` entries until the owner
confirms (delete) or restores (moves the row back, e.g. after a connector
fault). This is deliberately the *only* destructive-adjacent path, and it is
two-phase.

**Write discipline.** Atomic write (tmp + rename), stable field order, bumps
top-level `as_of` to the sync date on any write (an *intraday* no-change re-run
leaves the file untouched, `as_of` included; a new-day sync always writes,
though, because the pinned account's `last_synced` advances on each successful
merge — deliberate, so staleness accounting stays honest and quiet days still
produce a daily "monitor-alive" audit commit, notifications remaining separately
gated),
idempotent (re-running on the same snapshot yields zero changes), `--dry-run`
for tests and manual inspection, exit codes mirror P1 (`0` clean with or
without changes, `2` environment error). **`portfolio.yaml` becomes a
machine-written file:** PyYAML round-trips do not preserve hand comments, so
during implementation the current comments (cash provenance, account
groupings, combo notes) are promoted once into structured `note:` fields —
`cash` is a currency→amount map, so its provenance note goes in a sibling
top-level `note:`, not inside the map — and the contract doc states that
future annotations belong in `note:` fields, not comments. Three guards
around the write:

- **Comment guard:** if the pre-image contains `#` comment lines, the script
  refuses to write and reports it (a slip back into the comment habit must
  not be silently eaten).
- **Post-write validation:** every write is followed by a
  `validate_records.py` pass over the state home (runtime and in tests) so a
  malformed machine write is caught before P1 consumes it.
- **Vault auto-commit:** the state home is git-backed; the session commits
  after every sync write (`sync: <summary>`), making each merge a reviewable,
  revertible diff.

### 2. `scripts/morning_check.py` — unchanged

The P1 sweep runs as-is against the freshly-synced `portfolio.yaml`. No code
changes. (The weekly report needs per-name spots; it reuses `market_price`
from the day's positions JSON for held names instead of extending this
script.)

### 3. `scripts/notify_gate.py` — edge-trigger dedup (new)

P1 findings are level-triggered; naive gating would push the same standing
condition twice a day until the owner mutes notifications. This small script
(stdlib + PyYAML) owns the run-over-run state so dedup never rides on LLM
memory:

```
python scripts/notify_gate.py --findings FILE --changes FILE
    [--state FILE] [--run-id "YYYY-MM-DD am"] [--max-gap-hours 36]
    [--format json]
```

- **Stable finding keys:** `price_trigger` → symbol+trigger_group+level;
  `drawdown` → symbol; `review_expiry` → symbol+review_by date;
  `earnings_proximity` → symbol+next_earnings date; `options_assignment` →
  underlying+strike+expiry; `sync_staleness` → account. Sync diff changes are
  inherently edge-triggered (diff vs the file) and always pass through.
- **Decision:** a finding notifies when its key is new or its urgency
  escalated vs `monitoring/state.json`; standing keys are suppressed; keys
  absent from the current run are dropped from state, so a condition that
  clears and later recurs notifies again.
- **Output:** `{notify, new, escalated, standing, cleared, missed_gap_hours}` —
  the skill notifies iff `notify` is true, and the brief may list `standing`
  for context without re-pushing it.
- **Run-ledger watchdog:** state records each run's timestamp; a gap larger
  than `--max-gap-hours` (default 36 — wider than the widest normal
  weekend/weekly gap) reports `missed_gap_hours` (the elapsed gap in hours,
  else null), which always notifies. This is
  a catch-up alert on the next successful run (missed tasks also fire on next
  app launch); true same-instant death of a session cannot alert itself.

### 4. `skills/morning-check` — Scheduled Mode and Weekly Mode

The manual flow (P1) is unchanged for interactive use. Two new modes, selected
by the invoking prompt:

**Scheduled Mode (am/pm daily).** Non-interactive discipline: never ask, never
block. Concretely:

1. Resolve the state home; unreadable → notify the error and stop (errors the
   session can see always notify). If the previous run's log line is younger
   than 30 minutes (a late-fired missed task overlapping the next slot), log
   `skipped (overlap)` and end.
2. Pull positions via the connector; connector down or unauthorized →
   **degraded mode**: run `sync_portfolio.py` *without* `--positions` (no
   merge, freshness accounting still emits `sync_staleness` findings) and the
   brief carries "positions not synced (connector unavailable)".
3. Run `sync_portfolio.py --positions <dump> --account <pinned>
   --emit-prices <spots>`, then `morning_check.py --prices <spots>
   --format json` (option-underlying spots not in the STK rows still come from
   live fetch).
4. Price-fetch gaps become brief items (P1's ask-the-owner fallback is
   manual-mode only).
5. Resolve any `needs_mapping` items (one-time LLM judgment), write the
   resolutions file, **re-run** `sync_portfolio.py --resolve` and then the
   sweep, so resolved names are merged and checked the same day.
6. **Exception gate = `notify_gate.py`.** Quiet ⇔ `notify: false`. Quiet →
   append `YYYY-MM-DD HH:MM am|pm quiet (N names, M gaps)` to
   `monitoring/log.md`, end without notification. Otherwise → judge `llm_todo`
   for flagged names only (a name is *flagged* when it has a sync change above
   epsilon or a `new`/`escalated` finding), write the brief (header stamps the
   **actual** run time — a late-fired task carries midday prices), send
   exactly one `PushNotification` whose text leads with the single most
   actionable line (≤200 chars).
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
a 14-day calendar (`review_by`, `next_earnings`), all **standing** findings
from the notify-state ledger (the ones daily runs deliberately stopped
re-pushing), pending `suspected_closed` confirmations, the week's
sync-drift / alert / missed-run summary (from `log.md` + daily briefs),
uncovered-account staleness, and cash as last hand-confirmed. Saved as
`monitoring/YYYY-MM-DD-weekly.md`; notification sent only if the week
surfaced act/review items, otherwise the report is written silently.

**Monthly outcome-scoring task** invokes the existing P2 flow
(`scripts/outcome_score.py` + outcome-scoring skill) and saves its report;
notify only on errors or notable calibration findings.

SKILL.md's "Manual trigger only; scheduling is out of scope" line is replaced
by the mode documentation **in both places it appears** — the frontmatter
`description:` (which drives skill routing) and the Scope section.

### 5. Scheduled task prompts

Four tasks created via the app's scheduler. Each prompt is fully
self-contained (a fresh session sees none of this design): repo path **and
the repo `.venv` interpreter path** (the global Python is known-broken), the
pinned IBKR account ID, state-home resolution, mode, connector usage,
notification rules, read-only guardrail, degrade-on-failure behavior. The
implementation plan drafts all four prompts **verbatim** — they are the real
production interface, not an afterthought. Task setup also **pre-authorizes
the session's tool permissions** (connector read tools, the scripts, writes
under the state home) — a scheduled session that stalls on a permission
prompt with nobody watching is a silent death, the failure mode this design
forbids:

| taskId | cron (local) | prompt drives |
| --- | --- | --- |
| `morning-check-am` | `30 8 * * 1-6` | Scheduled Mode, am |
| `morning-check-pm` | `10 16 * * 1-5` | Scheduled Mode, pm |
| `portfolio-weekly` | `0 10 * * 0` | Weekly Mode |
| `outcome-scoring-monthly` | `0 9 1 * *` | P2 scoring run |

`notifyOnCompletion: false` on all four — the skill's own exception-gated
`PushNotification` is the sole notification channel, so quiet runs stay
genuinely silent.

**Rollout order:** (1) **account probe first** — establish what
`get_account_summary` identifies, whether positions can be enumerated per
account, and whether `get_account_positions` ever returns a merged view; pin
the account ID(s) from the answer. If U12837156 is permanently unreachable,
document in the contract that its rows stay hand-maintained. (2) Create
`morning-check-am` ad-hoc (no cron), run it manually once end-to-end against
the real vault; verify the merge, brief, and notification, that one option
leg's premium landed per-share (the 100× check), and that the run hit **zero
permission prompts**. (3) Attach cron expressions and create the remaining
three.

## Contract updates (`decision-records.md`)

- `portfolio.yaml` optional fields formalized: `account` (already in real-world
  use, missing from the contract), `broker_contract_id`, `note`.
- New top-level sections: `accounts:` (per-account `last_synced` freshness —
  the single `as_of` cannot express which account is stale) and
  `suspected_closed:` (two-phase close quarantine; excluded from the P1
  sweep's held universe by construction).
- State that `portfolio.yaml` may be machine-written by broker sync; hand
  annotations belong in `note:` fields (cash provenance in a sibling
  top-level `note:`, since `cash` is a currency→amount map);
  `kind`/`combo`/`thesis_record` are owner-owned and sync-invariant.
- `monitoring/` layout: `log.md` (one line per run), `state.json` (notify
  ledger + run timestamps), plus `YYYY-MM-DD-{am|pm|weekly}.md` briefs
  (extends P1's `YYYY-MM-DD-morning-check.md` naming for manual runs).

## Testing & CI

- **`tests/test_sync_portfolio.py`** (main pyyaml-only suite, fully offline):
  fixture positions JSON (anonymized copy of the real payload shape) + fixture
  state home. Cases: matched update (qty/avg_cost), fractional quantities,
  deterministic US/ASX mapping, KRX ambiguity → `needs_mapping`,
  adopt-suffix when an existing KR row shares the code, option description
  parsing across date formats (`Jun16'28`, `Aug31'26`), OPT premium
  unit normalization (the 100× guard), premium only-if-present update rule,
  `kind`/`combo` preservation on matched legs, short-put default kind,
  suspected-close moves the row to `suspected_closed:` (two-phase, only
  within the pinned account), cross-account symbol collision does NOT touch
  the other account's row (the GOOG scenario), all-positions-sold pinned
  account closes cleanly, empty-snapshot guard degrades instead of
  mass-closing, uncovered account untouched and reported, inference-quorum
  fallback is report-only, currency-mismatch → `needs_mapping`, multi-row
  contract sum matching (`needs_mapping` on mismatch), `--resolve` round-trip
  persists `broker_contract_id`, `--emit-prices` contains STK rows only,
  comment guard refuses to write, resize-epsilon suppression,
  `sync_staleness` in degraded mode, idempotent re-run, `--dry-run` leaves
  the file byte-identical, atomic write, post-write `validate_records.py`
  pass, exit codes.
- **`tests/test_notify_gate.py`** (offline): new finding fires, standing
  suppressed, urgency escalation fires, cleared-then-recrossed re-fires, sync
  changes always pass, `sync_staleness` dedupes like any standing key,
  missed-run watchdog over the run-timestamp ledger, state round-trip.
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
4. Real e2e (this machine), after the rollout account probe: ad-hoc
   `morning-check-am` run → live IBKR pull → `portfolio.yaml` reflects
   reality (spot-check MU 45, CMCSA 3500, BOXX 2955; the two new KRX names
   resolved once and pinned by `broker_contract_id`; the MSFT leg's premium
   is per-share ≈69.8, not ≈6980) → brief written → notification received →
   zero permission prompts. Immediate re-run is quiet (dedup + idempotence
   proof).
5. Attach crons; observe one full AM + PM + Sunday cycle before closing out.
