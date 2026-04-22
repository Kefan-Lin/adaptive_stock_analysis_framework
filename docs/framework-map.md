# Framework Map

## Core Structure

The framework has one controller skill and ten industry companion skills.

```text
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

1. User asks for company or stock analysis.
2. Invoke `analyzing-stocks`.
3. The controller identifies the primary business model.
4. The controller routes to one industry companion skill.
5. The controller selects the correct analysis family and valuation family.
6. The controller uses shared references plus the industry output.
7. The final output uses the unified report contract.

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
