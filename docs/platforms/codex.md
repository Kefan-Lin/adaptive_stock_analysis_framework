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

## Verify

Check that the skills exist in the destination:

```bash
ls ~/.agents/skills/analyzing-stocks
ls ~/.agents/skills/analyzing-software-platforms
```

Restart Codex if your environment does not hot-reload skills.
