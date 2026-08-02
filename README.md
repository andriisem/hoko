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
| `hoko doctor` | Scores repository health (0–100) and flags issues such as missing hooks or stale configuration. |
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

- **v0.1** — `init`, `add`, `rm`, `list`, `doctor`, `update`, `check`, `export`, `import`; Python/JavaScript/Go/Rust formatting, Python lint, secrets, markdown, yaml, docker, commitlint; interactive capability selection; preset export/import *(current — 0.1.6, published on PyPI)*
- **v0.2** — Hardening: CLI-level tests for `doctor`/`check`/`export`/`import`/`update`, a `doctor` score that reflects per-capability staleness rather than 3 fixed checks, `hoko --version`, standardized `vX.Y.Z` release tags, a `CHANGELOG.md`, and a published (not just drafted) Homebrew formula
- **v0.3** — Team/org preset sharing beyond a local file, plugin system for third-party capabilities
- **v1.0** — Stable plugin API, Windows Scoop package, GitHub Action, VS Code extension

## License

[MIT](LICENSE) © [Andrii S](https://github.com/andriisem)
