# Solver Bot

Automated coding bot that reads GitHub Issues and generates code fixes → PR.

## Architecture

**Environment Separation**: Agent environment ≠ Project environment

| | Agent Environment | Project Environment |
|---|---|---|
| Setup by | Workflow | **Agent (reads README.md)** |
| Location | System Python/Node | Project-defined (e.g., `venv`) |
| Dependencies | `google-genai` or `codex` | Project-defined |

Agent reads project files (README.md, pyproject.toml) to understand setup.
This allows the solver to work with any project without hardcoded commands.

## Workflows

<!-- markdownlint-disable MD013 -->
| Workflow | Agent | Branch | Features |
|----------|-------|--------|----------|
| `solver-codex.yml` | OpenAI Codex CLI | `codex-issue-N` | Full agent |
| `solver-gemini.yml` | Gemini (Vertex AI) | `gemini-issue-N` | Tool-calling agent |
<!-- markdownlint-enable MD013 -->

## Usage

1. **Actions** → Select **solver-codex** or **solver-gemini**
2. **Run workflow** → Select branch, enter `issue_number`
3. Agent sets up project env → explores code → makes changes → runs tests → PR

## Flow

```text
1. Workflow: Setup agent env (google-genai or codex only)
2. Agent: Read README.md to understand project setup
3. Agent: Setup project env following project instructions
4. Agent: Explore codebase, make changes, run tests
5. Workflow: Commit only intended files (exclude .solver, .secrets, etc.)
6. Workflow: Create/update PR
```

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

## Commit Filtering

Workflow automatically excludes from commits:

- `.solver/` - Temporary issue context
- `.secrets/` - GCP credentials
- `.codex/` - Codex auth

Project venv (e.g., `venv/`) should be in project's `.gitignore`.

## Limits

- **Job timeout**: 30 minutes
- **Max iterations**: 20 (configurable for Gemini)
- **Shell command timeout**: 120 seconds

## TODO

- [ ] Add Issue/PR event triggers
- [ ] Allowlist-based actor filtering
- [ ] Auto-close PR when Issue is closed
