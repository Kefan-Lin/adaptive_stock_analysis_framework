# Web App — Read-Only Projection Layer — Design

Status: design (all decisions user-approved 2026-08-10/11; this document converges
the local wayfinder map + two prototype rounds into the repo)
Depends on: P0 decision-records layer (`scripts/validate_records.py` loaders,
record/INDEX contract), P1 price plumbing (`scripts/morning_check.py`
provider mapping and lazy-import pattern), P2 scoring
(`scripts/outcome_score.py` used as a library).
Defers: calibration/review view and morning alert strip (v1.1, data already in
the contract); everything in Out of scope.

## Problem

The framework now has structured longitudinal state — per-symbol decision
records with `stance` / `valuation_zone` / `weighted_fair_value` / `scenarios`
/ `triggers` / `review_by`, an `INDEX.md` chain per symbol, `portfolio.yaml`,
and P2 outcome scores — but reading it means running scripts and opening YAML.
Two questions the flat files answer worst:

1. **"What is in each valuation zone right now?"** — a cross-symbol snapshot.
2. **"How did this thesis evolve, and did price walk into the bands we drew?"**
   — the per-symbol longitudinal view, which is precisely what a directory of
   markdown files cannot show.

v1 is a **read-only projection layer** that answers exactly these two
questions: a Zone Board index page and a per-symbol Thesis Timeline page,
generated as a static site from the private vault. The vault stays the only
source of truth; the app writes nothing.

Two build forms share one pipeline:

- **Private build** — real vault data, opened locally via `file://`, zero
  network in the browser.
- **Sanitized demo build** — fictional + non-position data, deployed to GitHub
  Pages from this public repo (the resume/interview payoff; may land after the
  private build).

## Provenance

Decisions were made in a local wayfinder map (untracked `.scratch/`, private)
across nine tickets: go/no-go + guardrails (01), price-data research (02),
stack survey (03), data contract (04), architecture/deployment (05), Zone
Board prototype (06), Thesis Timeline prototype (07), and two parked v1.1
stubs (08, 09). Tickets 06/07 were interactive HTML prototypes built against
the **real vault** and iterated with the user across two rounds; every open
question below is closed with a user verdict dated 2026-08-10 or 2026-08-11.

The two prototype directories (single-file HTML + export/build scripts +
screenshots) are **retained** locally under `.scratch/stock-analysis-web-app/prototypes/`
as the visual/behavioral reference for implementation and for later
comparison — they contain real positions and full report texts and must never
enter this public repo.

## Scope & guardrails (locked, ticket 01)

- Read-only projection: vault is the sole source of truth; zero write-back.
- Two forms: private local dashboard + public sanitized demo.
- Size: a 1–2 week projection layer. Anything growing past that gets cut.
- Out of scope, permanently for this map: broker/position auto-sync, scheduled
  or hosted monitoring (both explicitly rejected 2026-08-03), multi-user /
  SaaS / auth, trade execution, and any v1 in-app editing of records. If
  write-back is ever wanted, that is a new map.

## Architecture decisions (locked, ticket 05)

1. **Static generation.** Export script reads the vault → JSON snapshot →
   static site. Private and demo are the same pipeline with different
   datasets. Refresh cadence = manual re-run, same rhythm as the manual
   morning check.
2. **Frontend stack: Python-generated static HTML + inlined ECharts.** No
   node, no framework, no build chain beyond the repo's Python. This repo
   already generates HTML from Python; v1 is only two views, so hand-built
   HTML stays maintainable at this scale. The frozen JSON contract is the
   asset — if the app outgrows this, swapping renderers is cheap.
3. **Private instance = output directory + `file://` double-click.**
   `webapp_out/` (gitignored): `index.html` + one page per symbol + shared
   assets. Data is inlined into each page (`file://` blocks `fetch` but not
   relative `<script src>`). Zero servers, zero listeners.
