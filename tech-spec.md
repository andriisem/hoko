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
or an org-wide dashboard. Combine it with `--fix` to repair and report in one
call, useful for fleet-wide policy checks across many repos.

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

## Fleet

```bash
hoko fleet ~/dev/service-a ~/dev/service-b
hoko fleet ~/dev/service-a ~/dev/service-b --fix
hoko fleet ~/dev/service-a ~/dev/service-b --json
```

Runs the same health check `doctor` runs — and, with `--fix`, the same
repair — against each repo directory given, then reports a rollup: a table by
default, or with `--json` a single object shaped
`{"repos": [...], "summary": {"count", "healthy", "errors"}}`, where each
repo entry matches `doctor --json`'s shape (or `{"path", "error"}` if the
path doesn't exist or isn't a git repository).

Implementation note: hoko's config loading and health checks are
cwd-relative by design — a single repo is always "the current directory" —
so `fleet` reuses that logic unchanged by hopping into each repo directory
in turn (restoring the original working directory afterward) rather than
threading a root path through every layer of the precommit adapter.

This is the building block for org-wide policy checks: point it at every
repo in an org (however that list is obtained — a config file, a shell
glob, or eventually a discovery step against the GitHub API) and the score
gives you compliance evidence without hand-checking each one.

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
        fleet.py

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

## Shipped — v0.1 (current, 0.1.6, published on PyPI)

* `init`, `add`, `rm`, `list`, `doctor`, `update`, `check`, `export`, `import`
* Capabilities: `python`, `formatting` (Python/JS/Go/Rust), `secrets`, `markdown`, `yaml`, `docker`, `commitlint`
* Automatic project detection (Python, JavaScript, Go, Rust, Docker, GitHub Actions)
* Interactive multi-select for `add`/`rm`
* Preset export/import
* Homebrew formula drafted (not yet published to a tap — real release sha256 still a placeholder)

---

## v0.2 — Hardening

* CLI-level tests for `doctor`, `check`, `export`, `import`, `update` — today they're only exercised indirectly through the `precommit` adapter tests, not through `CliRunner`
* Deepen `doctor`'s health score: it currently checks three fixed things (pre-commit present, hooks installed, config file exists) but doesn't detect stale hook revisions, missing companion configs (e.g. `.commitlintrc.yaml`), or a missing `commit-msg` hook for capabilities that need one
* `hoko --version`, backed by a single source of truth for the version string (today it's hand-duplicated in `pyproject.toml` and `hoko/__init__.py`)
* Standardize release tags on `vX.Y.Z` — history mixes `0.1.2`, `v.0.1.2`, and `v0.1.6`
* `CHANGELOG.md`
* Finish the Homebrew formula: real release sha256, submitted to a tap

---

## v0.3 — Presets & extensibility

* Team/org preset sharing beyond a local file (e.g. import by URL)
* Plugin system for third-party capabilities

---

## v1.0

* Stable plugin API
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
