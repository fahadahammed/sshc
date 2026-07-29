# Development

## Tooling

| Concern | Tool |
|---------|------|
| Package / scripts | Poetry (`pyproject.toml`) |
| Runtime dep | `pyyaml ^6.0` |
| Dev dep | `poetry ^1.3.2` (dev group) |
| Lint (CI) | pylint (`--exit-zero`) |
| Tests | `unittest` |

`poetry.lock` is gitignored — lockfiles are not committed; installs can drift.

## Local setup

```shell
poetry install
poetry run sshc --help
poetry run python -m unittest tests/basic-function-test.py
```

## Tests

File: `tests/basic-function-test.py`

| Area | What it covers |
|------|----------------|
| Basic | Missing DB → `SystemExit`; version from `pyproject.toml` |
| Portable paths | `Path.home()`-based defaults; Windows/Posix shapes |
| DB metadata | `meta`, checksum, legacy upgrade, mutations |
| `cleanup_file` | Portable file removal |
| Workflow | CRUD + generate helpers on temp paths |
| Duplicate insert / partial update | BUG fixes |
| `list` / `read` CLI | Alias + empty DB |
| `status` | Integrity, sync, JSON CLI |
| OpenSSH Include | `update_openssh_config_include` |
| Generate confirm | `confirm_overwrite`, `-y` behavior |

## CI / CD

### Lint + tests — `.github/workflows/test_code_and_functionality.yaml`

- Triggers: push to `main`, `development`, `GITHUB_ACTIONS`
- Matrix OS: `ubuntu-latest`, `windows-latest` (Python 3.9)
- **Lint_Unittest:** pylint on Ubuntu only; unittest on both OSes
- **Command_Test:** `poetry install`, then `sshc --version`, `--help`, `init` on both OSes

### Publish — `.github/workflows/python-package-pypi-build-publish.yaml`

- Trigger: GitHub release `published`
- Sets `version` from release tag; copies `pyproject.toml` → `src/pyproject.toml`; `poetry publish`

## Versioning

- Local: root `pyproject.toml` → `version`
- CLI: `read_pyproject_toml()` (module dir, then repo root)
- User-facing history: [CHANGELOG.md](../CHANGELOG.md) — add **`[Unreleased]`** entries for every user-visible change

## Contributing (maintainers)

Align with [README.md](../README.md#contributing):

- PRs target **`development`**
- Run unit tests on Linux and/or Windows before opening PR
- Update README + CHANGELOG for CLI/behavior changes
- Use `Context/` for deeper design notes; keep `src/sshc.py` conventions

## Coding patterns to preserve

- CLI dispatch in `__main__()` unless splitting modules intentionally.
- Host key: DB field `name`; delete flag `--hostname`.
- Portable paths: `get_home_dir`, `default_*` — not `os.getenv('HOME')`.
- Lowercase host names on write paths.
- `generate` is full rebuild; confirm before overwriting non-empty artifacts.
- Prefer `sshc_ssh_config` + optional `Include` over overwriting OpenSSH `config`.