4. **Demo deployment = GitHub Pages, this repo.** `actions/deploy-pages`
   artifact flow, manual dispatch / push trigger, **no cron**. Privacy rails:
   the private output dir is gitignored by default; the demo build requires an
   explicitly different dataset path and command — the two builds never share
   default arguments.
5. **Prices = export-time snapshot + local incremental cache + zero network in
   the frontend.** The cache only appends tail bars; upstream failure falls
   back to cache and marks the series **stale**; `as_of` is tracked per symbol
   (five markets, five calendars). FX (Frankfurter) is snapshotted at export
   time too — when viewing, not a byte leaves the machine. Demo prices are
   frozen with the demo dataset.
6. **Adjustment basis: full split-factor correction to the current share
   basis** (splits only, no dividend adjustment), uniform across markets:
   yfinance `auto_adjust=False` Close for US/HK/KR/AU/JP (natively that
   basis); CN via eastmoney `fqt=0` + self-computed split/bonus factors
   (`fqt=1` includes dividends — banned). Historical record numbers
   (`scenarios`, `weighted_fair_value`, price triggers, `price_at_decision`)
   are converted by the **Python side** using the cumulative split factor from
   record date → today, and the factor is exported alongside for audit. A
   missing/suspect factor degrades to an explicit warning, never a silent
   wrong number. The snapshot schema carries `price_basis: current share
   basis (split-adjusted, ex-dividend)`.

Rationale trail (tickets 02/03, condensed): browser-side price fetching has
hard coverage gaps (no free+CORS source for KR/AU; Yahoo chart API has no CORS
and its ToS bars automated collection), so prices must come through the
existing Python provider stack at export time. Both yfinance and akshare have
documented intermittent-failure history → `as_of` + retry + stale flagging are
mandatory, not nice-to-have. Static-hosting-friendly stacks were surveyed;
zero-node strictness leaves Python-generated static HTML (repo precedent) as
the fit.

## Data contract: `web-export/v1` (locked, ticket 04 + prototype patches)

### Core decisions

1. **Zone semantics = recorded value + mechanical signals.** Grouping uses the
   latest record's `valuation_zone` **as recorded**, labeled with its decision
   date — the machine never re-derives a zone (zones are judgment calls per
   the workflow; `Invalidation` is "thesis break, not price alone"). What the
   Python side *does* compute and export, per card:
   - **cursor** — current price's position on the bear—WFV—bull scale:
     `(price − bear) / (bull − bear)`, may exceed [0,1];
   - **discount** — `price / weighted_fair_value − 1` (the sort key,
     ascending: deepest discount first);
   - **trigger touches** — price-type `add_on` / `trim_exit` levels crossed at
     the current price;
   - **scenario breach** — price below bear or above bull;
   - **stale** — `review_by` overdue, with day count;
   - **drawdown** — current price vs `price_at_decision`;
   - **earnings proximity** — days to `next_earnings` when in the future;
   - **no-price** — an explicit state (see patches).
   The frontend renders; it contains **zero judgment logic**.
2. **Field range = full passthrough + a consumption checklist.** Every
   `decision-record/v1` frontmatter field is exported as-is (including
   `action_taken` — the timeline event pins — and `scenario_probabilities`).
   Record body markdown is exported in full (**private build only**). The
   contract document lists which fields the frontend actually consumes;
   the frontend must not depend on anything outside that list.
3. **P1/P2 ride along.** Derivable monitoring signals (drawdown, stale,
   earnings, put-assignment proximity) plus the full P2 `outcome_score`
   output (direction hit / WFV convergence / scenario landing / trigger touch
   at 90/180/365d) are in v1. Unmatured horizons are `null`/pending — the
   contract explicitly allows partial scores. `outcome_score` is imported as a
   library by the exporter; `morning_check` the *script* is not in the
   pipeline.
