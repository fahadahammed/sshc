# sshc — Repository Context

Living context for humans and AI assistants working in this repo.
Prefer these docs over guessing; update them when behavior or structure changes.

| Doc | Use when you need… |
|-----|--------------------|
| [overview.md](overview.md) | What sshc does, why it exists, stack, version |
| [architecture.md](architecture.md) | Layout, modules, data flow, entry points |
| [data-model.md](data-model.md) | Host DB schema, default paths, generated artifacts |
| [cli.md](cli.md) | Subcommands, args, typical workflows |
| [development.md](development.md) | Poetry, tests, CI, packaging, PR conventions |
| [gotchas.md](gotchas.md) | Known bugs, platform quirks, README mismatches |
| [todo.md](todo.md) | Adjustments & backlog |
| [../CHANGELOG.md](../CHANGELOG.md) | Release notes (user-facing) |

User-facing docs: [README.md](../README.md). Contributing: README § Contributing.

## One-line summary

**sshc** is a Python CLI that stores SSH hosts in a JSON DB and generates an OpenSSH config file plus an Ansible inventory from that single source of truth.

## Primary code

Almost all logic lives in one file: `src/sshc.py`.

## Quick map

```
CLI (__main__)
  ├─ init / insert / delete / update / read|list  →  mjdb  →  sshc_db.json
  ├─ status  →  collect_status (DB integrity + generated sync)
  └─ generate
       ├─ generate_host_entry_string       →  sshc_ssh_config
       └─ generate_ansible_inventory_file  →  sshc_ansible_inventory.{json|yml}
```
