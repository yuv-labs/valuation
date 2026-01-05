# Solver Bot

Automated coding bot that reads GitHub Issues and generates code fixes → PR.

## Workflows

<!-- markdownlint-disable MD013 -->
| Workflow | Agent | Branch | Features |
|----------|-------|--------|----------|
| `solver-codex.yml` | OpenAI Codex CLI | `codex-issue-N` | Full agent (file R/W, terminal, retry) |
| `solver-gemini.yml` | Gemini (Vertex AI) | `gemini-issue-N` | Tool-calling agent with max iterations |
<!-- markdownlint-enable MD013 -->

## Usage

1. **Actions** → Select **solver-codex** or **solver-gemini**
2. **Run workflow** → Select branch, enter `issue_number`
3. Bot creates branch → explores code → makes changes → runs tests → PR

## Flow

```text
Issue fetch → Agent explores codebase → Modifies files → Runs pytest → Push → PR
```

## Agent Capabilities

Both agents can:

- **Read files** - Explore the codebase
- **Write files** - Create/modify code
- **Run shell commands** - Execute pytest, git status, etc.
- **Iterate** - Retry if tests fail (up to max_iterations)

## Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `issue_number` | required | GitHub issue number to solve |
| `max_iterations` | 20 | Max agent loop iterations (Gemini only) |

## Secrets

| Secret | Workflow | Purpose |
|--------|----------|---------|
| `CODEX_AUTH_JSON` | solver-codex | Codex CLI auth |
| `GCP_SA_KEY_JSON` | solver-gemini | Vertex AI auth |
| `GCP_PROJECT_ID` | solver-gemini | GCP project |
| `GCP_LOCATION` | solver-gemini | Vertex AI region |

## Files

```text
.github/workflows/
├── solver-codex.yml      # Codex workflow
├── solver-gemini.yml     # Gemini workflow
├── solver_gemini.py      # Gemini tool-calling agent
└── SOLVER_README.md      # This file
```

## Limits

- **Job timeout**: 30 minutes
- **Max iterations**: 20 (configurable for Gemini)
- **File read limit**: 50,000 chars
- **Shell command timeout**: 120 seconds

## TODO

- [ ] Add Issue/PR event triggers
- [ ] Allowlist-based actor filtering
- [ ] Auto-close PR when Issue is closed
