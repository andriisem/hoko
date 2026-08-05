# Hoko

> **Developer workflows in one command.**

Hoko is a CLI that installs, configures, and maintains Git hooks and repository quality tools with sensible defaults.

Instead of manually editing `.pre-commit-config.yaml`, copying YAML between repositories, or remembering which tools to install, developers simply install **capabilities**.

```bash
hoko init

hoko add python
hoko add formatting
hoko add secrets

git commit
```

No YAML.

No copy-paste.

No setup guides.

---

# Vision

Every repository should have high-quality checks with almost zero effort.

Developers shouldn't need to know:

* which formatter to install
* which secret scanner is best
* how to configure pre-commit
* how to update hook versions
* how to merge YAML files

Hoko handles that automatically.

---

# Core Principles

* Convention over configuration.
* Install capabilities, not tools.
* Never require editing YAML manually.
* Safe and idempotent.
* Cross-platform.
* Plugin-based architecture.
* Excellent developer experience.

---

# The Problem

Today every repository repeats the same setup:

* Install `pre-commit`
* Create `.pre-commit-config.yaml`
* Search GitHub for hook repositories
* Copy configuration
* Install hooks
* Keep versions updated
* Repeat in the next repository

This process is slow, inconsistent, and error-prone.

---

# The Solution

Instead of configuring tools directly:

```bash
hoko add formatting
```

Hoko determines the appropriate formatter based on the project.

Python

→ Ruff Formatter

JavaScript

→ Prettier

Go

→ gofmt

Rust

→ rustfmt

The developer installs a capability, not an implementation.

---

# Commands

## Initialize

```bash
hoko init
```

Creates and configures everything required.

* installs pre-commit (if missing)
* creates `.pre-commit-config.yaml`
* installs Git hooks
* safely merges existing configuration

---

## Add

```bash
hoko add python

hoko add formatting

hoko add secrets

hoko add markdown

hoko add yaml

hoko add docker

hoko add commitlint
```

Hoko installs dependencies and updates configuration automatically.

Run it without arguments to choose from an interactive, multi-select list of
every capability. Already installed ones are shown but not selectable.

```bash
hoko add
```

---

## Remove

```bash
hoko rm formatting
```

Safely removes a capability. Like `add`, running it without arguments opens an
interactive multi-select list — of the installed capabilities only.

```bash
hoko rm
```

---

## List

```bash
hoko list
```

Example

```
Installed

✓ Python
✓ Formatting
✓ Secrets
✓ Markdown
```

---

## Doctor

```bash
hoko doctor
hoko doctor --fix
hoko doctor --json
```

Example

```
Repository Health

66 / 100

✓ pre-commit available

✓ Hooks installed

⚠ Configuration valid

Recommendation

hoko doctor --fix
```

`--fix` reapplies the stored capabilities through the same idempotent path
`init`/`add`/`import` already use, then re-reports the score.

`--json` prints only a single JSON object (`score`, `capabilities`,
`fix_attempted`, `checks`) — no other output, so it's safe to pipe into `jq`
or a dashboard. Combine it with `--fix` to repair and report in one call.

---

## Update

```bash
hoko update
```

Updates all managed hook versions.

---

## Check

```bash
hoko check
```

Runs all configured hooks without creating a commit.

Useful for CI.

---

## Export

```bash
hoko export
```

Produces

```yaml
version: 1

capabilities:

  - python
  - formatting
  - secrets
```

---

## Import

```bash
hoko import hoko.yaml
```

Installs everything from a preset.

---

# Automatic Project Detection

Hoko inspects the repository.

If it finds

```
pyproject.toml
```

recommend Python capabilities.

If it finds

```
package.json
```

recommend JavaScript capabilities.

If it finds

```
go.mod
```

recommend Go capabilities.

If it finds

```
Cargo.toml
```

recommend Rust capabilities.

---

# Interactive Setup

```
hoko init
```

Output

```
Detected

✓ Python
✓ Docker
✓ GitHub Actions

Install recommended capabilities?

✓ Formatting
✓ Secrets
✓ YAML
✓ Docker

Continue?
```

---

# Capability Model

Instead of exposing tools, Hoko exposes capabilities.

Examples

```
formatting
```

May install

* Ruff Formatter
* Prettier
* gofmt
* rustfmt

depending on the project.

---

```
secrets
```

May install

* detect-secrets
* gitleaks

---

```
python
```

May install

* Ruff
* mypy

---

```
markdown
```

May install

* markdownlint

The implementation can evolve without changing the user-facing interface.

---

# Architecture

```
CLI

↓

Command Layer

↓

Capability Registry

↓

Project Detection

↓

Configuration Model

↓

Generators

↓

pre-commit Adapter
```

Commands should never edit YAML directly.

Everything modifies an internal configuration model, which is then rendered to `.pre-commit-config.yaml`.

---

# Repository Structure

