# Issue tracker: GitHub

Repository: Kefan-Lin/adaptive_stock_analysis_framework
URL: https://github.com/Kefan-Lin/adaptive_stock_analysis_framework

Specs and new engineering tasks live in GitHub Issues.
Existing .scratch/ material remains in place; migrate only when requested.

## Access

Prefer the connected GitHub tools when they support the operation.
Otherwise use gh with an explicit
--repo Kefan-Lin/adaptive_stock_analysis_framework argument.

GitHub connector access was verified on 2026-11-07.
Local gh access was blocked by the execution environment's proxy restriction.
Do not assume the CLI is available until verified.

Before creating issues, verify the target repository.
Never publish project tasks to the upstream skills repository.

For CLI issue bodies and comments, write multiline text to a temporary
file and use --body-file.

## Operations

- Publish a spec: create an issue with the ready-for-agent label.
- Fetch a task: read its body, labels, comments, and blocking dependencies.
- Track implementation: one issue per independently verifiable task.
- Link child tasks using native sub-issues where supported.
  Otherwise use "Part of #N" in the child and a task list in the parent.
- Record blockers using native issue dependencies where supported.
  Otherwise use "Blocked by: #N, #M" near the top of the issue body.
- A task is unblocked only when all its blockers are closed.
- Record progress and decisions in issue comments.
- Close a task after recording its outcome and verification evidence.
- Map triage states using docs/agents/triage-labels.md.

## Pull requests as a triage surface

PRs as a request surface: no.

## Wayfinding

- Map: one issue labelled wayfinder:map.
- Children: linked issues labelled wayfinder:research,
  wayfinder:prototype, wayfinder:grilling, or wayfinder:task.
- Frontier: open, unblocked, unassigned child issues, in map order.
- Claim: assign the issue to the driving developer before starting.
- Resolve: record the answer, close the child, and add its result
  and link to the map's decisions.
- Create wayfinder labels only when that workflow is used.
