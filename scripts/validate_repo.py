#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

TOP_LEVEL_REQUIRED = [
    "README.md",
    "LICENSE",
    ".gitignore",
    "docs/plans/2026-03-16-adaptive-stock-analysis-framework-design.md",
    "docs/plans/2026-03-16-adaptive-stock-analysis-framework.md",
]

FULL_REQUIRED = [
    "skills/investment-decision-workflow/SKILL.md",
    "skills/investment-decision-workflow/agents/openai.yaml",
    "skills/analyzing-stocks/SKILL.md",
    "skills/analyzing-stocks/agents/openai.yaml",
    "skills/analyzing-stocks/references/business-moat.md",
    "skills/analyzing-stocks/references/capital-allocation.md",
    "skills/analyzing-stocks/references/financial-diagnostics.md",
    "skills/analyzing-stocks/references/industry-playbooks.md",
    "skills/analyzing-stocks/references/industry-structure.md",
    "skills/analyzing-stocks/references/macro-overlay.md",
    "skills/analyzing-stocks/references/portfolio-construction.md",
    "skills/analyzing-stocks/references/portfolio-sizing.md",
    "skills/analyzing-stocks/references/risk-register.md",
    "skills/analyzing-stocks/references/report-template.md",
    "skills/analyzing-stocks/references/source-policy.md",
    "skills/analyzing-stocks/references/valuation-router.md",
    "skills/analyzing-stocks/references/valuation-scenarios.md",
    "skills/analyzing-stocks/references/value-investing-lens.md",
    "skills/debating-stocks/SKILL.md",
    "skills/debating-stocks/REFERENCE.md",
    "skills/debating-stocks/agents/openai.yaml",
    "skills/analyzing-banks/SKILL.md",
    "skills/analyzing-banks/agents/openai.yaml",
    "skills/analyzing-consumer-retail/SKILL.md",
    "skills/analyzing-consumer-retail/agents/openai.yaml",
    "skills/analyzing-healthcare-biotech/SKILL.md",
    "skills/analyzing-healthcare-biotech/agents/openai.yaml",
    "skills/analyzing-industrials-transport/SKILL.md",
    "skills/analyzing-industrials-transport/agents/openai.yaml",
    "skills/analyzing-insurers/SKILL.md",
    "skills/analyzing-insurers/agents/openai.yaml",
    "skills/analyzing-real-estate/SKILL.md",
    "skills/analyzing-real-estate/agents/openai.yaml",
    "skills/analyzing-resource-energy-materials/SKILL.md",
    "skills/analyzing-resource-energy-materials/agents/openai.yaml",
    "skills/analyzing-semiconductors-hardware/SKILL.md",
    "skills/analyzing-semiconductors-hardware/agents/openai.yaml",
    "skills/analyzing-software-platforms/SKILL.md",
    "skills/analyzing-software-platforms/agents/openai.yaml",
    "skills/analyzing-utilities-telecom/SKILL.md",
    "skills/analyzing-utilities-telecom/agents/openai.yaml",
    "install/install.sh",
    "install/install-codex.sh",
    "install/install-claude.sh",
    "docs/platforms/codex.md",
    "docs/platforms/claude.md",
    "docs/platforms/openai.md",
    "docs/framework-map.md",
    "examples/prompts.md",
    "examples/routing-examples.md",
    "tests/test_install.sh",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate repository structure.")
    parser.add_argument(
        "--profile",
        choices=("top-level", "full"),
        default="full",
        help="Validation profile to run.",
    )
    return parser.parse_args()


def check_required(paths: list[str]) -> list[str]:
    missing = []
    for relative_path in paths:
        if not (REPO_ROOT / relative_path).exists():
            missing.append(relative_path)
    return missing


def main() -> int:
    args = parse_args()
    required = list(TOP_LEVEL_REQUIRED)
    if args.profile == "full":
        required.extend(FULL_REQUIRED)

    missing = check_required(required)
    if missing:
        print("Missing required paths:")
        for item in missing:
            print(f"- {item}")
        return 1

    print(f"Repository validation passed for profile: {args.profile}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
