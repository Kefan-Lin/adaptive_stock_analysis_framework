# Adaptive Stock Analysis Framework

[![CI](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/actions/workflows/ci.yml/badge.svg)](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

Adaptive Stock Analysis Framework is a multi-skill equity research system that adapts the analysis to a company's industry instead of forcing every name through one generic template. A controller skill routes each company into one of ten industry-specific frameworks, enforces valuation and red-team discipline before any conclusion, and can escalate a contested thesis to a fact-checked adversarial debate engine.

It is packaged as a GitHub-ready repository that can be cloned and installed for Codex, Claude, and OpenAI-compatible skill workflows.

## Included

- `investment-decision-workflow` as the end-to-end decision orchestrator
- `analyzing-stocks` as the research and valuation controller skill
- `debating-stocks` as the fact-checked adversarial bull/bear debate engine for contested theses, events, and positions
- 10 industry companion skills
- 14 shared references covering source policy, financial diagnostics, valuation routing and scenarios, business moat, capital allocation, risk register, macro overlay, portfolio sizing and construction, and report structure
- per-skill OpenAI metadata in `agents/openai.yaml`
- installation scripts for Codex and Claude
- platform docs and example prompts
- a Python test suite and repository validator wired into GitHub Actions CI

## Quick Start

Clone the repository:

```bash
git clone https://github.com/Kefan-Lin/adaptive_stock_analysis_framework.git
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
├── tests/          # install and validation checks
└── .github/        # GitHub Actions CI workflow
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

Run the full check suite locally (the same steps GitHub Actions runs on every push and pull request):

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_repo.py --profile full
bash tests/test_install.sh
```

## License

MIT
