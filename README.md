# sshc

**SSH config and Ansible inventory from one host database.**

[sshc](https://github.com/fahadahammed/sshc) stores your servers in a JSON database under `~/.ssh`, then generates OpenSSH config and Ansible inventory from that single source of truth. Works on **Linux and Windows**.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Features

- One JSON DB for all hosts (names, IPs, users, keys, groups, comments).
- DB **metadata** and **SHA-256** integrity checksum on the hosts payload.
- Generate `sshc_ssh_config` and `sshc_ansible_inventory.json` (or YAML).
- **`sshc status`** — check integrity, drift vs generated files, missing keys.
- **`sshc list`** — alias of `read`; optional verbose metadata output.
- Optional **`Include`** in your default `~/.ssh/config` so `ssh <host>` works without `-F`.
- Safe **`generate`** — confirms before overwriting existing artifacts (`-y` to skip).

## Installation

```shell
pip3 install sshc --upgrade
```

**From source (development):**

```shell
git clone https://github.com/fahadahammed/sshc.git
cd sshc
poetry install
poetry run sshc --version
```

Release notes: [CHANGELOG.md](CHANGELOG.md).

## Quick start

```shell
sshc init
sshc insert --name web1 --host 192.168.0.10 --user ubuntu --groups web prod
sshc generate
sshc list
sshc status
```

Use generated files:

```shell
ssh -F ~/.ssh/sshc_ssh_config web1
ansible -i ~/.ssh/sshc_ansible_inventory.json all --list-hosts
```

On Windows (PowerShell):

```powershell
ssh -F $env:USERPROFILE\.ssh\sshc_ssh_config web1
```

## Default paths

| Artifact | Path |
|----------|------|
| Host DB | `<home>/.ssh/sshc_db.json` |
| SSH config (generated) | `<home>/.ssh/sshc_ssh_config` |
| Ansible inventory | `<home>/.ssh/sshc_ansible_inventory.json` |
| OpenSSH default config | `<home>/.ssh/config` (optional Include only) |

`<home>` is your user profile directory (`$HOME` or `%USERPROFILE%`).

## Commands

| Command | Description |
|---------|-------------|
| `init` | Create or upgrade the host DB (adds metadata to legacy files). |
| `insert` | Add a host (unique `name`; skipped if duplicate). |
| `update` | Change only fields you pass; insert if name is new. |
| `delete` | Remove a host by name. |
| `read` / `list` | Show hosts; `--verbose yes` includes DB metadata. |
| `generate` | Rebuild SSH config and Ansible inventory from the DB. |
| `status` | Health check; `--json` for automation. |

Global: `sshc --version`, `sshc --help`.

Most subcommands accept `--destination`, `--dbfile`, and generate/status also accept `--configfile` / `--inventoryfile`.

### `init`

Creates `{ "meta": {...}, "hosts": [] }`. If the file already exists as a legacy JSON array, **`init` upgrades it in place** and keeps existing hosts.

```shell
sshc init
```

### `insert`

```shell
sshc insert --name myserver --host 10.0.0.5 --user deploy \
  --port 22 --groups app staging --comment "staging app"
```

Groups are **space-separated**. Default user is `root`; default key path is `<home>/.ssh/id_rsa`.

### `generate`

Rebuilds artifacts from the DB (full replace of generated content).

```shell
sshc generate
sshc generate -y
sshc generate --include-default-config
sshc generate --filetype yaml --inventoryfile ~/.ssh/sshc_ansible_inventory.yml
```

- **Confirmation:** if SSH config or inventory already have content, you are prompted (`Overwrite? [y/N]:`). Use **`-y` / `--yes`** in scripts.
- **Include in default SSH config:** `--include-default-config` adds a managed block to `<home>/.ssh/config` pointing at `sshc_ssh_config` so you can run `ssh <hostname>` without `-F`. Your main `config` is not overwritten—only an `Include` block is added or updated.
- Prefer **`sshc_ssh_config`** over writing directly to `config` so personal SSH settings stay separate.

### `status`

```shell
sshc status
sshc status --json
```

Exit code `0` when healthy (warnings allowed); `1` when regeneration is required or integrity fails.

### `update` / `delete` / `read`

```shell
sshc update --name myserver --port 2222
sshc delete --hostname myserver
sshc list --verbose yes
```

## Example output

<details>
<summary>Generated SSH config (excerpt)</summary>

```ini
# Generated At: 2023-01-24 11:35:25.885044
# sshc Version: 3.0.0

# -- <
Host server1
HostName 192.168.0.100
Port 22
User ubuntu
IdentityFile /home/user/.ssh/id_rsa
LogLevel INFO
Compression yes
# Comment: Personal Server: ONE
# -- >
```

</details>

<details>
<summary>Generated Ansible inventory (excerpt)</summary>

```json
{
  "all": {
    "hosts": {
      "server1": {
        "ansible_host": "192.168.0.100",
        "ansible_port": 22,
        "ansible_user": "ubuntu",
        "ansible_ssh_private_key_file": "/home/user/.ssh/id_rsa"
      }
    },
    "children": {
      "personal": { "hosts": { "server1": null } }
    }
  },
  "others": {
    "generated_at": "2023-01-24 11:35:25.885044",
    "sshc_version": "3.0.0"
  }
}
```

</details>

## Requirements

- **Runtime:** Python 3.7+, [PyYAML](https://pypi.org/project/PyYAML/) (installed with the package).
- **Platforms:** Linux and Windows for sshc itself; **OpenSSH** and **Ansible** are separate installs used to consume generated files.

## Contributing

Contributions are welcome—bug reports, docs, tests, and features.

1. **Fork** the repository and create a branch from **`development`** (not `main`).
2. **Set up** locally: `poetry install`, then `poetry run python -m unittest tests/basic-function-test.py`.
3. **Change** the smallest scope that fixes the issue; match existing style in `src/sshc.py`.
4. **Document** user-visible behavior in `README.md` and add an entry under **`[Unreleased]`** in [CHANGELOG.md](CHANGELOG.md).
5. **Open a pull request** to `development` with a clear description and how you tested (OS, commands run).

Maintainer-oriented design notes live in the [`Context/`](Context/) directory (architecture, CLI, data model, gotchas).

- **Questions or bugs:** [GitHub Issues](https://github.com/fahadahammed/sshc/issues)
- **License:** [MIT](LICENSE)

Thank you for helping improve sshc.

## Author

[Fahad Ahammed](https://github.com/fahadahammed) — DevOps enthusiast, Dhaka, Bangladesh.
