# Architecture

## Repository layout

```
sshc/
├── .github/workflows/
│   ├── test_code_and_functionality.yaml      # lint + unittest + CLI smoke
│   └── python-package-pypi-build-publish.yaml # release → PyPI
├── Context/                                  # this documentation
├── src/
│   ├── __init__.py                           # empty
│   └── sshc.py                               # entire application (~473 lines)
├── tests/
│   ├── __init__.py                           # empty
│   └── basic-function-test.py
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

There is no multi-package layout, no `__main__.py`, and no separate library API beyond the CLI.

## Packaging / entry point

From `pyproject.toml`:

```toml
packages = [{ include = "src/*" }]

[tool.poetry.scripts]
sshc = 'src.sshc:__main__'
```

- Installed command: `sshc`
- Import path used by Poetry/tests: `src.sshc` (not a top-level `sshc` package)
- CLI lives in function `__main__()` inside `src/sshc.py` (name is the entry symbol, not a `__main__.py` module)
- There is no `if __name__ == "__main__"` guard; run via the Poetry script or by calling `__main__`

## Module map (`src/sshc.py`)

| Symbol | Role |
|--------|------|
| `get_random_id()` | UUID4 string for host `id` |
| `get_home_dir()` / `get_ssh_dir()` | Portable home and `<home>/.ssh` via `pathlib` |
| `default_destination()` / `default_db_file()` / `default_identity_file()` / `default_ssh_config_file()` / `default_inventory_file()` | CLI default paths (no `HOME` env dependency) |
| `read_pyproject_toml()` | Read `version` from `pyproject.toml` beside the module or repo root |
| `mjdb` | JSON-file “database” CRUD |
| `mjdb.create_db()` | Create empty document `{meta, hosts: []}` if missing |
| `mjdb.insert_data(data)` | Append host if `name` unique; assign `id`; bump meta |
| `mjdb.update_data(data)` | Merge fields onto existing host; single rewrite + meta bump |
| `mjdb.read_data(hostname)` | Lookup by `name` |
| `mjdb.delete_data(hostname)` | Remove matching `name`; rewrite + meta bump |
| `mjdb.read_all_data()` | Return `hosts` list; warn if `hosts_sha256` mismatches |
| `mjdb.read_meta()` / `load_document()` | Metadata / full document (legacy array supported) |
| `compute_hosts_sha256(hosts)` | Canonical SHA-256 of hosts payload |
| `cleanup_file(configfile)` | Remove/recreate SSH config before regenerate |
| `generate_host_entry_string(...)` | Append one OpenSSH `Host` block |
| `generate_ansible_inventory_file(...)` | Write inventory as JSON or YAML |
| `__main__()` | argparse + command dispatch |

## Data flow

```
┌─────────────┐     CRUD      ┌──────────────────┐
│  CLI args   │ ────────────► │  sshc_db.json    │
└─────────────┘               └────────┬─────────┘
                                       │ read_all
                                       ▼
                              ┌──────────────────┐
                              │     generate     │
                              └────────┬─────────┘
                     ┌─────────────────┴─────────────────┐
                     ▼                                   ▼
            sshc_ssh_config                   sshc_ansible_inventory.*
            (OpenSSH blocks)                  (JSON or YAML inventory)
```

## Design style

- Procedural CLI with one lowercase-named class (`mjdb`).
- Broad `try/except Exception` with print + `False`/`{}` returns in many paths.
- Host names are lowercased on insert/delete/update.
- Generate always rebuilds artifacts from the full DB (not incremental patch).
