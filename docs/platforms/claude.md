# Claude Installation

## Default Path

This repository installs Claude skills into:

```bash
~/.claude/skills
```

## Quick Install

From the cloned repository root:

```bash
bash install/install-claude.sh
```

Install a subset of skills:

```bash
bash install/install-claude.sh analyzing-stocks analyzing-consumer-retail analyzing-real-estate
```

Install into a custom directory:

```bash
bash install/install-claude.sh --dest "$HOME/.claude/skills"
```

Copy instead of symlink:

```bash
bash install/install-claude.sh --copy
```

Replace existing installed skill directories:

```bash
bash install/install-claude.sh --force
```

## Skills That Run Repository Code

`morning-check`, `outcome-scoring`, and `discovering-inflections` execute deterministic code that lives in this repository — `scripts/morning_check.py`, `scripts/outcome_score.py`, and the `inflection_discovery/` package — not inside the installed skill directory. Keep the cloned repository in place and run those commands from the repository root (each SKILL.md states the exact command). The default symlink install keeps a path back to the clone; `--copy` does not, so the clone is still required. The monitoring and scoring scripts need only PyYAML; the discovery engine uses the repository's uv-managed `.venv`.

## Verify

Check that the skill directories exist:

```bash
ls ~/.claude/skills/analyzing-stocks
ls ~/.claude/skills/analyzing-healthcare-biotech
ls ~/.claude/skills/morning-check
```

Restart Claude if the client does not reload skills automatically.