4. **`portfolio.yaml` passes through in full; the UI consumes exactly three
   badges:** held (qty > 0), option legs present, and put-assignment-nearing
   (short-put moneyness `price/strike < 1.05` **and** ≤ 45 days to expiry —
   Python-derived). No P&L or portfolio-level views in v1: the board is a
   *valuation-position* surface and must not drift into a P&L surface. The
   demo gets a fictional `portfolio.yaml`.
5. **Versioning.** Export top level carries `schema: web-export/v1`. Additive
   changes don't bump; breaking changes bump to v2; the generator refuses
   caches/datasets whose schema doesn't match.
6. **Thesis chain = what the vault already encodes.** Per-symbol records
   sorted by `(date, mode-priority)`; the record↔INDEX row bijection is
   already enforced by `validate_records.py`; `historical` INDEX rows become
   **ghost** pre-history nodes; `related_symbols` renders as see-also. **No
   `supersedes` relation is introduced** — the projection layer has no
   authority to push schema back into the vault (that would make the
   projection a second source of truth by the back door).

### Amendment made by prototyping (supersedes the initial 04 call)

- **Referenced session reports ARE exported in v1** (private build). Ticket 04
  initially excluded `source_report` targets ("additive, can add back");
  ticket 07's report drawer exercised that additive path immediately: every
  report referenced by a record or ghost row is rendered to HTML at export
  time and shipped in the page payload, with block anchors for navigation.
  Demo builds ship fictional reports only.

### Contract patches exposed by real-data prototyping

These were discovered by running the prototypes against the real vault and are
**part of the v1 contract**, not future work:

1. **`valuation_zone` has a fifth real value: `Missing Inputs`.** Several live
   records carry it; the four-value enum in the original vocabulary is
   incomplete. Contract: the exporter passes it through; the UI gives it a
   dedicated narrow board column, styled neutral gray + secondary encoding
   (dashed), *outside* the four-color zone palette. **Upstream patch
   required:** add `Missing Inputs` to `VALUATION_ZONES` in
   `scripts/validate_records.py` (additive vocabulary change; today those real
   records would fail validation — the validator is behind vault reality) and
   sync the vocabulary contract tests / taxonomy references.
2. **`market` includes `JP` in real data.** The `SYMBOL_PATTERNS` map
   (US/HK/CN/KR/AU) is incomplete. **Upstream patch required:** add
   `JP: ^\d{4}\.T$` to `SYMBOL_PATTERNS` and to the provider mapping
   (yfinance serves `.T` natively). The exporter must otherwise treat market
   as an open set — unknown markets degrade gracefully, never crash.
3. **"No price" is a first-class state.** One real symbol is unfetchable
   (delisted per the provider). Cards render with a no-price chip, no cursor,
   no discount, sorted to the column tail; the exporter records the reason.
4. **Extreme discounts exist (> +400% observed).** Every linear scale (micro
   ruler, any axis) must clamp, with out-of-range values pinned at the edge
   with an arrow affordance.
5. **Option/put badge logic is implemented but unverified against real data**
   (`option_legs` was empty at prototype time). Keep the logic and the
   fixtures-based tests; flag it as untested-in-production in the contract
   notes.
6. **Basket reports don't get sliced.** Multi-symbol ("basket") reports are
   exported **whole**; each symbol's page opens the full report and
   auto-jumps to that symbol's `Part` via anchor matching (match symbol or
   company name against level-1 blocks, **excluding the first
   document-title block** — document h1 titles often contain the symbol and
   would false-match; reports with no Part structure land at the top).
   Per-symbol slicing was rejected as brittle (depends on a `# Part` heading
   convention).
7. **P2 is all-pending at launch.** Every real record is younger than 90 days
   until ~2026-10; the timeline's score chips will read "未到期 + maturity
   date" for the first months. This is the honest state and the UI is
   designed for it (see Thesis Timeline). A deterministic **simulated-maturity
   preview** (reusing `outcome_score`'s real formulas; 90d = latest close,
   180/365d drift toward base) exists behind a masthead toggle with a global
   amber warning strip and hatched/amber-tagged chips so it can never be
   mistaken for real scores. Private build only.
