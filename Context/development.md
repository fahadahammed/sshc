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
python -m unittest tests/basic-function-test.py
```

## Tests

File: `tests/basic-function-test.py`

| Area | What it covers |
|------|----------------|
| Basic | Missing DB → `SystemExit`; version from `pyproject.toml` (not hardcoded) |
| Portable paths | `Path.home()`-based defaults; no `$HOME` env dependency; Windows/Posix pure-path shapes |
| `cleanup_file` | Removes existing file; tolerates missing file on native temp paths |
| Workflow | `create_db` → insert → generate SSH/inventory → delete on OS-native temp dirs |
| Duplicate insert | Skip + message; returns `False`; DB unchanged |
| Partial update | Only provided fields change; other fields preserved |
| `read_all_data` errors | Invalid JSON / non-list JSON → `[]` |

## CI / CD

### Lint + tests — `.github/workflows/test_code_and_functionality.yaml`

- Triggers: push to `main`, `development`, `GITHUB_ACTIONS`
- Matrix OS: `ubuntu-latest`, `windows-latest` (Python 3.9)
- **Lint_Unittest:** pylint on Ubuntu only; unittest on both OSes
- **Command_Test:** `poetry install`, then `sshc --version`, `--help`, `init` on both OSes

### Publish — `.github/workflows/python-package-pypi-build-publish.yaml`

- Trigger: GitHub release `published`
- Runs lint + command jobs, then **Build_Publish**:
  - Sets `version` in `pyproject.toml` from release tag
  - Copies `pyproject.toml` → `src/pyproject.toml` (needed for packaged installs)
  - `poetry build` / `poetry publish` with `PYPI_API_TOKEN`

Actions still use `actions/checkout@v2` and `actions/setup-python@v2`.

## Versioning

- Source of truth for local/dev: root `pyproject.toml` → `version`
- Runtime `--version` uses `read_pyproject_toml()` (module-dir then repo-root candidates via `Path`)
- Release workflow overwrites version from the git tag before publish

## Contributing conventions

From README:

- PRs should target the **`development`** branch (not only `main`).
- Prefer clearer comments when changing behavior.
- Include better comments for readability.

## Coding patterns to preserve

- Keep CLI dispatch in `__main__()` unless intentionally splitting modules.
- Host identity key is DB field `name`; delete CLI flag is `--hostname`.
- Use portable path helpers (`get_home_dir`, `default_*`) — do not use `os.getenv('HOME')` or hardcoded `/`.
- Lowercase host names on write paths.
- Generate is full rebuild, not patch.
- Prefer sshc default output paths over overwriting real SSH/Ansible defaults in docs and examples.
