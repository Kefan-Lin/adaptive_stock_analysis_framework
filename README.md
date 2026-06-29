# Adaptive Stock Analysis Framework

Adaptive Stock Analysis Framework is a multi-skill equity research framework built around one controller skill and ten industry companion skills. It is packaged as a GitHub-ready repository that can be cloned and installed for Codex, Claude, and OpenAI-compatible skill workflows.

## Included

- `investment-decision-workflow` as the end-to-end decision orchestrator
- `analyzing-stocks` as the research and valuation controller skill
- `debating-stocks` as the fact-checked adversarial bull/bear debate engine for contested theses, events, and positions
- 10 industry companion skills
- shared references for source policy, diagnostics, valuation, portfolio sizing, and report structure
- OpenAI-oriented metadata in `agents/openai.yaml`
- installation scripts for Codex and Claude
- platform docs and example prompts

## Quick Start

Clone the repository:

```bash
git clone <your-github-url> adaptive_stock_analysis_framework
cd adaptive_stock_analysis_framework
```

Install for Codex:

```bash
bash install/install-codex.sh
```

Install for Claude:

```bash
bash install/install-claude.sh
```

Install only selected skills:

```bash
bash install/install-codex.sh analyzing-stocks analyzing-software-platforms analyzing-banks
```

Copy instead of symlink:

```bash
bash install/install-codex.sh --copy
```

## Repository Layout

```text
adaptive_stock_analysis_framework/
├── skills/         # controller skill, references, and companion skills
├── install/        # installation scripts
├── docs/           # platform docs and framework map
├── examples/       # sample prompts and routing examples
├── scripts/        # repository validation
└── tests/          # install and validation checks
```

## Skill Topology

`investment-decision-workflow` routes new ideas, existing reports, live positions, and events through research, valuation, stale checks, incremental valuation updates, decision briefs, and execution sheets.

`debating-stocks` runs a fact-checked bull/bear (or multi-stakeholder) debate to stress-test a contested thesis, judge a corporate-action or event impact, or decide a live position; `analyzing-stocks` and `investment-decision-workflow` escalate to it for the Red-Team / value-trap gate.

`analyzing-stocks` routes companies into one primary industry path:

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

See `docs/framework-map.md` for the controller contract and routing structure.

## Platform Docs

- `docs/platforms/codex.md`
- `docs/platforms/claude.md`
- `docs/platforms/openai.md`

## Examples

- `examples/prompts.md`
- `examples/routing-examples.md`

## Verify

Run the repository checks:

```bash
python3 scripts/validate_repo.py --profile full
bash tests/test_install.sh
```

## License

MIT