8. **`action_taken` has one real sample** (a single `exited`). The rendering
   for the rest of the action vocabulary (bought/added/reduced/sold-put/
   put-assigned/put-closed) is implemented against fixtures only; same
   flagging as patch 5.
9. **Same-day double records are real** (event-review + position-review on
   one date). The band segment is attributed by mode priority
   (position-review wins — matches `MODE_PRIORITY`); both markers render on
   that date; the tooltip shows both records side by side.
10. **Ghost pre-history is thick** (up to ~10 `historical` INDEX rows per
    symbol, including sector-context rows). Ghost nodes are part of the rail,
    and their linked reports render in the drawer like any other.
11. **Payload reality:** a deep-chain symbol page with all referenced reports
    + inlined ECharts lands ≈ 0.3–0.8 MB — acceptable. Demo dataset must
    keep fictional report volume in check.

### Payload shape (sketch)

Top level (per dataset):

```json
{
  "schema": "web-export/v1",
  "generated_at": "…", "price_basis": "current share basis (split-adjusted, ex-dividend)",
  "fx": {"base": "USD", "rates": {"…": 0.0}, "as_of": "…"},
  "board": {"cards": [ { "symbol": "…", "market": "…", "currency": "…",
      "record_date": "…", "mode": "…", "stance": "…", "confidence": "…",
      "position_size": "…", "valuation_zone": "…",
      "wfv": 0, "bear": 0, "base": 0, "bull": 0,
      "price": 0, "price_as_of": "…", "price_stale": false, "no_price_reason": null,
      "price_at_decision": 0, "split_factor": 1,
      "cursor": 0.0, "discount": 0.0,
      "triggers_touched": [], "scenario_breach": null,
      "stale_days": 0, "review_by": "…", "earnings_in": null,
      "drawdown": 0.0,
      "held": false, "qty": null, "avg_cost": null,
      "option_legs": 0, "put_assignment_risk": false } ]},
  "symbols": { "SYM": {
      "price": {"dates": [], "closes": [], "as_of": "…", "splits": [], "stale": false},
      "records": [ { "…": "full frontmatter passthrough", "adj": {"…": "split-adjusted numbers"},
          "summary": "first sentence", "delta": {"stance": [null, "…"], "wfv": [], "zone": [], "confidence": []},
          "body_html": "…", "report_path": null,
          "outcome": {"windows": {}, "pending": [], "gaps": []},
          "sim_outcome": {} } ],
      "ghosts": [ {"date": "…", "mode": "…", "reports": []} ],
      "actions": [ {"date": "…", "action": "…", "instrument": "…", "note": "…"} ],
      "held": false, "qty": null, "avg_cost": null } },
  "reports": { "<id>": {"title": "…", "html": "…", "blocks": [{"id": "blk-0", "level": 1, "title": "…"}]} }
}
```

(Field names follow the prototypes; the implementation plan freezes the exact
consumption checklist as a contract test.)

## View 1 — Zone Board (index page)

**Winning variant: columnar kanban** (user verdict 2026-08-10; aligned-ruler
ledger and scatter variants rejected — the ledger's full-page aligned-ruler
scan may return as an optional list view someday, not in v1).

- **Layout:** 4+1 vertical zone columns — Accumulation / Hold / Exhaustion /
  Invalidation + a narrow Missing Inputs column. Within a column, cards sort
  by discount ascending (deepest discount first). Zone header shows the
  recorded-value framing (zone = judgment at record date, never renamed).