```
hoko/

    cli/

    commands/

        init.py
        add.py
        rm.py
        list.py
        doctor.py
        update.py
        check.py
        export.py
        import_.py

    capabilities/

    detection/

    generators/

    ui/

        prompts.py

    adapters/

        precommit.py

    config/

tests/
```

---

# Technology

Language

Python 3.12+

Framework

Typer

Libraries

* Rich
* Pydantic
* ruamel.yaml
* platformdirs
* pytest

Package manager

uv

Distribution

PyPI

Installation

```
uv tool install hoko
```

or

```
pipx install hoko
```

Future

```
brew install hoko
```

---

# Roadmap

## Shipped — v0.1 (current, 0.1.7, published on PyPI)

* `init`, `add`, `rm`, `list`, `doctor`, `update`, `check`, `export`, `import`
* Capabilities: `python`, `formatting` (Python/JS/Go/Rust), `secrets`, `markdown`, `yaml`, `docker`, `commitlint`
* Automatic project detection (Python, JavaScript, Go, Rust, Docker, GitHub Actions)
* Interactive multi-select for `add`/`rm`
* Preset export/import
* Homebrew formula drafted (not yet published to a tap — real release sha256 still a placeholder)

### Removed: `fleet`

`hoko fleet` (multi-repo `doctor` rollup, shipped 0.1.7) has been pulled. It
was `doctor` looped over a path list with a table/JSON renderer on top —
reproducible today with
`for r in $repos; do (cd "$r" && hoko doctor --json); done | jq -s .`. It
also targeted a platform/org-audit persona nothing else in hoko serves, and
inherited `doctor`'s current shallow health score (see v0.2 below).
Revisit only once `doctor`'s score reflects real signal and there's actual
multi-repo demand.

---

## v0.2 — Hardening

* CLI-level tests for `doctor`, `check`, `export`, `import`, `update` — today they're only exercised indirectly through the `precommit` adapter tests, not through `CliRunner`
* Deepen `doctor`'s health score: it currently checks three fixed things (pre-commit present, hooks installed, config file exists) but doesn't detect stale hook revisions, missing companion configs (e.g. `.commitlintrc.yaml`), or a missing `commit-msg` hook for capabilities that need one
* `hoko --version`, backed by a single source of truth for the version string (today it's hand-duplicated in `pyproject.toml` and `hoko/__init__.py`)
* Standardize release tags on `vX.Y.Z` — history mixes `0.1.2`, `v.0.1.2`, and `v0.1.6`
* `CHANGELOG.md`
* Finish the Homebrew formula: real release sha256, submitted to a tap

---

## v0.3 — Agent capabilities & extensibility

Extend the capability model from git hooks to per-project review agents,
without hoko becoming an agent runtime — it provisions config the same way
it provisions `.pre-commit-config.yaml` today; it never calls an LLM itself.

* `hoko agent add <name>` / `hoko agent rm` / `hoko agent list` — a separate
  namespace from hook capabilities, same interaction model as
  `hoko add`/`rm`/`list` (including interactive multi-select)
* Agent capability registry to start: `code-review`, `infra-review` (IaC),
  `docs`, `dependency-audit`
* Each agent capability resolves to three generated artifacts, mirroring how
  `formatting` resolves to a concrete pre-commit hook per ecosystem:
  * a scoped system prompt / instructions file
  * a least-privilege tool/permission manifest (e.g. `code-review` gets
    read-only diff access, no shell or network)
  * trigger wiring — a PR-opened GitHub Actions workflow first, a git hook
    as a secondary trigger
* New `hoko/adapters/agent_ci.py`: generates and merges a GitHub Actions
  workflow YAML non-destructively, the same principle `precommit.py`
  already applies to `.pre-commit-config.yaml`
* A per-agent budget ceiling baked into the generated workflow config, not
  left to the runtime's defaults
* Repo content an agent reads (README, comments, issue text) is treated as
  untrusted data, never as instructions — the standard prompt-injection
  guard for anything that ingests repo text
* Ship against one supported runtime target first rather than an abstract
  multi-runtime API; document the coupling instead of hiding it
* Team/org preset sharing beyond a local file (e.g. import by URL)
* Plugin system for third-party hook capabilities

---

## v1.0

* Stable plugin API (hook and agent capabilities)
* Windows Scoop package
* GitHub Action wrapping `hoko check`
* VS Code extension

---

# Success Criteria

A developer should be able to create a production-ready hook setup in under one minute.

Example

```bash
uv tool install hoko

cd my-project

hoko init

hoko add formatting secrets

git commit
```

No documentation.

No YAML editing.

No copy-paste.

Just install capabilities and keep shipping.

---

# Long-Term Vision

Today, Hoko manages **pre-commit**.

Tomorrow, it can manage:

* pre-push hooks
* commit-msg hooks
* repository standards
* GitHub Actions checks
* CI quality policies
* organization-wide presets

The user interface should stay the same:

```bash
hoko add <capability>
```

Developers think about **what they want to achieve**, not which underlying tool they need to configure.
