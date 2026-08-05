# Hoko

> **Developer workflows in one command.**

Hoko installs, configures, and maintains Git hooks and repository quality tooling. Instead of hand-editing `.pre-commit-config.yaml` or copy-pasting hook configs between repos, you install **capabilities** — `hoko add formatting` — and Hoko resolves the right tool for your project.

[![CI](https://github.com/andriisem/hoko/actions/workflows/ci.yml/badge.svg)](https://github.com/andriisem/hoko/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hoko.svg)](https://pypi.org/project/hoko/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

```bash
uv tool install hoko

cd my-project
hoko init                            # detect the project, wire up git hooks
hoko add python formatting secrets   # install capabilities, not tools
git commit                           # hooks run automatically
```

No YAML. No copy-paste. No setup guides.

---

## Why

Setting up repo quality checks today means installing `pre-commit`, hand-writing `.pre-commit-config.yaml`, finding and pinning the right hook repos, and repeating all of it in every project — then keeping every pin current, forever. Hoko replaces that with a small set of commands over **capabilities** (outcomes like `formatting`, `secrets`) instead of tool-specific YAML. Which tool that resolves to — Ruff, Prettier, gofmt — is Hoko's problem, not yours.

Design principles: convention over configuration, capabilities not tools, never hand-edit YAML, safe and idempotent, cross-platform.

## How it compares

Hoko is **not a replacement for pre-commit** — it's built directly on top of it, generating and merging `.pre-commit-config.yaml` for you. Husky solves an adjacent, narrower problem (wiring git hook events to scripts you already have) and is npm-specific.

| | Husky | pre-commit | Hoko |
|---|---|---|---|
| Choosing a tool | You decide and wire it up | You decide, then pin the hook repo/rev | Resolved per detected ecosystem |
| Cross-language repos | No | Yes | Yes |
| Keeping hooks current | Manual | `pre-commit autoupdate` by hand | `hoko update` |
| Health/audit | None | None built in | `hoko doctor` |
| Sharing a setup | Copy files by hand | Copy the YAML by hand | `hoko export` / `hoko import` |
| Config you hand-edit | Hook scripts | `.pre-commit-config.yaml` | None |

If you're already happy hand-writing and tracking pre-commit's YAML yourself, plain pre-commit is one less layer.

## Installation

Requires **Python 3.12+**.

```bash
uv tool install hoko   # recommended
pipx install hoko
pip install hoko
```

## Commands

| Command | Description |
|---|---|
| `hoko init [--yes]` | Detect the project, install `pre-commit` if missing, install recommended capabilities, wire up git hooks. |
| `hoko add [capability]...` | Install capabilities. No arguments opens an interactive picker. |
| `hoko rm [capability]...` | Remove capabilities. No arguments opens an interactive picker. |
| `hoko list` | List installed capabilities. |
| `hoko doctor [--fix] [--json]` | Score repo health (0–100); `--fix` repairs, `--json` for CI/dashboards. |
| `hoko update` | Update all managed hook versions. |
| `hoko check` | Run every configured hook without committing — for CI. |
| `hoko export [path]` | Write installed capabilities to a preset file. |
| `hoko import <path>` | Install every capability listed in a preset file. |
| `hoko --version` | Print the installed version. |

Every command takes `--help`. `hoko add`/`hoko rm` grey out what's already installed and require explicit arguments outside a terminal (CI, pipes). `hoko doctor --json` and `hoko check` are built for CI — see [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for a working example.

## Capabilities

| Capability | Purpose | Resolves to |
|---|---|---|
| `python` | Linting and type checking | Ruff, mypy |
| `formatting` | Code formatting | Ruff Formatter, Prettier, gofmt, rustfmt |
| `secrets` | Secret scanning | detect-secrets, gitleaks |
| `markdown` | Markdown linting | markdownlint |
| `yaml` | YAML linting | yamllint |
| `docker` | Dockerfile linting | hadolint |
| `commitlint` | Conventional commit messages | commitlint |

`hoko init` detects the project (`pyproject.toml`/`setup.py` → Python, `package.json` → JavaScript, `go.mod` → Go, `Cargo.toml` → Rust, `Dockerfile`, `.github/workflows/`) and recommends capabilities accordingly.

## Configuration

Hoko keeps its own state in `hoko.yaml`, separate from the generated `.pre-commit-config.yaml`:

```yaml
version: 1
capabilities: [python, formatting, secrets]
```

`.pre-commit-config.yaml` is always regenerated from this model — safe to delete and recreate via `hoko init`. Share a setup across repos with `hoko export team-preset.yaml` / `hoko import team-preset.yaml`.

## Architecture

```
CLI (Typer) → Command Layer → Capability Registry → Project Detection
   → Configuration Model (hoko.yaml) → Generators → pre-commit Adapter (.pre-commit-config.yaml)
```

Commands never hand-edit YAML directly — everything modifies the config model, which renders to `.pre-commit-config.yaml`.

## Development

```bash
git clone https://github.com/andriisem/hoko.git && cd hoko
uv sync
uv run hoko --help
uv run pytest
```

CI runs the test suite on Linux/macOS across Python 3.12–3.13. Releases publish to PyPI on tag. Open an issue before a significant PR.

## Roadmap

- **v0.1** — Core commands, capabilities, project detection, presets. *Shipped, 0.1.0–0.1.7.*
- **v0.2** — Hardening: deeper `doctor` checks, `hoko --version`, full CLI test coverage, `CHANGELOG.md`. *Shipped, current — 0.2.0.*
- **v0.3** — Agent capabilities: `hoko agent add <code-review|infra-review|docs|...>` provisions a scoped prompt, a least-privilege tool manifest, and CI trigger wiring per agent — the same capability model, aimed at agents instead of hooks. Hoko stays a provisioner, never a runtime. Plus team/org preset sharing and a hook-capability plugin system.
- **v1.0** — Stable plugin API, Windows Scoop package, GitHub Action, VS Code extension.

See [`CHANGELOG.md`](CHANGELOG.md) for what's actually shipped in each release, including what got pulled (e.g. `fleet`, cut in 0.2.0).

## License

[MIT](LICENSE) © [Andrii S](https://github.com/andriisem)