- **Card elements (all locked):**
  - ticker + market tag + the three badges (held / option legs / put-nearing);
  - current price in native currency, compact numerals for large-denomination
    currencies (e.g. `160k` / `2.27M` for KRW);
  - **micro ruler**: bear—◆WFV—bull with the price cursor as an ink dot, WFV
    as a diamond, compact end numerals; out-of-range cursor pins at the edge
    as a colored triangle; records without scenarios render a dashed
    placeholder ruler;
  - discount percentage;
  - stance · confidence · record date;
  - mechanical signal chips: trigger touched / scenario breach / stale
    (overdue days) / earnings-soon / no-price.
- **Stale styling:** dark-paper background + dashed border — visually recessed
  but present.
- **Navigation:** each card links to its symbol's Thesis Timeline page.

## View 2 — Thesis Timeline (per-symbol page)

**Winning variant: two-pane ledger ("双栏账房")** (user verdict 2026-08-10;
dossier-scroll and chart-stage variants rejected).

- **Layout:** left 58% sticky chart + selected-node detail panel; right 42%
  chain rail (new → old, worklog style). Chart and chain always share the
  viewport. Clicking a rail row selects it; the full report slides in as a
  right-side full-height drawer (block nav + body).
- **Chart:**
  - price close line (ink solid) over a **stepped scenario band**: from each
    record's date, bear/base/bull draw a band segment colored by that record's
    zone (half-transparent fill + deepened stroke); same-day double records
    attribute the segment by mode priority;
  - reference lines with a **three-channel line-style hierarchy** (rhythm ×
    weight × color, validated in the worst real case where base / cost / WFV
    sit within ~8% of each other):
    - WFV = anchor: ink 2px long dash `[9,4]`;
    - base = background tick: gray 1px micro-dot `[1,3]`;
    - holding cost = amber 1.2px dash-dot `[6,3,1.5,3]`;
  - **point-value paper labels:** the latest segment's bear/base/bull/WFV four
    values sit permanently in a 96px right-edge gutter, following the band
    under zoom; the selected/hovered segment's four values pin at that
    segment's start; near values de-collide with a minimum spacing of 8.5% of
    band height in value space; label identity is carried by text and ink
    color (WFV bold), zone color only as a 55% border tint;
  - node markers on the price line: shape = mode (● position-review,
    ◆ event-review, ▬ existing-report, 📍 new-idea, ○ ghost/historical,
    ▼ action), color = zone;
  - default zoom window = 30 days before the first event → `as_of` + 14 days
    (the band extends slightly into the future to read "still in force");
    dataZoom exposes the full 5y;
  - tooltip = date / close / the then-active band values (bear/base/bull/WFV/
    zone/discount) — directly answering "did price walk into the bands".
- **Linkage (in v1, bidirectional):** hover/select a rail row ↔ highlight the
  matching band segment + show its point labels; click a chart marker →
  scroll to and select the rail row.
- **Chain rail rows:** date + mode + stance/zone/WFV/confidence deltas (amber
  delta blocks) + one-line summary + P2 chips + held dot; ghost rows and
  action rows (▼, e.g. `exited`) interleave chronologically.
- **P2 score display (in v1, two layers):**
  - rail chips with Chinese semantics — matured: `90d ✗未中 -2.5%（落
    bear–base 间）`; pending: `90d · 10-27 到期`;
  - selected-node panel: a **P2 复盘明细** table — columns: window-end close /
    absolute return / direction hit (noting it is judged against stance) /
    scenario landing / WFV gap closed (noting convergence ratio toward WFV);
    unmatured rows read `未到期 —— YYYY-MM-DD 出分`; simulated rows carry an
    amber tag + hatching.
- **Report drawer:** rendered-at-export HTML; left sticky block navigation
  built from numbered anchors (`blk-N` — CJK headings can't slugify, so
  sequential anchors; h1 bold as Part dividers, h2 indented); basket reports
  open whole and auto-jump to this symbol's Part (see contract patch 6).
