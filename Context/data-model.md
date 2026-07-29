# Data model

## Default paths

Config home defaults to `<Path.home()>/.ssh` (`--destination`) — e.g. `~/.ssh` on Linux or `%USERPROFILE%\.ssh` on Windows.

| Artifact | Default |
|----------|---------|
| Host DB | `<home>/.ssh/sshc_db.json` |
| SSH config | `<home>/.ssh/sshc_ssh_config` |
| Ansible inventory | `<home>/.ssh/sshc_ansible_inventory.json` |

Override via `--destination`, `--dbfile`, `--configfile`, `--inventoryfile` where the subcommand supports them.

**Safety:** Prefer sshc-specific filenames. Generating into the real OpenSSH `config` or a live Ansible inventory **overwrites** the target file.

## Host DB (`sshc_db.json`)

Document format (schema version 1):

```json
{
  "meta": {
    "schema_version": 1,
    "created_at": "2026-07-29T05:00:00+00:00",
    "created_with_sshc_version": "3.0.0",
    "updated_at": "2026-07-29T05:10:00+00:00",
    "updated_with_sshc_version": "3.0.0",
    "update_count": 3,
    "hosts_sha256": "<sha256 of canonical hosts JSON>"
  },
  "hosts": []
}
```

| Meta field | Notes |
|------------|--------|
| `schema_version` | DB document schema (currently `1`) |
| `created_at` | UTC ISO-8601 when the DB was first created / upgraded |
| `created_with_sshc_version` | sshc version at creation |
| `updated_at` | UTC ISO-8601 of last successful host mutation |
| `updated_with_sshc_version` | sshc version that performed the last mutation |
| `update_count` | Number of successful insert/update/delete writes (`0` at init) |
| `hosts_sha256` | SHA-256 of canonical JSON for `hosts` (integrity); verified on read |

- Empty DB: `hosts: []` with metadata (created by `init` / `mjdb.create_db()`).
- Unique host key: `name` (stored lowercase).
- **Legacy:** a bare JSON array of hosts is still readable; **`sshc init`** upgrades the file to the document format with metadata (hosts preserved); host mutations also upgrade on write.
- View metadata: `sshc read --verbose yes` (or `sshc list --verbose yes`).

### Host record

```json
{
  "id": "<uuid4>",
  "name": "<lowercase host alias>",
  "host": "<ip or dns>",
  "port": 22,
  "user": "root",
  "log_level": "INFO",
  "compression": "yes",
  "identityfile": "/home/user/.ssh/id_rsa",
  "comment": "optional note",
  "groups": ["personal", "home"]
}
```

| Field | Notes |
|-------|--------|
| `id` | Assigned on insert via `get_random_id()` |
| `name` | OpenSSH `Host` alias; Ansible host key |
| `host` | OpenSSH `HostName` / `ansible_host` |
| `port` | OpenSSH `Port` / `ansible_port` |
| `user` | OpenSSH `User` / `ansible_user` |
| `identityfile` | OpenSSH `IdentityFile` / `ansible_ssh_private_key_file` |
| `log_level` | OpenSSH `LogLevel`: INFO, DEBUG, ERROR, WARNING |
| `compression` | OpenSSH `Compression`: `yes` / `no` |
| `comment` | Written as `# Comment: ...` in SSH config |
| `groups` | Become Ansible inventory `children` |

## Generated SSH config

Header includes generation timestamp (UTC) and sshc version. Each host is wrapped in `# -- <` / `# -- >` markers with:

```
Host <name>
HostName <host>
Port <port>
User <user>
IdentityFile <identityfile>
LogLevel <log_level>
Compression <compression>
# Comment: <comment>
```

## Generated Ansible inventory

```json
{
  "all": {
    "hosts": {
      "<name>": {
        "ansible_host": "...",
        "ansible_port": 22,
        "ansible_user": "...",
        "ansible_ssh_private_key_file": "..."
      }
    },
    "children": {
      "<group>": {
        "hosts": {
          "<name>": null
        }
      }
    }
  },
  "others": {
    "generated_at": "<utc datetime str>",
    "sshc_version": "<version>"
  }
}
```

- `--filetype {json,yaml,yml}` controls serialization.
- Inventory path extension must match the chosen filetype or generate refuses.
