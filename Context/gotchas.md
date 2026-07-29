# Gotchas and known quirks

Read this before changing CLI args, paths, versioning, or platform-related code.

## Platform

Windows path support was delivered in **[ADJ-001](todo.md#adj-001--ensure-windows-support)** (`done`). Defaults use `pathlib.Path.home()` and `.ssh` under that home (e.g. `%USERPROFILE%\.ssh` on Windows).

1. **OpenSSH / Ansible on Windows** are optional consumers of generated files — install them separately if you need `ssh -F` / `ansible -i`.
2. Prefer the portable helpers (`get_home_dir`, `get_ssh_dir`, `default_*`) instead of reintroducing `os.getenv('HOME')` or hardcoded `/` joins.

## Resolved CLI / DB behaviors

These backlog items are **`done`** (see [todo.md](todo.md)):

- **BUG-001** — `delete` accepts `--destination` / `--dbfile`.
- **BUG-002** — Partial `update` only writes fields the user passed.
- **BUG-003** — Duplicate insert prints a skip message and returns `False`.
- **BUG-004** — `read_all_data` always returns a `list` (`[]` on error / invalid shape).
- **DOC-001** — README insert/generate examples match the real CLI.
- **TST-001** — Version test reads from `pyproject.toml`.

## Packaging / version

3. **Publish copies pyproject into `src/`.** Packaged version reads prefer `src/pyproject.toml`, then repo-root `pyproject.toml` via `Path` candidates.
4. **No `python -m` CLI.** No `__main__.py`; use Poetry script `sshc` or call `__main__` via the entry point.
5. **No committed lockfile.** `poetry.lock` is ignored.

## Operational safety

6. **Generate overwrites target files.** Never point `--configfile` / `--inventoryfile` at live defaults unless intentional. Prefer `sshc_ssh_config` and `sshc_ansible_inventory.*` with `ssh -F` / `ansible -i`.

## Contribution process

7. Open PRs against **`development`**, not only `main`.