- **Legend panel:** a `☰ 图例` button on the chart legend row opens a fixed
  overlay with four sections covering every meaningful glyph: node markers
  (shape = event type, color = zone, pinned at decision price vs close),
  lines & bands (close/WFV/base/cost/scenario band/point papers), the five
  zone colors (Missing Inputs dashed gray included), and rail symbols (delta
  blocks, the four P2 chip states, held dot). Esc / click-outside closes.

## Shared visual system

- Warm-paper "private ledger broadsheet": Didot-style masthead, Menlo tabular
  numerals, system fonts only (zero font downloads).
- Zone palette `#2e7d4c / #3f6bb5 / #a97b00 / #c0304f`
  (Accumulation/Hold/Exhaustion/Invalidation) — passed the dataviz validator
  (CVD / contrast / chroma) on both paper surfaces (`#f6f2e8`, `#fdfbf5`).
  `Missing Inputs` gray `#86795a` stays **out** of the categorical palette;
  it is encoded neutral + dashed.
- Line families are distinguished by line *style* on a single ink family, not
  by hue.
- UI language: Chinese framework copy + English contract enums verbatim (zone
  names get small Chinese glosses).
- CJK typography in report bodies: serif (Songti/Iowan) at 1.85 line-height;
  tables at 11px UI font + `tabular-nums`, wrapped in horizontal-scroll
  containers; inline code in Menlo with a paper-tint background.

## Export & build pipeline

Two-stage, with the JSON snapshot as the contract seam:

1. **`scripts/export_web.py`** — vault → `web-export/v1` JSON dataset.
   - Reuses existing loaders/helpers instead of re-implementing:
     `validate_records.py` (frontmatter parsing, `resolve_home`,
     `MODE_PRIORITY`, INDEX parsing), `morning_check.py` (`provider_for`
     routing, lazy-import pattern), `outcome_score.py` (`score_record` and
     its scoring primitives — promoted to public names by the implementation
     plan, `PriceHistory` seam).
   - One addition on top of `provider_for`: an export-side
     `provider_symbol()` normalization for the yfinance path (US share-class
     dots → dashes, HK five-digit codes → four-digit). P1/P2 currently pass
     canonical symbols to yfinance raw; unifying them on this map is a
     follow-up upstream patch (same additive pattern as contract patches
     1–2), not part of v1.
   - Fetches 5y daily history per symbol through the provider stack with the
     **local incremental cache** (append-tail; stale fallback + per-symbol
     `as_of`); computes split factors and adjusts record numbers; snapshots
     FX.
   - Renders record bodies and referenced reports to HTML export-side using
     the `markdown` library (tables + fenced_code extensions), injecting
     `blk-N` anchors. `markdown` joins yfinance/akshare as a lazily-imported
     export-path dependency — the pyyaml-only main CI job stays clean (the
     prototype's `--target` install was a prototype expedient; the real
     dependency lands in `pyproject.toml` alongside the other extras).
   - CLI (mirrors repo conventions): `--home PATH`, `--out FILE`,
     `--dataset private|demo` semantics via explicit paths, `--offline`,
     `--as-of` for deterministic tests.
2. **`scripts/build_webapp.py`** — JSON dataset → static site in an output
   directory (default `webapp_out/`, gitignored).
   - Generates `index.html` (Zone Board) + one page per symbol (Thesis
     Timeline), inlining the per-page data slice and shared CSS.
   - ECharts (pinned 5.6.0, Apache-2.0) is vendored in the repo and inlined
     into pages at build time — deterministic offline builds, zero CDN.
   - Refuses datasets whose `schema` doesn't match `web-export/v1`.
3. **Demo path:** a separate dataset generator + explicit build command
   (never the default arguments), plus a GitHub Actions workflow
   (`deploy-pages`, manual dispatch / push trigger, no cron).

Privacy rails, restated as invariants:

- `webapp_out/` (private output) and any private dataset JSON are gitignored.
- The private build never runs in CI. The demo build never reads
  `~/.investing-home`.
