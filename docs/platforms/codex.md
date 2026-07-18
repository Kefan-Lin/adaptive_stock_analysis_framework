# Codex Installation

## Default Path

This repository installs Codex skills into:

```bash
~/.agents/skills
```

That is the preferred path for native skill discovery in current Codex environments.

## Quick Install

From the cloned repository root:

```bash
bash install/install-codex.sh
```

Install a subset of skills:

```bash
bash install/install-codex.sh analyzing-stocks analyzing-software-platforms analyzing-banks
```

Install into a custom directory:

```bash
bash install/install-codex.sh --dest "$HOME/.agents/skills"
```

Copy instead of symlink:

```bash
bash install/install-codex.sh --copy
```

Replace existing installed skill directories:

```bash
bash install/install-codex.sh --force
```

## Legacy Path

Some older Codex setups still read from:

```bash
~/.codex/skills
```

If you need that layout, install there explicitly:

```bash
bash install/install-codex.sh --dest "$HOME/.codex/skills"
```

## Skills That Run Repository Code

`morning-check`, `outcome-scoring`, and `discovering-inflections` execute deterministic code that lives in this repository — `scripts/morning_check.py`, `scripts/outcome_score.py`, and the `inflection_discovery/` package — not inside the installed skill directory. Keep the cloned repository in place and run those commands from the repository root (each SKILL.md states the exact command). The default symlink install keeps a path back to the clone; `--copy` does not, so the clone is still required. The monitoring and scoring scripts need only PyYAML; the discovery engine uses the repository's uv-managed `.venv`.

## Verify

Check that the skills exist in the destination:

```bash
ls ~/.agents/skills/analyzing-stocks
ls ~/.agents/skills/discovering-inflections
```

Restart Codex if your environment does not hot-reload skills.
