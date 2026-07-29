# Overview

## Product

**sshc** — SSH Config and Ansible Inventory Generator.

- **Version:** `0.3.0` (see root `pyproject.toml`; PyPI publish may rewrite from the GitHub release tag)
- **License:** MIT
- **Repo:** https://github.com/fahadahammed/sshc
- **Author:** Fahad Ahammed

## Problem

Managing many servers means maintaining both `~/.ssh/config` and Ansible inventory separately. That duplication drifts.

## Solution

1. Keep a JSON host database (`sshc_db.json`).
2. Generate SSH config from it.
3. Generate Ansible inventory (JSON or YAML) from the same DB.
4. Hosts can belong to multiple groups; groups become Ansible inventory children.

## Technology

| Layer | Choice |
|-------|--------|
| Language | Python 3.7+ |
| Packaging | Poetry |
| Runtime deps | `pyyaml` |
| Stdlib | argparse, json, os, datetime, sys, uuid, pprint, pathlib |
| Targets | OpenSSH config, Ansible inventory |

## Runtime expectations

- Supported on **Linux** and **Windows** for path defaults and file I/O (`Path.home()` → `<home>/.ssh`).
- OpenSSH / Ansible themselves must be installed separately to *use* generated files.
- Install: `pip3 install sshc --upgrade` or develop via Poetry.

## User-facing docs

End-user usage, examples, and install instructions live in root `README.md`.
This `Context/` folder is for maintainers and agents, not a replacement for the README.