- Frontend performs zero network requests in both forms.

## Demo dataset (locked, ticket 04)

Hybrid generation:

- **2–3 fictional symbols** (ACME-style) with synthetic price series from a
  piecewise drift/vol random-walk generator — these carry the deep timelines,
  multi-mode records, matured P2 scores, and fictional reports. Pages are
  visibly labeled fictional.
- **1–2 real, well-known, non-position symbols** run through the framework
  *on the day of generation*, producing a single genuine record each —
  demonstrating the real price pipeline end-to-end. **No history backfill**:
  backfilling records would fabricate a track record, which for a framework
  whose point is longitudinal honesty would be self-defeating.
- A not-advice disclaimer on every demo page.
- **Rejected:** scaling/perturbing the real vault — a price curve is a
  fingerprint; overlaying shapes identifies the symbol and reverse-engineers
  real positions and timing.

## Testing & CI

Follows the repo's established pattern (deterministic core in the pyyaml-only
main job; live paths gated):

- **Exporter tests** against a fixture vault (`tests/fixtures/`): contract
  shape (schema tag, consumption-checklist fields present), mechanical-signal
  arithmetic (cursor/discount/breach/stale/drawdown/put-proximity boundary
  cases), split-factor adjustment of record numbers, no-price and
  missing-field degradation, same-day double-record attribution, basket
  report anchor matching (including the h1-title false-match exclusion),
  ghost-row parsing, P2 pending/matured passthrough, cache append/stale
  fallback with an injectable history source, schema-mismatch refusal.
- **Builder tests**: pages generated for a fixture dataset; per-page data
  inlining; demo/private argument separation (the privacy invariants above
  asserted as tests where mechanically possible, e.g. builder refuses to
  write a demo build from a dataset marked private — dataset carries a
  `dataset: private|demo` tag for exactly this).
- **Vocabulary sync**: extending `VALUATION_ZONES` (+`Missing Inputs`) and
  `SYMBOL_PATTERNS` (+`JP`) updates the existing contract tests that pin
  those vocabularies; provider-mapping contract test covers JP.
- **Live smoke** (network-gated CI job, same as P1/P2): one real symbol per
  provider path through the history fetch + cache.
- No new dependency in the main CI job; `markdown` is imported lazily on the
  export path only.

## v1.1 (parked) and Out of scope

Parked with data already flowing in the v1 contract (UI only, no contract
changes needed): the cross-symbol **calibration/review view** (P2 aggregates
by stance/confidence/zone/market) and the **morning alert strip** (aggregated
drawdown/stale/earnings/put signals). Both start only after v1's two views
land.

Out of scope permanently (per guardrails): broker sync, scheduled/hosted
monitoring, multi-user/SaaS/auth, trade execution, v1 write-back.

## Verification

1. `python -m unittest discover -s tests -p 'test_*.py' -v` — green in the
   repo venv, including all new exporter/builder/vocabulary tests.
2. `python scripts/validate_repo.py --profile full` — passes.
3. Fixture end-to-end: `export_web.py --home tests/fixtures/… --offline` →
   `build_webapp.py` → open `webapp_out/index.html` via `file://` — board
   renders, symbol pages render, zero console network activity.
4. Real end-to-end (manual, private): run the private build against the real
   vault; compare both views against the retained 06/07 prototypes
   (`.scratch/stock-analysis-web-app/prototypes/`) — same cards, same bands,
   same report rendering; confirm the real-data patches (Missing Inputs
   column, JP symbol, no-price card, clamped extremes, basket anchor jump,
   all-pending P2 chips) all render as designed.
5. Demo end-to-end (may follow later): generate the demo dataset, build,
   deploy to GitHub Pages via manual dispatch, verify no private strings in
   the published artifact (mechanical grep for vault paths/symbols as a
   pre-publish check).
