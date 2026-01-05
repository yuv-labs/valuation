# Solver Bot

Automated coding bot that reads GitHub Issues and generates code fixes → PR.

## Workflows

<!-- markdownlint-disable MD013 -->
| Workflow | Agent | Branch | Features |
|----------|-------|--------|----------|
| `solver-codex.yml` | OpenAI Codex CLI | `codex-issue-N` | Full agent (file R/W, terminal, retry loop) |
| `solver-gemini.yml` | Gemini (Vertex AI) | `gemini-issue-N` | Single-shot patch generator |
<!-- markdownlint-enable MD013 -->

## Usage

1. **Actions** → Select **solver-codex** or **solver-gemini**
2. **Run workflow** → Enter `issue_number`
3. Bot creates branch → modifies code → runs tests → creates PR

## Flow

```text
Issue fetch → Dev setup (venv + deps) → Agent run → pytest verify → Push → PR
```

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
├── solver_gemini.py      # Gemini patch generator
└── SOLVER_README.md      # This file
```

## TODO

- [ ] Add Issue/PR event triggers
- [ ] Allowlist-based actor filtering
- [ ] Auto-close PR when Issue is closed
