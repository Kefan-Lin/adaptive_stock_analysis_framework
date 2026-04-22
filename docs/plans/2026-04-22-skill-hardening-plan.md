# Skill Hardening Plan

## Goal

Fix the framework issues surfaced in the review: sector-unsafe shared valuation and diagnostics logic, overly broad industry routing, US-centric source policy, weak sizing rules, and unstable controller/output contract wording.

## Execution Rules

- Execute one task at a time.
- For each task: add or update regression tests first, implement the changes, run verification, review the diff, then commit.
- Do not batch multiple tasks into one commit.
- Avoid unrelated cleanup.

## Task 1: Sector-Safe Controller Contract

### Objective

Stop the controller from forcing bank/insurance/real-estate/early-biotech names into operating-company DCF and generic three-statement diagnostics.

### Files

- Modify: `skills/analyzing-stocks/SKILL.md`
- Modify: `skills/analyzing-stocks/references/financial-diagnostics.md`
- Modify: `skills/analyzing-stocks/references/valuation-scenarios.md`
- Modify: `skills/analyzing-stocks/references/report-template.md`
- Modify: `docs/framework-map.md`
- Modify: `examples/prompts.md`
- Create or modify tests for controller/reference contract coverage

### Required outcomes

- Shared diagnostics become route-aware instead of implicitly operating-company only.
- Shared valuation scenario guidance explicitly branches by valuation family.
- The controller no longer treats reverse DCF as mandatory for every route.
- `Stance` vocabulary is unified between controller and report template.
- The report contract states how primary skill output and sector overlays merge.

### Verification gate

- Targeted unit tests for the controller/reference contract pass.
- Repository validator still passes.
- Manual diff review finds no remaining hard conflict between shared references and sector skills.

## Task 2: Industry Taxonomy and Routing Boundaries

### Objective

Tighten coarse routing so healthcare services, property services, specialty chemicals, and tower/network infrastructure do not inherit the wrong KPI or valuation frame by default.

### Files

- Modify: `skills/analyzing-stocks/SKILL.md`
- Modify: `skills/analyzing-healthcare-biotech/SKILL.md`
- Modify: `skills/analyzing-real-estate/SKILL.md`
- Modify: `skills/analyzing-resource-energy-materials/SKILL.md`
- Modify: `skills/analyzing-utilities-telecom/SKILL.md`
- Modify: `examples/routing-examples.md`
- Modify any controller or docs references that still reflect the old coarse buckets
- Create or modify tests for routing and subtype wording

### Required outcomes

- Controller routing table distinguishes operating healthcare vs pipeline-heavy healthcare.
- Real-estate route stops defaulting property-services names into NAV/FFO logic.
- Resource/materials route separates specialty chemicals/processors from asset-NAV businesses.
- Utilities/telecom route makes tower and network infrastructure handling explicit.
- Examples and framework map reflect the new boundaries.

### Verification gate

- Targeted routing contract tests pass.
- Repository validator still passes.
- Manual review confirms route descriptions no longer contradict the intended valuation anchors.

## Task 3: Global Source Policy and Executable Sizing Rules

### Objective

Make the framework usable across US, HK, and CN markets, and make position-size downgrades operational for illiquid and high-friction names.

### Files

- Modify: `skills/analyzing-stocks/SKILL.md`
- Modify: `skills/analyzing-stocks/references/source-policy.md`
- Modify: `skills/analyzing-stocks/references/portfolio-sizing.md`
- Modify any examples or docs that summarize evidence or sizing rules
- Create or modify tests for source-policy and sizing requirements

### Required outcomes

- Primary source checklist covers SEC, HKEX, and A-share disclosure patterns.
- Guidance references IFRS / US GAAP / PRC GAAP interpretation risk where relevant.
- Portfolio sizing includes quant-ish liquidity and spread heuristics.
- ADR, micro-cap, low-turnover, and wide-spread names auto-downgrade appropriately.
- Controller wording stays consistent with the tightened sizing rules.

### Verification gate

- Targeted source-policy and sizing tests pass.
- Repository validator still passes.
- Manual review confirms no lingering US-only language in the shared source contract.
