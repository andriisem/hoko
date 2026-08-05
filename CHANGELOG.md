# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project
follows [Semantic Versioning](https://semver.org/).

This file starts at v0.2.0 — the releases below it (`v0.1.0`–`v0.1.7`) are
reconstructed from git history for reference. From v0.2.0 on, generate new
entries with the changelog-generator skill's
`scripts/generate_changelog.py` against the commit range since the last
tag, rather than writing them by hand.

## [Unreleased]

### Added

- `hoko --version`, backed by a single source of truth for the version
  string (`hoko/__init__.py` now reads it from installed package metadata
  instead of duplicating the value from `pyproject.toml`)
- `doctor` checks every required git hook type, not just `pre-commit` — a
  repo with `commitlint` installed but a missing `commit-msg` hook now
  correctly fails instead of reporting "Hooks installed ✓"
- `doctor` flags a managed hook pinned to a rev older than hoko's bundled
  default ("Hook versions current")
- `doctor` flags a missing `.commitlintrc.yaml` (or equivalent) when the
  `commitlint` capability is installed ("Commitlint config present")
- CLI-level (`CliRunner`) tests for `check`, `export`, `import`, `update` —
  previously only exercised indirectly through the `precommit` adapter
  tests

### Changed

- `precommit._merge_repos` now never downgrades a managed repo's pinned rev:
  if `pre-commit autoupdate` (via `hoko update`) has already moved a rev
  ahead of hoko's bundled default, regenerating `.pre-commit-config.yaml`
  (e.g. via `hoko doctor --fix`) preserves it instead of reverting to the
  older bundled pin

### Fixed

- `hoko import <missing-file>` used to silently succeed with an empty
  `hoko.yaml` instead of failing; it now errors immediately if the preset
  file doesn't exist

### Removed

- `hoko fleet` — multi-repo `doctor` rollup, shipped in v0.1.7 and pulled
  before it saw real use (see the README's "Removed: `fleet`" note for why)

## [v0.1.7] - 2026-08-02

### Added

- `hoko doctor --fix` / `--json`
- `hoko fleet <repo>...` — later removed, see Unreleased

## [v0.1.6] - 2026-08-02

### Changed

- Version bump and Homebrew formula URL update
- Removed the hidden `remove` alias for `rm`

## [v0.1.5] - 2026-08-02

### Added

- Interactive capability selection (multi-select) for `hoko add` and
  `hoko rm` when run without arguments
- commitlint configuration for the repo itself, plus a generated-config
  test

## [v.0.1.4] - 2026-08-02

### Changed

- Improved pre-commit hook installation and configuration management
  (more reliable `pre-commit` binary resolution across pipx/uv/Homebrew
  installs)

## [0.1.3] - 2026-08-02

### Changed

- Version bump; Homebrew formula upkeep

## [v.0.1.2] / [0.1.2] - 2026-08-02

### Added

- `fix: show available capabilities and enable tab-completion for hoko add`

### Changed

- README rewritten as public-facing docs; CI workflow added
- Version bump (tagged twice under two different tag-naming conventions —
  see "Standardize release tags" below)

## [v.0.1.1] - 2026-08-02

### Changed

- Improved pre-commit integration: command resolution and installation
  checks

## [v0.1.0] - 2026-08-02

### Added

- Initial `hoko` CLI package scaffold
- Pre-commit hook repo/rev registry
- Merging hoko-managed hooks into an existing `.pre-commit-config.yaml`
  without clobbering hand-added entries
- Interactive capability recommendations in `hoko init`
- MIT license
- Publish-to-PyPI GitHub Actions workflow, triggered on release

---

**A note on tag naming:** early history mixes `0.1.2`, `v.0.1.2`, and
`v0.1.6`-style tags. Every tag from `v0.1.5` onward follows `vX.Y.Z`; that's
now the standing convention going forward. The inconsistent early tags are
left as-is rather than rewritten, since they're already public.
