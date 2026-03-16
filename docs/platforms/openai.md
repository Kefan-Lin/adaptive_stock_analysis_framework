# OpenAI-Compatible Usage

## Included Metadata

Each skill in this repository keeps its OpenAI-oriented metadata in:

```text
skills/<skill-name>/agents/openai.yaml
```

That metadata is preserved so the repository can be referenced by OpenAI-compatible skill workflows that support GitHub-path or local-directory ingestion.

## Repository Paths

The main controller skill is:

```text
skills/analyzing-stocks
```

Industry companion skills live alongside it under `skills/`.

## GitHub-Path Installation Pattern

If your environment supports GitHub-path installation, reference the repository paths directly. Typical paths are:

- `skills/analyzing-stocks`
- `skills/analyzing-software-platforms`
- `skills/analyzing-banks`
- `skills/analyzing-consumer-retail`

For environments that support a repository installer script, the common pattern is:

```bash
python install-skill-from-github.py --repo <owner>/<repo> --path skills/analyzing-stocks
```

You can install multiple companion skills in the same call by passing multiple `--path` values.

## Local Directory Pattern

If your OpenAI-compatible environment loads skills from local directories:

1. Clone this repository locally.
2. Point the client or installer at `skills/<skill-name>`.
3. Keep the `agents/openai.yaml` file with the skill directory.

## Recommended Set

For most setups, start with:

- `skills/analyzing-stocks`
- the 2-4 industry skills you use most often

If you want the full framework, install all directories under `skills/`.
