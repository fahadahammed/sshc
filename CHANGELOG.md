# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Windows-friendly default paths via `pathlib.Path.home()` (typically `%USERPROFILE%\.ssh` on Windows).
- DB document format with metadata: `schema_version`, `created_at`, `created_with_sshc_version`, `updated_at`, `updated_with_sshc_version`, `update_count`, `hosts_sha256`.
- `sshc status` health check (integrity, empty DB, SSH config / Ansible inventory sync, identity-file presence, `needs_regeneration`) with `--json` and path overrides.
- `list` as an alias of `read`.
- `Context/` maintainer docs (architecture, CLI, data model, todo, gotchas).
- CI matrix runs on `ubuntu-latest` and `windows-latest`.
- Unit tests for portable paths, DB metadata, status, `list` alias, and empty-DB listing.

### Changed

- Host DB shape is now `{ "meta": {...}, "hosts": [...] }` (legacy bare JSON arrays remain readable).
- `sshc init` upgrades an existing legacy/incomplete DB in place and adds metadata without deleting hosts; no-ops when metadata is already complete.
- Partial `update` only applies fields that were explicitly passed.
- Verbose `read` / `list` prints DB metadata and hosts.
- README updated for Windows, metadata, status, and accurate CLI examples.

### Fixed

- `delete` accepts `--destination` and `--dbfile` (previously caused `AttributeError`).
- Duplicate `insert` prints a clear skip message and returns `False`.
- `read_all_data` always returns a `list` on error (never a `dict`).
- Empty-DB `read` / `list` no longer crashes on `max([])`.
- `cleanup_file` and `read_pyproject_toml` use portable path handling.
- Version unit test no longer hardcodes `0.3.0`.

## [0.3.0] - 2023-01

### Added

- `update` subcommand for modifying host entries.
- sshc version stamped into generated SSH config and Ansible inventory.
- GitHub Actions for pylint, unittest, CLI smoke tests, and PyPI publish on release.

### Changed

- Improved `read` command output formatting.

### Fixed

- Update path when host is missing: insert-check refactor and missing-data handling ([#18](https://github.com/fahadahammed/sshc/issues/18) / PR #19).

## [0.2.0] - prior

### Added

- Core CLI: `init`, `insert`, `delete`, `read`, `generate`.
- JSON host database with SSH config and Ansible inventory generation (JSON/YAML).
- Poetry packaging and PyPI distribution as `sshc`.

[Unreleased]: https://github.com/fahadahammed/sshc/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/fahadahammed/sshc/releases/tag/v0.3.0
[0.2.0]: https://github.com/fahadahammed/sshc/releases/tag/v0.2.0
