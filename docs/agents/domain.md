# Domain documentation

## Layout

This repository uses a single domain context:
- GLOSSARY.md at the repository root.
- Architecture decision records under docs/adr/.

## Reading rules

Before exploring an area, read the glossary and relevant ADRs.
If they do not exist, proceed silently.
Create them lazily when terms or decisions are actually resolved.

Use the glossary's vocabulary consistently in specifications,
issues, code discussions, and tests.

If a needed concept is missing, identify the gap for domain modeling.
Do not present proposed terminology as an agreed definition.

If proposed work contradicts an ADR, identify the conflict explicitly
and explain why the decision may need revisiting.
Do not silently override recorded decisions.
