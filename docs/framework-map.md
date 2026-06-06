# Framework Map

## Core Structure

The framework has one end-to-end decision workflow, one research controller skill, and ten industry companion skills.

```text
investment-decision-workflow
└── orchestrates analyzing-stocks, stale checks, valuation updates, decision briefs, and execution sheets

analyzing-stocks
├── references/
│   ├── source-policy.md
│   ├── industry-structure.md
│   ├── industry-playbooks.md
│   ├── business-moat.md
│   ├── financial-diagnostics.md
│   ├── capital-allocation.md
│   ├── valuation-router.md
│   ├── valuation-scenarios.md
│   ├── value-investing-lens.md
│   ├── portfolio-sizing.md
│   └── report-template.md
└── routes to one primary industry skill
```

## Decision Workflow Skill

`investment-decision-workflow` is responsible for:

- selecting `New Idea Decision`, `Existing Report to Action`, `Position Review`, or `Event Review`
- running live verification before current execution advice
- requiring stale checks and incremental valuation updates for existing reports, positions, and events
- reusing `analyzing-stocks` as the Research and Valuation Engine
- mapping research output into candidate tier, valuation zone, execution method, option suitability, and review triggers
- enforcing equivalent exposure, no-action, do-not-initiate, technical-filter, and earnings-risk rules

## Controller Skill

`analyzing-stocks` is responsible for:

- defining the decision scope
- routing the company into the right industry path
- choosing the right analysis family and valuation family
- loading shared references
- enforcing evidence quality
- producing the unified 10-block report
- merging primary and secondary sector overlays into one stable contract

## Industry Companion Skills

The controller routes to one primary skill from this set:

- `analyzing-software-platforms`
- `analyzing-consumer-retail`
- `analyzing-industrials-transport`
- `analyzing-semiconductors-hardware`
- `analyzing-resource-energy-materials`
- `analyzing-banks`
- `analyzing-insurers`
- `analyzing-real-estate`
- `analyzing-healthcare-biotech`
- `analyzing-utilities-telecom`

These skills should not replace the controller. They provide only:

- subtype classification
- analysis family
- valuation family
- KPI trees
- accounting traps
- valuation anchors
- industry-specific risks
- monitor triggers
- sections influenced

## Typical Flow

1. User asks for an investment decision, action plan, position review, or event response.
2. Invoke `investment-decision-workflow`.
3. The workflow selects the mode and verifies current data.
4. For new or stale research, the workflow invokes `analyzing-stocks`.
5. The controller identifies the primary business model and routes to the right industry companion skill.
6. The workflow performs stale check or incremental valuation update when using prior material.
7. The final output is a decision brief plus execution sheet.

## Shared-Reference Contract

Shared references are not a license to force one methodology on every industry.

- `financial-diagnostics.md` must branch by diagnostic family.
- `valuation-scenarios.md` must branch by valuation family.
- `report-template.md` fixes the output blocks, not one universal DCF table.
- `value-investing-lens.md` applies downside discipline across different valuation anchors.

## Packaging Notes

- Each skill directory contains its own `SKILL.md`.
- OpenAI-oriented metadata is preserved in `agents/openai.yaml`.
- Shared references live only under `skills/analyzing-stocks/references/`.
