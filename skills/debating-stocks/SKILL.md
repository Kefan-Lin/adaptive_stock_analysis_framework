---
name: debating-stocks
description: Stress-test an equity thesis or live decision through a structured, fact-checked adversarial debate. Parallel bull/bear (or multi-stakeholder) debater subagents each do their own live research and steelman, cross-rebut, a neutral verifier checks every claim, then the moderator synthesizes a verdict with cruxes, confidence, scenario-based expected returns, and flip/trim triggers. Use when a thesis is contested or high-stakes, to run the Red-Team / value-trap gate of `$analyzing-stocks`, to judge a corporate-action or event impact (spin-off, M&A, earnings), or to decide buy/hold/trim/sell on a position. Use when the user says "debate this stock", "argue both sides", "stress-test my thesis", "黄金坑还是价值陷阱", or "这次分拆/财报是利好还是利空".
---

# Debating Stocks

## Overview

The adversarial, fact-checked engine behind the `$analyzing-stocks` **Red-Team Gate** and value-trap judgment. **You are the moderator, not a debater — stay neutral until synthesis.** Spin up opposing debater subagents, make them fight on verified facts, then judge.

Core principle: **先用对抗性辩论逼出双方最强论证，再独立核查事实，最后才裁决并给仓位**。A Stance is earned only after a thesis survives a bull/bear debate whose every material claim has been independently verified — not after one analyst argues with themselves. Reuse `$analyzing-stocks` references so the debate speaks the framework's language (Bear/Base/Bull, Weighted Fair Value, Stance, Position Size, value-trap, flip / Trim-Exit triggers, Fact / Inference / Assumption).

## Modes

State `Mode` + `Reason` at the top of the verdict.

- `Thesis Stress-Test` — is the buy/avoid thesis right? Frame as **黄金坑 vs 价值陷阱** (golden pit vs value trap).
- `Event / Corporate-Action Impact` — spin-off, M&A, earnings, guidance, regulation: net positive or negative for valuation and investment? Verify the news is confirmed vs rumor first.
- `Position Decision` — a live holding (cost basis, weight, income vs total-return goal): add / hold / trim / sell / take-profit? Debate from the user's actual cost and sizing.

## Critical rule: subagents are stateless

Each `Agent` call starts cold. So, every round, the **moderator**:

- keeps the full running transcript;
- pastes the **opponent's latest arguments** into each debater's next prompt — a debater that can't see what it's rebutting will monologue;
- spawns same-round debaters **in one parallel message** so neither sees the other's current-round text (keeps it fair);
- may instead **continue a prior debater** by its `agentId` (Claude Code: `SendMessage`) so it retains its own research — still message each side separately.

## Workflow

Create a checklist (TodoWrite) for anything beyond one quick round.

1. **Frame** — Restate the question as a crisp, debatable resolution. Pick sides (2 = bull/bear by default; 3+ named stances for multi-stakeholder events). Set rounds (2 = opening + rebuttal default; 3 for hard calls), horizon (default 3–5y), and the current price anchor. **Internet-verify the setup first** — live price, and for events whether the news is actually confirmed.
2. **Round 1 — Openings (parallel).** One subagent per side. Each must: do its own live research (`WebSearch`/`WebFetch`), steelman its side, label `Fact / Inference / Assumption` with dated sources, and give a **Bear/Base/Bull annualized-return decomposition** from the current price.
3. **Rebuttal round(s) (parallel).** Re-spawn each debater with its own prior argument + the opponent's full prior argument. Force it to attack the opponent's data conflicts and defend its return math.
4. **Fact-check (MANDATORY).** One neutral verifier (takes no side). Mark every material claim `Supported / Disputed / Unverifiable` with a one-line reason + source, and **re-do the key arithmetic**. Probe the equity traps below. Discount flagged claims before synthesis.
5. **Synthesize the verdict** — the contract below.

## Equity fact-check traps (always probe in step 4)

- **CFO mislabeled as FCF**; FCF flattered by one-time tax or working-capital items → use a normalized figure.
- **Headline P/E or P/FCF distorted by one-off gains** (spin gains, tax benefits) → recompute on normalized earnings.
- **as-reported vs pro-forma** revenue/EBITDA growth (post-spin/M&A) — say which, and that pro-forma "growth" may lean on non-recurring items.
- **SOTP "upside" measured from a pre-news price while the stock already popped** → restate the remaining upside **from the current price**.
- **Capital-return / dividend claims**: "N consecutive years of increases" that has actually stalled or been frozen; buyback masking per-share decline.
- **Segment EBITDA scope**: a loss-making unit hiding a profitable one (or vice versa) inside a blended segment number.
- **Arithmetic**: recompute every yield, growth rate, and the probability-weighted expected return — an order-of-magnitude slip here has decided debates.

## Verdict contract

Output, in order (reuses the framework's language so it feeds back into `$analyzing-stocks` / `$investment-decision-workflow`):

- **Resolution / Mode**
- **Strongest case per side** — steelmanned, 2–4 bullets each.
- **Cruxes** — the genuine disagreements that decide it. For 3+ sides, map which stances conflict vs reconcilable.
- **Concessions & weak points** — where each side gave ground or argued poorly.
- **Fact-check ledger** — disputed/unverifiable claims and exactly what was discounted.
- **What would resolve each crux** — the data/test that settles it.
- **Expected annualized return** — `Bear / Base / Bull` with probabilities + probability-weighted, **decomposed** (starting FCF/earnings yield + per-share growth + multiple re-rating + capital returns), measured **from the current price**.
- **Verdict + Confidence + Flip conditions** — a reasoned call; if genuinely balanced, say so and explain why.
- **Framework hand-off** — `Stance` (Buy/Add/Hold/Reduce/Avoid), `value-trap judgment`, `Red-Team Gate result`, `Position Size` impact, `Add-on Trigger`, `Trim/Exit Trigger`, monitor list.
- **Caveats** — assumptions, scope; and the standard line: *analytical synthesis, not personalized investment advice.*

## Hard rules

1. Moderator stays neutral until synthesis; debaters never judge themselves.
2. Internet-verify price, latest filing, guidance, and capital action before any verdict (follow `$analyzing-stocks` → `source-policy`). Every material number carries a date.
3. **Fact-check is mandatory.** Any inflated or mis-stated claim is corrected and discounted before it can support the verdict.
4. Same-round debaters run in parallel; never let one see the other's current-round text.
5. Expected return and remaining upside are measured **from the current price**, not a pre-move anchor.
6. No positive Stance without an explicit downside/flip path. If a debater concedes a structural decline, the verdict must carry it.
7. Mirror the `$investment-decision-workflow` **Valuation Evidence Gate**: do not move Bear/Base/Bull fair value just because price moved — price changes update margin of safety, expected return, and valuation zone, not intrinsic value.
8. Reuse, don't reinvent: `$analyzing-stocks` references (`valuation-scenarios`, `value-investing-lens`, `risk-register`, `portfolio-sizing`) for the analysis spine; `$investment-decision-workflow` for execution/sizing of any resulting action.

## Templates

See [REFERENCE.md](REFERENCE.md) for copy-paste debater / rebuttal / neutral-fact-checker / judge prompts and the three mode presets.
