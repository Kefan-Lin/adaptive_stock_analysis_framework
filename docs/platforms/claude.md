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

## Verify

Check that the skill directories exist:

```bash
ls ~/.claude/skills/analyzing-stocks
ls ~/.claude/skills/analyzing-healthcare-biotech
```

Restart Claude if the client does not reload skills automatically.
