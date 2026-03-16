# Adaptive Stock Analysis Framework Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a standalone GitHub-ready repository for the Adaptive Stock Analysis Framework with migrated skills, multi-platform installation scripts, and verification coverage.

**Architecture:** Keep `skills/` as the single source of truth, preserve the controller-plus-subskills structure, and add thin installation and validation layers around it. Use shell installers for user entrypoints and lightweight Python validation plus shell integration tests for confidence.

**Tech Stack:** Markdown, Bash, Python 3 standard library, Git

---

### Task 1: Create repository skeleton and planning docs

**Files:**
- Create: `docs/plans/2026-03-16-adaptive-stock-analysis-framework-design.md`
- Create: `docs/plans/2026-03-16-adaptive-stock-analysis-framework.md`
- Create: `README.md`
- Create: `LICENSE`
- Create: `.gitignore`

**Step 1: Write the failing test**

Create a repository validation test that expects these files to exist.

**Step 2: Run test to verify it fails**

Run: `python3 scripts/validate_repo.py`
Expected: fail because the files and directories do not exist yet.

**Step 3: Write minimal implementation**

Create the top-level repository docs and metadata files.

**Step 4: Run test to verify it passes**

Run: `python3 scripts/validate_repo.py`
Expected: passes top-level structure checks.

**Step 5: Commit**

```bash
git add .
git commit -m "feat: scaffold adaptive stock analysis repo"
```

### Task 2: Migrate the framework skills into `skills/`

**Files:**
- Create: `skills/analyzing-stocks/**`
- Create: `skills/analyzing-banks/**`
- Create: `skills/analyzing-consumer-retail/**`
- Create: `skills/analyzing-healthcare-biotech/**`
- Create: `skills/analyzing-industrials-transport/**`
- Create: `skills/analyzing-insurers/**`
- Create: `skills/analyzing-real-estate/**`
- Create: `skills/analyzing-resource-energy-materials/**`
- Create: `skills/analyzing-semiconductors-hardware/**`
- Create: `skills/analyzing-software-platforms/**`
- Create: `skills/analyzing-utilities-telecom/**`

**Step 1: Write the failing test**

Extend validation to require all skills, controller references, and `agents/openai.yaml` files.

**Step 2: Run test to verify it fails**

Run: `python3 scripts/validate_repo.py`
Expected: fail with missing skill paths.

**Step 3: Write minimal implementation**

Copy the staged skill directories into `skills/` unchanged.

**Step 4: Run test to verify it passes**

Run: `python3 scripts/validate_repo.py`
Expected: all required skill files detected.

**Step 5: Commit**

```bash
git add .
git commit -m "feat: migrate adaptive stock analysis skills"
```

### Task 3: Add installation tooling

**Files:**
- Create: `install/install.sh`
- Create: `install/install-codex.sh`
- Create: `install/install-claude.sh`
- Test: `tests/test_install.sh`

**Step 1: Write the failing test**

Write shell tests that install into temporary directories and assert expected links or copied folders exist for Codex and Claude targets.

**Step 2: Run test to verify it fails**

Run: `bash tests/test_install.sh`
Expected: fail because installers do not exist.

**Step 3: Write minimal implementation**

Implement the common installer and thin platform wrappers.

**Step 4: Run test to verify it passes**

Run: `bash tests/test_install.sh`
Expected: pass for symlink installs in temp directories.

**Step 5: Commit**

```bash
git add .
git commit -m "feat: add multi-platform install scripts"
```

### Task 4: Add publishing documentation and examples

**Files:**
- Create: `docs/platforms/codex.md`
- Create: `docs/platforms/claude.md`
- Create: `docs/platforms/openai.md`
- Create: `docs/framework-map.md`
- Create: `examples/prompts.md`
- Create: `examples/routing-examples.md`
- Modify: `README.md`

**Step 1: Write the failing test**

Extend validation to require the platform docs and example files.

**Step 2: Run test to verify it fails**

Run: `python3 scripts/validate_repo.py`
Expected: fail with missing docs.

**Step 3: Write minimal implementation**

Add the platform installation and usage docs and link them from the README.

**Step 4: Run test to verify it passes**

Run: `python3 scripts/validate_repo.py`
Expected: full repository contract satisfied.

**Step 5: Commit**

```bash
git add .
git commit -m "docs: add install and usage documentation"
```

### Task 5: Verify and initialize git

**Files:**
- Create: `scripts/validate_repo.py`
- Modify: repository metadata as needed

**Step 1: Write the failing test**

Ensure validation reports a non-zero exit code on any missing required file or malformed skill root.

**Step 2: Run test to verify it fails**

Run: `python3 scripts/validate_repo.py --check-missing-placeholder`
Expected: fail under a forced negative check or before the repository is complete.

**Step 3: Write minimal implementation**

Implement the validator and run it alongside installation tests.

**Step 4: Run test to verify it passes**

Run:
- `python3 scripts/validate_repo.py`
- `bash tests/test_install.sh`

Expected: both commands exit successfully.

**Step 5: Commit**

```bash
git add .
git commit -m "chore: verify and initialize repository"
```

User already requested direct execution in this session, so implementation should proceed immediately after the plan is written.
