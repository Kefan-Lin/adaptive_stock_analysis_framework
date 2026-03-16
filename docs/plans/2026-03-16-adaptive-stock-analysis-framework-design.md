# Adaptive Stock Analysis Framework Design

## Goal

Create a release-ready Git repository for the Adaptive Stock Analysis Framework that can be cloned from GitHub and installed for Codex, Claude, and OpenAI-compatible skill workflows.

## Repository Shape

The repository uses a single-source layout:

- `skills/` stores the controller skill, its shared references, and all industry companion skills.
- `install/` stores user-facing installation scripts.
- `docs/` stores platform guidance and the framework map.
- `examples/` stores sample prompts and routing examples.

This avoids a `src/` and `dist/` split because the framework is already text-first skill content and should remain easy to inspect and maintain.

## Skill Model

`analyzing-stocks` remains the controller skill. It owns:

- the unified report contract
- routing logic
- shared references in `references/`
- OpenAI-facing metadata in `agents/openai.yaml`

The 10 industry skills remain companion skills. They keep their own `SKILL.md` and `agents/openai.yaml` and do not duplicate controller-level logic.

## Platform Support

### Codex

Primary install target is `~/.agents/skills/` using symlinks so updates from `git pull` are reflected immediately. Documentation also notes the legacy `~/.codex/skills/` path for older environments.

### Claude

Install target is `~/.claude/skills/`, also using symlinks by default.

### OpenAI

The repository preserves per-skill `agents/openai.yaml` metadata and provides GitHub-path-based usage guidance. No custom local path convention is invented in this repo.

## Installation Approach

The repository will provide:

- `install/install.sh` as the main entrypoint
- `install/install-codex.sh`
- `install/install-claude.sh`

The installer will:

- resolve the repository root dynamically
- install either all skills or a selected subset
- create destination directories if missing
- default to symlink mode
- support copy mode when requested
- fail clearly if the target already exists unless overwrite is explicit

## Verification

The repository will include:

- a repository validator to confirm required files exist
- shell-based installation tests using temporary directories
- final verification commands run before claiming completion

## Release Contract

A successful result must leave a standalone git repository in `adaptive_stock_analysis_framework/` with:

- migrated skills
- installation tooling
- platform documentation
- examples
- license and ignore rules
- verification artifacts that prove the install flow works
