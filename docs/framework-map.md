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
- loading shared references
- enforcing evidence quality
- producing the unified 10-block report

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
- KPI trees
- accounting traps
- valuation routing
- industry-specific risks
- monitor triggers

## Typical Flow

1. User asks for company or stock analysis.
2. Invoke `analyzing-stocks`.
3. The controller identifies the primary business model.
4. The controller routes to one industry companion skill.
5. The controller uses shared references plus the industry output.
6. The final output uses the unified report contract.

## Packaging Notes

- Each skill directory contains its own `SKILL.md`.
- OpenAI-oriented metadata is preserved in `agents/openai.yaml`.
- Shared references live only under `skills/analyzing-stocks/references/`.
