# CLI reference

Entry: `src.sshc:__main__` → function `__main__()`.

```
sshc [-h] [--version] {init,insert,delete,update,read,generate,status} ...
```

`list` is an alias of `read` (`sshc list` ≡ `sshc read`).

## Commands

| Command | Purpose | Core implementation |
|---------|---------|---------------------|
| `init` | Ensure destination dir; create empty DB | `mjdb.create_db()` |
| `insert` | Add a host (name must be unique) | `mjdb.insert_data()` |
| `delete` | Remove host by name | `mjdb.delete_data()` |
| `update` | Merge fields onto existing host; insert if missing | `mjdb.update_data()` / `insert_data()` |
| `read` / `list` | Print DB (optional hostname filter / verbose) | `mjdb.read_all_data()` |
| `generate` | Rebuild SSH config + Ansible inventory | `cleanup_file`, `generate_host_entry_string`, `generate_ansible_inventory_file` |
| `status` | Health check: integrity, emptiness, sync, identity files | `collect_status` |

## Common options

Shared across most mutating commands (where defined on the subparser):

| Option | Meaning |
|--------|---------|
| `--destination` | Config home (default `<Path.home()>/.ssh`) |
| `--dbfile` | DB path (default `<home>/.ssh/sshc_db.json`) |

## `init`

```
sshc init [--destination DESTINATION] [--dbfile DBFILE]
```

## `insert`

Required: `--name`, `--host`.

Notable defaults:

- `--user` → `root`
- `--port` → `22`
- `--identityfile` → `<home>/.ssh/id_rsa`
- `--groups` → `nargs='+'` (space-separated group names)
- `--loglevel` ∈ `{INFO,DEBUG,ERROR,WARNING}`
- `--compression` ∈ `{yes,no}`

Host `name` is lowercased before insert.

## `delete`

```
sshc delete --hostname NAME [--destination DESTINATION] [--dbfile DBFILE]
```

## `update`

Requires `--name`. Other fields are optional and **only overwrite when explicitly passed** (no default injection on partial update).

If the host is missing, update falls through to insert and then requires `--host` and `--port` (insert defaults apply for other omitted fields).

## `read` / `list`

```
sshc read [--hostname NAME] [--verbose yes]
sshc list [--hostname NAME] [--verbose yes]
```

`list` is registered as an argparse alias of `read`; behavior is identical.
With `--verbose yes`, output includes DB `meta` then the hosts list.

## `status`

```
sshc status [--destination DESTINATION] [--dbfile DBFILE]
            [--configfile CONFIGFILE] [--inventoryfile INVENTORYFILE]
            [--json]
```

Reports:

- DB exists / valid / legacy / empty / host count / meta summary
- `hosts_sha256` match
- SSH config and Ansible inventory presence + content sync vs DB
- Missing identity files on disk (warnings)
- `needs_regeneration` when hosts exist but generated files are missing or out of sync

Exit `1` on error-level issues; warnings alone exit `0`. `--json` prints the full report object.

## `generate`

```
sshc generate [--configfile PATH] [--inventoryfile PATH]
              [--destination DESTINATION] [--dbfile DBFILE]
              [--filetype {json,yaml,yml}]
              [--include-default-config] [--openssh-configfile PATH]
              [-y|--yes]
```

Behavior:

1. Validate inventory path extension vs `--filetype`.
2. Load DB; exit if empty.
3. If SSH config / inventory already have content, prompt for overwrite unless `-y` / `--yes`.
4. Create missing artifact files if needed.
5. Wipe/recreate SSH config via `cleanup_file`; write header + one block per host.
6. Build Ansible `all.hosts` + `children` from groups; write inventory.
7. Optionally update OpenSSH default `config` with managed `Include` (`--include-default-config`).
8. Print usage hints (`ssh -F ...`, `ansible -i ...`, optional `ssh <host>`).

## `generate` flags (extra)

| Flag | Purpose |
|------|---------|
| `--include-default-config` | Add/update `Include <sshc_ssh_config>` in OpenSSH default `config` |
| `--openssh-configfile` | Target file for Include (default `<home>/.ssh/config`) |
| `-y` / `--yes` | Overwrite existing generated files without confirmation |

## Typical workflow

```shell
sshc init
sshc insert --name server1 --host 192.168.0.100 --user ubuntu --groups personal home
sshc generate
ssh -F $HOME/.ssh/sshc_ssh_config server1
ansible -i $HOME/.ssh/sshc_ansible_inventory.json all --list-host
```

## Dev invocation

```shell
poetry install
poetry run sshc --help
poetry run sshc --version
```
