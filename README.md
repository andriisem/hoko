# Hoko

> **Developer workflows in one command.**

Hoko is a CLI that installs, configures, and maintains Git hooks and repository quality tooling with sensible defaults. Instead of hand-editing `.pre-commit-config.yaml` or copy-pasting hook configs between repos, you install **capabilities** — `hoko add formatting` — and Hoko figures out the right tool for your project.

[![CI](https://github.com/andriisem/hoko/actions/workflows/ci.yml/badge.svg)](https://github.com/andriisem/hoko/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hoko.svg)](https://pypi.org/project/hoko/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

```bash
hoko init
hoko add python formatting secrets
git commit
```

No YAML. No copy-paste. No setup guides.

---

## Contents

- [Why Hoko](#why-hoko)
- [How Hoko compares](#how-hoko-compares)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Commands](#commands)
- [Capabilities](#capabilities)
- [Automatic project detection](#automatic-project-detection)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Development](#development)
- [Roadmap](#roadmap)
- [License](#license)

---

## Why Hoko

Setting up repository quality checks today means repeating the same manual steps in every project:

1. Install `pre-commit`
2. Hand-write `.pre-commit-config.yaml`
3. Search GitHub for the right hook repositories and pin versions
4. Wire up secret scanning, formatting, linting separately
5. Keep every hook version current, forever
6. Repeat step 1 in the next repository

Hoko replaces all of that with a small set of commands operating on **capabilities** — outcomes you want ("formatting", "secrets") — rather than tool-specific YAML. The underlying tool choice (Ruff vs. Prettier vs. gofmt) is an implementation detail Hoko resolves per project.

**Design principles**

- Convention over configuration
- Install capabilities, not tools
- Never require hand-editing YAML
- Safe and idempotent — running a command twice is a no-op, not a corruption risk
- Cross-platform, plugin-friendly architecture

---

## How Hoko compares

Hoko is **not a replacement for pre-commit** — it's built directly on top of it. Hoko shells out to the `pre-commit` binary and generates `.pre-commit-config.yaml` for you; if you're already happy hand-writing that file and tracking hook repos and revisions yourself, you don't need Hoko. What Hoko removes is the research and upkeep: deciding which hook repo to use, pinning a revision, merging it into existing YAML without clobbering hooks you added by hand, and doing all of that again for the next repo and the next tool update.

Husky solves a narrower, adjacent problem: it wires git hook *events* (`pre-commit`, `commit-msg`, ...) to scripts you already have, typically paired with `lint-staged` to scope them to staged files. It doesn't help you decide which tools to run or install them, and it's npm/Node-specific — a polyglot repo (Python + Go + JS) needs separate hook plumbing per ecosystem. Hoko and pre-commit are language-agnostic by design.

| | Husky | pre-commit | Hoko |
|---|---|---|---|
| What it manages | Wiring git hook events to scripts you provide | Git hooks + hook-tool installation, via a YAML config you author | Same engine as pre-commit, but generates and merges that config for you |
| Choosing a tool | You decide and wire it up yourself | You decide, then find and pin the hook repo + revision | Hoko resolves the tool per detected ecosystem (`formatting` → Ruff, Prettier, gofmt, or rustfmt) |
| Cross-language repos | No — npm/Node-oriented | Yes | Yes |
| Keeping hooks current | Manual | `pre-commit autoupdate`, invoked by hand | `hoko update` — same mechanism, same command surface as everything else |
| Health/audit | None | None built in | `hoko doctor` scores the repo and flags missing or stale setup |
| Sharing a setup across repos | Copy config files by hand | Copy `.pre-commit-config.yaml` by hand | `hoko export` / `hoko import` |
| Config you hand-edit | Hook scripts | `.pre-commit-config.yaml` | None — `hoko add`/`hoko rm` only |

If you already know exactly which hooks you want and are comfortable maintaining the YAML yourself, plain pre-commit is one less layer. Hoko is for the more common case: you know you want "formatting" and "secret scanning" on every repo, not which specific tool and pinned revision that means this month.

---

## Installation

Requires **Python 3.12+**.

```bash
# uv (recommended)
uv tool install hoko

# pipx
pipx install hoko

# pip
pip install hoko
```

From source:

```bash
git clone https://github.com/andriisem/hoko.git
cd hoko
uv sync
uv run hoko --help
```

---

## Quickstart

```bash
cd my-project

hoko init                       # detect the project, install pre-commit, wire up git hooks
hoko add python formatting secrets
git commit                      # hooks run automatically
```

Verify everything is healthy at any time:

```bash
hoko doctor
```

```
Repository Health

100 / 100

✓ Hooks installed
✓ Configuration valid
```

---

## Commands

| Command | Description |
|---|---|
| `hoko init [--yes]` | Detects the project, installs `pre-commit` if missing, installs recommended capabilities, and wires up Git hooks. `--yes` skips the confirmation prompt. |
| `hoko add [capability]...` | Installs one or more capabilities and updates `.pre-commit-config.yaml`. Run without arguments to pick from an interactive list. |
| `hoko rm [capability]...` | Removes one or more capabilities. Run without arguments to pick from an interactive list. |
| `hoko list` | Lists installed capabilities. |
| `hoko doctor [--fix] [--json]` | Scores repository health (0–100) and flags issues such as missing hooks or stale configuration. `--fix` reapplies the configured capabilities to repair what it finds. `--json` prints a machine-readable report (score, capabilities, checks) for CI or dashboards instead. |
| `hoko update` | Updates all managed hook versions to their latest release. |
| `hoko check` | Runs every configured hook without creating a commit — built for CI. |
| `hoko export [path]` | Writes installed capabilities to a preset file (defaults to `hoko.yaml`). |
| `hoko import <path>` | Installs every capability listed in a preset file. |

Every command exposes `--help` for full option details:

```bash
hoko <command> --help
```

### Interactive selection

Run `hoko add` or `hoko rm` without arguments to pick capabilities from a list. Use the arrow keys to move, space to toggle, and enter to confirm:

```
? Which capabilities do you want to install? (space to select, enter to confirm)

  ◯ commitlint  Conventional commit message linting.
❯ ◉ docker      Dockerfile linting.
  - formatting  Code formatting for the detected language. (installed)
  ◯ markdown    Markdown linting.
  ◉ python      Python linting and type checking.
  ◯ secrets     Secret scanning.
  ◯ yaml        YAML linting.
```

`hoko add` greys out what is already installed, and `hoko rm` lists only what you actually have. Outside a terminal — in CI or when piping — both commands require explicit arguments instead of prompting.

### Using `hoko check` in CI

```yaml
- name: Run Hoko checks
  run: |
    pipx install hoko
    hoko check
```

### Using `hoko doctor --json` for CI or dashboards

`hoko doctor --json` prints nothing but a single JSON object — safe to pipe into `jq` or a dashboard ingester:

```bash
hoko doctor --json
```

```json
{
  "score": 100,
  "capabilities": ["python", "formatting", "secrets"],
  "fix_attempted": false,
  "checks": [
    { "message": "pre-commit available", "ok": true },
    { "message": "Hooks installed", "ok": true },
    { "message": "Configuration valid", "ok": true }
  ]
}
```

Combine with `--fix` to repair and report in one step — `fix_attempted` tells you whether remediation ran, `score` tells you whether it worked:

```bash
hoko doctor --fix --json
```

---

## Capabilities

Capabilities describe an outcome, not a tool. Hoko resolves the tool per detected ecosystem:

| Capability | Purpose | Resolves to |
|---|---|---|
| `python` | Linting and type checking | Ruff, mypy |
| `formatting` | Code formatting | Ruff Formatter (Python), Prettier (JS/TS), gofmt (Go), rustfmt (Rust) |
| `secrets` | Secret scanning | detect-secrets, gitleaks |
| `markdown` | Markdown linting | markdownlint |
| `yaml` | YAML linting | yamllint |
| `docker` | Dockerfile linting | hadolint |
| `commitlint` | Conventional commit message linting | commitlint |

List capabilities available in your installed version at any time:

```bash
hoko add --help
```

---

## Automatic project detection

`hoko init` inspects the repository root for known markers and recommends capabilities accordingly:

| Marker | Ecosystem |
|---|---|
| `pyproject.toml`, `setup.py` | Python |
| `package.json` | JavaScript |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `Dockerfile` | Docker |
| `.github/workflows/` | GitHub Actions |

---

## Configuration

Hoko keeps its own state in a small `hoko.yaml` at the repository root, separate from the generated `.pre-commit-config.yaml`:

```yaml
version: 1
capabilities:
  - python
  - formatting
  - secrets
```

Commands never hand-edit `.pre-commit-config.yaml` directly — it's always regenerated from this model, so it's safe to delete and regenerate at any time via `hoko init`.

Share a setup across repositories:

```bash
hoko export team-preset.yaml
hoko import team-preset.yaml   # in another repo
```

---

## Architecture

```
CLI (Typer)
   │
   ▼
Command Layer        hoko/commands/*.py
   │
   ▼
Capability Registry   hoko/capabilities/registry.py
   │
   ▼
Project Detection     hoko/detection/*.py
   │
   ▼
Configuration Model   hoko/config/models.py  (hoko.yaml)
   │
   ▼
Generators             hoko/generators/*.py
   │
   ▼
pre-commit Adapter    hoko/adapters/precommit.py  (.pre-commit-config.yaml)
```

```
hoko/
├── cli/            entry point (Typer app)
├── commands/        init, add, rm, list, doctor, update, check, export, import
├── capabilities/     capability registry
├── detection/        project + tooling detection, recommendations
├── config/           HokoConfig model (hoko.yaml)
├── generators/        hook repo / hook definitions
├── ui/               interactive prompts
└── adapters/
    └── precommit.py  translates the config model into .pre-commit-config.yaml
tests/
```

---

## Development

```bash
git clone https://github.com/andriisem/hoko.git
cd hoko

uv sync                 # install dependencies
uv run hoko --help       # run the CLI locally
uv run pytest            # run the test suite
uv run pytest -v          # verbose
```

CI runs the test suite on Linux and macOS across Python 3.12 and 3.13 for every push and pull request (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)). Releases are published to PyPI automatically on tag via [`.github/workflows/publish.yml`](.github/workflows/publish.yml).

Contributions are welcome — please open an issue to discuss significant changes before submitting a pull request.

---

## Roadmap

- **v0.1** — `init`, `add`, `rm`, `list`, `doctor`, `update`, `check`, `export`, `import`; Python/JavaScript/Go/Rust formatting, Python lint, secrets, markdown, yaml, docker, commitlint; interactive capability selection; preset export/import *(current — 0.1.7, published on PyPI)*
- **v0.2** — Hardening: CLI-level tests for `doctor`/`check`/`export`/`import`/`update`, a `doctor` score that reflects per-capability staleness rather than 3 fixed checks (stale hook revisions, missing companion configs, a missing `commit-msg` hook for capabilities that need one), `hoko --version`, standardized `vX.Y.Z` release tags, a `CHANGELOG.md`, and a published (not just drafted) Homebrew formula
- **v0.3** — Agent capabilities & extensibility:
  - `hoko agent add <name>` / `hoko agent rm` / `hoko agent list` — a separate namespace from hook capabilities, same interaction model as `hoko add`/`rm`/`list`
  - Agent capability registry to start: `code-review`, `infra-review` (IaC), `docs`, `dependency-audit`
  - Each agent capability resolves to a scoped system prompt, a least-privilege tool/permission manifest, and trigger wiring (PR-opened GitHub Actions workflow first; a git hook as a secondary trigger) — mirroring how `formatting` resolves to a concrete pre-commit hook today
  - New `hoko/adapters/agent_ci.py`: generates and merges a GitHub Actions workflow YAML non-destructively, the same principle `precommit.py` already applies to `.pre-commit-config.yaml`
  - A per-agent budget ceiling baked into the generated workflow config, not left to runtime defaults
  - Hoko stays a provisioner, not a runtime: it never calls an LLM itself, only generates config for an existing runtime — scoped to one supported target initially rather than an abstract multi-runtime API
  - Team/org preset sharing beyond a local file (e.g. import by URL), plugin system for third-party hook capabilities
- **v1.0** — Stable plugin API (hook and agent capabilities), Windows Scoop package, GitHub Action wrapping `hoko check`, VS Code extension

### Removed: `fleet`

`hoko fleet` (multi-repo `doctor` rollup) shipped in 0.1.7 and has been pulled. It added a table/JSON renderer over `doctor` looped across paths — everything it did is reproducible today with `for r in $repos; do (cd "$r" && hoko doctor --json); done | jq -s .`. It also targeted a platform/org-audit persona nothing else in hoko serves, and inherited `doctor`'s current shallow health score. Revisit only once `doctor`'s score reflects real signal (see v0.2) and there's actual multi-repo demand — until then it's not worth the surface area.

## License

[MIT](LICENSE) © [Andrii S](https://github.com/andriisem)
