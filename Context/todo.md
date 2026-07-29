# Todo

Tracked adjustments and planned work for this repo.
Update statuses here when work starts, lands, or is dropped. Link related gotchas when useful.

**Status key:** `todo` · `in_progress` · `done` · `dropped`

---

## Adjustments

### ADJ-001 — Ensure Windows support

| Field | Value |
|-------|--------|
| Status | `done` |
| Priority | High |
| Area | Platform / paths / docs / CI |
| Related | [gotchas.md](gotchas.md) § Platform |

**Goal:** Make sshc usable on Windows the same way it is on Linux (init → CRUD → generate → use with OpenSSH / Ansible where available).

**Work items:** all completed (see git history / prior notes).

### ADJ-002 — DB metadata + integrity checksum

| Field | Value |
|-------|--------|
| Status | `done` |
| Priority | Medium |
| Area | Data model / CRUD |

**Goal:** Store DB lifecycle metadata and a SHA-256 of the hosts payload.

**Delivered**

- Document shape `{ "meta": {...}, "hosts": [...] }`
- Fields: `schema_version`, `created_at`, `created_with_sshc_version`, `updated_at`, `updated_with_sshc_version`, `update_count`, `hosts_sha256`
- Mutations bump `update_count` / timestamps / version and refresh checksum
- Legacy bare-array DBs remain readable; upgraded on next write
- Integrity mismatch warns on read; `read --verbose` shows meta

### ADJ-003 — `sshc status` health check

| Field | Value |
|-------|--------|
| Status | `done` |
| Priority | Medium |
| Area | CLI / ops |

**Goal:** Read-only status command for integrity, emptiness, generated-file sync, and identity-file presence.

**Delivered**

- `sshc status` with `--destination` / `--dbfile` / `--configfile` / `--inventoryfile` / `--json`
- SHA-256 verification, empty DB detection, legacy format warning
- Sync compare for SSH config + Ansible inventory; `needs_regeneration` when hosts exist and artifacts missing/stale
- Missing generated files: warning if DB empty, error if hosts present
- Identity file existence warnings
- Exit `1` on error-level issues

---

## Backlog (from known quirks)

| ID | Status | Item | Related |
|----|--------|------|---------|
| BUG-001 | `done` | Fix `delete`: add `--destination` / `--dbfile` to subparser | ADJ-001 |
| BUG-002 | `done` | Fix partial `update` so omitted fields are not overwritten by defaults | `update` CLI + `update_data` |
| BUG-003 | `done` | Surface a clear message when insert skips a duplicate `name` | `insert_data` returns `False` + message |
| BUG-004 | `done` | Make `read_all_data` error return shape consistent (always a list) | returns `[]` on error / non-list |
| DOC-001 | `done` | Align README insert/generate examples with real CLI | README |
| TST-001 | `done` | Stop hardcoding version `0.3.0` in unittest | tests |

### BUG-002 notes

- Update argparse defaults for optional fields are `None` (not injected defaults).
- CLI builds a patch dict with only explicitly provided fields.
- Insert-on-missing still fills insert defaults (`user=root`, etc.) when required.

### BUG-003 notes

- Duplicate `name` prints `Host '<name>' already exists. Skipping insert.` and returns `False`.

### BUG-004 notes

- JSON load failures and non-array DB contents return `[]` (never `{}`).

---

## How to maintain this file

1. New adjustments get an `ADJ-NNN` (or `BUG` / `DOC` / `TST`) id and a short status table.
2. Prefer checklists under the item for implementable steps.
3. When closing an item, set Status to `done` and note the PR/commit if useful — do not delete history immediately.
4. Keep [Context/README.md](README.md) linked to this file.
