import argparse
import hashlib
import json
import os
import datetime
import sys
import uuid
import pprint
from pathlib import Path
import yaml

DB_SCHEMA_VERSION = 1


def get_random_id():
    the_id = uuid.uuid4()
    return str(the_id)


def utc_now_iso():
    """UTC timestamp in ISO-8601 form."""
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def get_home_dir():
    """Return the user home directory in a platform-portable way."""
    return Path.home()


def get_ssh_dir():
    """Default sshc config home: <home>/.ssh on all platforms."""
    return get_home_dir() / ".ssh"


def default_destination():
    return str(get_ssh_dir())


def default_db_file():
    return str(get_ssh_dir() / "sshc_db.json")


def default_identity_file():
    return str(get_ssh_dir() / "id_rsa")


def default_ssh_config_file():
    return str(get_ssh_dir() / "sshc_ssh_config")


def default_inventory_file():
    return str(get_ssh_dir() / "sshc_ansible_inventory.json")


def read_pyproject_toml():
    """Read package version from pyproject.toml next to the module or repo root."""
    module_dir = Path(__file__).resolve().parent
    candidates = (
        module_dir / "pyproject.toml",
        module_dir.parent / "pyproject.toml",
    )
    for candidate in candidates:
        if candidate.is_file():
            with open(file=str(candidate), mode='r', encoding='utf-8') as tomlfile:
                lines = tomlfile.readlines()
                for line in lines:
                    if "version" in line:
                        return line.split('"')[-2]
            return ""
    return ""


def compute_hosts_sha256(hosts):
    """SHA-256 of a canonical JSON encoding of the hosts list (integrity of payload)."""
    payload = json.dumps(hosts, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def new_db_meta(hosts=None):
    """Create initial DB metadata for an empty or given hosts list."""
    now = utc_now_iso()
    version = read_pyproject_toml()
    hosts = hosts if hosts is not None else []
    return {
        "schema_version": DB_SCHEMA_VERSION,
        "created_at": now,
        "created_with_sshc_version": version,
        "updated_at": now,
        "updated_with_sshc_version": version,
        "update_count": 0,
        "hosts_sha256": compute_hosts_sha256(hosts),
    }


class mjdb:
    def __init__(self, db_file_name="sshc_db.json"):
        self.db_file_name = db_file_name

    def create_db(self):
        """
        Ensure a DB document with metadata exists.

        - Missing file: create `{meta, hosts: []}`.
        - Legacy bare array (or document missing meta fields): upgrade in place,
          preserving hosts. Does not bump update_count as a host mutation.
        - Already modern with meta: leave as-is.
        """
        try:
            if not os.path.exists(self.db_file_name):
                document = {
                    "meta": new_db_meta([]),
                    "hosts": [],
                }
                with open(self.db_file_name, 'w', encoding='utf-8') as opened_db:
                    json.dump(document, opened_db, indent=2)
                print(f"Created DB with metadata: {self.db_file_name}")
                return True

            try:
                with open(self.db_file_name, 'r', encoding='utf-8') as opened_db:
                    raw = json.load(opened_db)
            except Exception as ex:
                print(ex)
                return False

            needs_upgrade = False
            hosts = []
            if isinstance(raw, list):
                hosts = raw
                needs_upgrade = True
            elif isinstance(raw, dict) and isinstance(raw.get("hosts"), list):
                hosts = raw.get("hosts") or []
                meta = raw.get("meta") if isinstance(raw.get("meta"), dict) else {}
                required = (
                    "schema_version",
                    "created_at",
                    "created_with_sshc_version",
                    "updated_at",
                    "updated_with_sshc_version",
                    "update_count",
                    "hosts_sha256",
                )
                if not all(meta.get(key) is not None for key in required):
                    needs_upgrade = True
            else:
                print(f"{self.db_file_name} has invalid format; cannot initiate/upgrade.")
                return False

            if needs_upgrade:
                # Preserve hosts; write full meta without counting as a host mutation.
                meta = new_db_meta(hosts)
                # If upgrading a non-empty legacy DB, keep update_count at 0 for init,
                # but timestamps/version/checksum reflect current state.
                payload = {"meta": meta, "hosts": hosts}
                with open(self.db_file_name, 'w', encoding='utf-8') as opened_db:
                    json.dump(payload, opened_db, indent=2)
                print(
                    f"Upgraded DB to document format with metadata "
                    f"({len(hosts)} host(s)): {self.db_file_name}"
                )
            else:
                print(f"DB already initialized with metadata: {self.db_file_name}")
            return True
        except Exception as ex:
            print(ex)
            return False

    def _load_raw(self):
        if not os.path.exists(self.db_file_name):
            print(f"{self.db_file_name} file doesn't exists. Please initiate DB first.")
            sys.exit("DB file doesn't exists. Please initiate first.")
        with open(self.db_file_name, 'r', encoding='utf-8') as opened_db:
            return json.load(opened_db)

    def load_document(self, warn_integrity=True):
        """
        Load DB as {"meta": dict, "hosts": list}.

        Legacy format (bare JSON array) is accepted and normalized in memory;
        the next write upgrades the file to the document format.
        """
        try:
            raw = self._load_raw()
        except SystemExit:
            raise
        except Exception as ex:
            print(ex)
            return {"meta": {}, "hosts": [], "legacy": False, "valid": False}

        if isinstance(raw, list):
            return {"meta": {}, "hosts": raw, "legacy": True, "valid": True}

        if isinstance(raw, dict) and isinstance(raw.get("hosts"), list):
            meta = raw.get("meta") if isinstance(raw.get("meta"), dict) else {}
            hosts = raw.get("hosts")
            expected = meta.get("hosts_sha256")
            if expected:
                actual = compute_hosts_sha256(hosts)
                if actual != expected and warn_integrity:
                    print(
                        f"Warning: DB integrity check failed for {self.db_file_name}. "
                        f"Expected hosts_sha256={expected}, got {actual}."
                    )
            return {"meta": meta, "hosts": hosts, "legacy": False, "valid": True}

        print(f"{self.db_file_name} has invalid format; expected "
              f'{{"meta": ..., "hosts": [...]}} or a legacy JSON array.')
        return {"meta": {}, "hosts": [], "legacy": False, "valid": False}

    def read_meta(self):
        """Return DB metadata dict (may be empty for legacy DBs until next write)."""
        return dict(self.load_document().get("meta") or {})

    def _write_document(self, hosts, bump_update=True):
        """Persist hosts + refreshed metadata (single write path for all mutations)."""
        document = self.load_document()
        meta = dict(document.get("meta") or {})
        now = utc_now_iso()
        version = read_pyproject_toml()

        if not meta.get("created_at"):
            meta["created_at"] = now
            meta["created_with_sshc_version"] = version
        meta["schema_version"] = DB_SCHEMA_VERSION

        if bump_update:
            meta["update_count"] = int(meta.get("update_count") or 0) + 1
            meta["updated_at"] = now
            meta["updated_with_sshc_version"] = version
        elif "updated_at" not in meta:
            meta["updated_at"] = meta.get("created_at", now)
            meta["updated_with_sshc_version"] = meta.get(
                "created_with_sshc_version", version
            )
            meta["update_count"] = int(meta.get("update_count") or 0)

        meta["hosts_sha256"] = compute_hosts_sha256(hosts)

        payload = {"meta": meta, "hosts": hosts}
        with open(self.db_file_name, 'w', encoding='utf-8') as opened_db:
            json.dump(payload, opened_db, indent=2)
        return payload

    def insert_data(self, data):
        """Take json data and insert it into the DB"""
        if not os.path.exists(self.db_file_name):
            print(f"{self.db_file_name} file doesn't exists. Please initiate DB first.")
            sys.exit()
        try:
            data["id"] = get_random_id()
            existing_data = self.read_all_data()
            data_exists = [x for x in existing_data if x.get("name") == data.get("name")]
            if data_exists:
                print(f"Host '{data.get('name')}' already exists. Skipping insert.")
                return False
            self._write_document(existing_data + [data], bump_update=True)
            return True
        except Exception as ex:
            print(ex)
            return False

    def update_data(self, data):
        """Merge provided fields onto an existing host record and rewrite the DB."""
        if not os.path.exists(self.db_file_name):
            print(f"{self.db_file_name} file doesn't exists. Please initiate DB first.")
            sys.exit()
        try:
            hosts = self.read_all_data()
            found = False
            new_hosts = []
            for host in hosts:
                if host.get("name") == data.get("name"):
                    updated_data = host.copy()
                    for k, v in data.items():
                        updated_data[k] = v
                    new_hosts.append(updated_data)
                    found = True
                else:
                    new_hosts.append(host)
            if not found:
                print(f"Host '{data.get('name')}' not found. Cannot update.")
                return False
            self._write_document(new_hosts, bump_update=True)
            return True
        except Exception as ex:
            print(ex)
            return False

    def read_data(self, hostname):
        all_data = self.read_all_data()
        if all_data:
            data = [x for x in all_data if x.get("name") == hostname]
            if data:
                return data[0]
            return {}
        return {}

    def delete_data(self, hostname):
        all_data = self.read_all_data()
        to_insert = [data for data in all_data if data.get("name") != hostname]
        self._write_document(to_insert, bump_update=True)
        return to_insert

    def read_all_data(self):
        document = self.load_document()
        return document.get("hosts") or []


def cleanup_file(configfile):
    """Remove an existing config file using portable path handling."""
    config_path = Path(configfile)
    try:
        if config_path.is_file():
            config_path.unlink()
    except Exception as ex:
        print(ex)
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(str(config_path), "w", encoding='utf-8') as openconfig:
                openconfig.write("")
        except Exception as mkdir_ex:
            print(mkdir_ex)


def generate_host_entry_string(name, host, port, user, log_level,
                               compression, identityfile, configfile, comment):
    entry_template = f'''# -- <
Host {name}
HostName {host}
Port {port}
User {user}
IdentityFile {identityfile}
LogLevel {log_level}
Compression {compression}
# Comment: {comment}
# -- >
\n'''

    with open(file=configfile, mode="a+", encoding='utf-8') as thefile:
        thefile.write(entry_template)


def generate_ansible_inventory_file(data_to_write, inventory_file_name, file_type="json"):
    if file_type == "json":
        with open(file=inventory_file_name, mode="w", encoding='utf-8') as thefile:
            json.dump(data_to_write, thefile)
    if file_type in ["yaml", "yml"]:
        with open(file=inventory_file_name, mode="w", encoding='utf-8') as thefile:
            yaml.dump(data=data_to_write, stream=thefile)


def parse_ssh_config_hosts(configfile):
    """Parse OpenSSH-style Host blocks into {name: {host, port, user, identityfile}}."""
    path = Path(configfile)
    if not path.is_file():
        return {}
    hosts = {}
    current = None
    with open(str(path), "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue
            key, value = parts[0], parts[1].strip()
            key_l = key.lower()
            if key_l == "host":
                current = value.split()[0]
                hosts[current] = {}
            elif current is None:
                continue
            elif key_l == "hostname":
                hosts[current]["host"] = value
            elif key_l == "port":
                try:
                    hosts[current]["port"] = int(value)
                except ValueError:
                    hosts[current]["port"] = value
            elif key_l == "user":
                hosts[current]["user"] = value
            elif key_l == "identityfile":
                hosts[current]["identityfile"] = value
    return hosts


def load_ansible_inventory_hosts(inventoryfile):
    """Load ansible inventory hosts map from JSON or YAML inventory file."""
    path = Path(inventoryfile)
    if not path.is_file():
        return None
    suffix = path.suffix.lower()
    with open(str(path), "r", encoding="utf-8") as handle:
        if suffix in (".yaml", ".yml"):
            data = yaml.safe_load(handle) or {}
        else:
            data = json.load(handle)
    all_block = data.get("all") if isinstance(data, dict) else None
    if not isinstance(all_block, dict):
        return {}
    hosts = all_block.get("hosts") or {}
    return hosts if isinstance(hosts, dict) else {}


def _compare_generated_to_db(db_hosts, generated_by_name, source_label):
    """Compare DB hosts to parsed SSH config or Ansible inventory entries."""
    db_by_name = {h.get("name"): h for h in db_hosts if h.get("name")}
    missing = sorted(set(db_by_name) - set(generated_by_name))
    extra = sorted(set(generated_by_name) - set(db_by_name))
    mismatches = []
    for name, db_host in db_by_name.items():
        gen = generated_by_name.get(name)
        if not gen:
            continue
        if source_label == "ssh_config":
            expected = {
                "host": db_host.get("host"),
                "port": db_host.get("port"),
                "user": db_host.get("user"),
                "identityfile": db_host.get("identityfile"),
            }
            actual = {
                "host": gen.get("host"),
                "port": gen.get("port"),
                "user": gen.get("user"),
                "identityfile": gen.get("identityfile"),
            }
        else:
            expected = {
                "host": db_host.get("host"),
                "port": db_host.get("port"),
                "user": db_host.get("user"),
                "identityfile": db_host.get("identityfile"),
            }
            actual = {
                "host": gen.get("ansible_host"),
                "port": gen.get("ansible_port"),
                "user": gen.get("ansible_user"),
                "identityfile": gen.get("ansible_ssh_private_key_file"),
            }
        field_diffs = {}
        for field, exp_val in expected.items():
            act_val = actual.get(field)
            if field == "port":
                try:
                    exp_val = int(exp_val) if exp_val is not None else None
                except (TypeError, ValueError):
                    pass
                try:
                    act_val = int(act_val) if act_val is not None else None
                except (TypeError, ValueError):
                    pass
            if exp_val != act_val:
                field_diffs[field] = {"db": exp_val, "generated": act_val}
        if field_diffs:
            mismatches.append({"name": name, "fields": field_diffs})
    in_sync = not missing and not extra and not mismatches
    return {
        "in_sync": in_sync,
        "missing_in_generated": missing,
        "extra_in_generated": extra,
        "field_mismatches": mismatches,
    }


def collect_status(dbfile, configfile, inventoryfile):
    """Build a structured health report for DB + generated artifacts."""
    issues = []
    needs_regeneration = False
    version = read_pyproject_toml()

    report = {
        "sshc_version": version,
        "ok": True,
        "needs_regeneration": False,
        "db": {
            "path": dbfile,
            "exists": False,
            "readable": False,
            "valid": False,
            "legacy_format": False,
            "empty": True,
            "host_count": 0,
            "integrity": {"ok": None, "expected": None, "actual": None},
            "meta": {},
        },
        "ssh_config": {
            "path": configfile,
            "exists": False,
            "in_sync": None,
            "missing_in_generated": [],
            "extra_in_generated": [],
            "field_mismatches": [],
        },
        "ansible_inventory": {
            "path": inventoryfile,
            "exists": False,
            "readable": False,
            "in_sync": None,
            "missing_in_generated": [],
            "extra_in_generated": [],
            "field_mismatches": [],
        },
        "identity_files": {"missing": [], "present": []},
        "issues": issues,
    }

    if not os.path.exists(dbfile):
        issues.append({
            "level": "error",
            "code": "db_missing",
            "message": f"DB file not found: {dbfile}. Run `sshc init` first.",
        })
        report["ok"] = False
        return report

    report["db"]["exists"] = True
    db = mjdb(db_file_name=dbfile)
    try:
        document = db.load_document(warn_integrity=False)
    except SystemExit:
        issues.append({
            "level": "error",
            "code": "db_unreadable",
            "message": f"DB file could not be loaded: {dbfile}",
        })
        report["ok"] = False
        return report

    report["db"]["readable"] = True
    report["db"]["valid"] = bool(document.get("valid"))
    report["db"]["legacy_format"] = bool(document.get("legacy"))
    hosts = document.get("hosts") or []
    meta = document.get("meta") or {}
    report["db"]["meta"] = meta
    report["db"]["host_count"] = len(hosts)
    report["db"]["empty"] = len(hosts) == 0

    if not document.get("valid"):
        issues.append({
            "level": "error",
            "code": "db_invalid",
            "message": f"DB file has invalid format: {dbfile}",
        })
        report["ok"] = False
        return report

    if document.get("legacy"):
        issues.append({
            "level": "warning",
            "code": "db_legacy_format",
            "message": "DB is legacy JSON array format; next write will upgrade to document format.",
        })

    expected = meta.get("hosts_sha256")
    actual = compute_hosts_sha256(hosts)
    report["db"]["integrity"] = {
        "ok": (expected == actual) if expected else None,
        "expected": expected,
        "actual": actual,
    }
    if expected and expected != actual:
        issues.append({
            "level": "error",
            "code": "integrity_mismatch",
            "message": (
                f"hosts_sha256 mismatch (expected {expected}, actual {actual})."
            ),
        })
        report["ok"] = False
    elif not expected and not document.get("legacy"):
        issues.append({
            "level": "warning",
            "code": "integrity_missing",
            "message": "DB meta has no hosts_sha256; integrity cannot be verified.",
        })

    if report["db"]["empty"]:
        issues.append({
            "level": "warning",
            "code": "db_empty",
            "message": "DB has no hosts.",
        })

    invalid_hosts = []
    for host in hosts:
        if not host.get("name") or not host.get("host"):
            invalid_hosts.append(host.get("name") or "<unnamed>")
    if invalid_hosts:
        issues.append({
            "level": "warning",
            "code": "invalid_host_records",
            "message": f"Hosts missing name/host: {', '.join(invalid_hosts)}",
        })

    names = [h.get("name") for h in hosts if h.get("name")]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        issues.append({
            "level": "warning",
            "code": "duplicate_host_names",
            "message": f"Duplicate host names in DB: {', '.join(dupes)}",
        })

    missing_keys = []
    present_keys = []
    for host in hosts:
        identity = host.get("identityfile")
        if not identity:
            continue
        if Path(identity).is_file():
            present_keys.append(identity)
        else:
            missing_keys.append({"name": host.get("name"), "identityfile": identity})
    report["identity_files"]["missing"] = missing_keys
    report["identity_files"]["present"] = present_keys
    for item in missing_keys:
        issues.append({
            "level": "warning",
            "code": "identityfile_missing",
            "message": (
                f"Identity file for host '{item['name']}' not found: "
                f"{item['identityfile']}"
            ),
        })

    # SSH config
    config_exists = Path(configfile).is_file()
    report["ssh_config"]["exists"] = config_exists
    if not config_exists:
        if report["db"]["empty"]:
            issues.append({
                "level": "warning",
                "code": "ssh_config_missing",
                "message": f"SSH config not found (DB empty): {configfile}",
            })
        else:
            issues.append({
                "level": "error",
                "code": "ssh_config_missing",
                "message": f"SSH config missing; run `sshc generate`: {configfile}",
            })
            needs_regeneration = True
            report["ok"] = False
    else:
        parsed = parse_ssh_config_hosts(configfile)
        cmp_result = _compare_generated_to_db(hosts, parsed, "ssh_config")
        report["ssh_config"].update(cmp_result)
        if hosts and not cmp_result["in_sync"]:
            needs_regeneration = True
            report["ok"] = False
            issues.append({
                "level": "error",
                "code": "ssh_config_out_of_sync",
                "message": "SSH config does not match DB hosts; regeneration needed.",
            })
        elif not hosts and not cmp_result["in_sync"]:
            issues.append({
                "level": "warning",
                "code": "ssh_config_out_of_sync",
                "message": "SSH config has entries while DB is empty.",
            })

    # Ansible inventory
    inventory_exists = Path(inventoryfile).is_file()
    report["ansible_inventory"]["exists"] = inventory_exists
    if not inventory_exists:
        if report["db"]["empty"]:
            issues.append({
                "level": "warning",
                "code": "inventory_missing",
                "message": f"Ansible inventory not found (DB empty): {inventoryfile}",
            })
        else:
            issues.append({
                "level": "error",
                "code": "inventory_missing",
                "message": (
                    f"Ansible inventory missing; run `sshc generate`: {inventoryfile}"
                ),
            })
            needs_regeneration = True
            report["ok"] = False
    else:
        try:
            inv_hosts = load_ansible_inventory_hosts(inventoryfile)
            report["ansible_inventory"]["readable"] = True
        except Exception as ex:
            inv_hosts = None
            report["ansible_inventory"]["readable"] = False
            issues.append({
                "level": "error",
                "code": "inventory_unreadable",
                "message": f"Failed to read inventory {inventoryfile}: {ex}",
            })
            report["ok"] = False
            needs_regeneration = True
        if inv_hosts is not None:
            cmp_result = _compare_generated_to_db(hosts, inv_hosts, "ansible_inventory")
            report["ansible_inventory"].update(cmp_result)
            if hosts and not cmp_result["in_sync"]:
                needs_regeneration = True
                report["ok"] = False
                issues.append({
                    "level": "error",
                    "code": "inventory_out_of_sync",
                    "message": (
                        "Ansible inventory does not match DB hosts; regeneration needed."
                    ),
                })
            elif not hosts and not cmp_result["in_sync"]:
                issues.append({
                    "level": "warning",
                    "code": "inventory_out_of_sync",
                    "message": "Ansible inventory has entries while DB is empty.",
                })

    report["needs_regeneration"] = needs_regeneration
    if needs_regeneration:
        issues.append({
            "level": "error",
            "code": "needs_regeneration",
            "message": "Run `sshc generate` to refresh SSH config and/or Ansible inventory.",
        })
    report["issues"] = issues
    return report


def print_status_report(report):
    """Human-readable status output."""
    db = report.get("db", {})
    print("sshc status")
    print("." * 50)
    print(f"sshc version: {report.get('sshc_version')}")
    print(f"overall: {'OK' if report.get('ok') else 'NOT OK'}")
    print(f"needs_regeneration: {report.get('needs_regeneration')}")
    print("." * 50)
    print("DB")
    print(f"  path: {db.get('path')}")
    print(f"  exists: {db.get('exists')}  readable: {db.get('readable')}  "
          f"valid: {db.get('valid')}  legacy: {db.get('legacy_format')}")
    print(f"  empty: {db.get('empty')}  host_count: {db.get('host_count')}")
    integrity = db.get("integrity") or {}
    print(f"  integrity_ok: {integrity.get('ok')}")
    if integrity.get("expected"):
        print(f"  hosts_sha256 expected: {integrity.get('expected')}")
        print(f"  hosts_sha256 actual:   {integrity.get('actual')}")
    meta = db.get("meta") or {}
    if meta:
        print(f"  created_at: {meta.get('created_at')} "
              f"(sshc {meta.get('created_with_sshc_version')})")
        print(f"  updated_at: {meta.get('updated_at')} "
              f"(sshc {meta.get('updated_with_sshc_version')})")
        print(f"  update_count: {meta.get('update_count')}")
    print("SSH config")
    ssh = report.get("ssh_config") or {}
    print(f"  path: {ssh.get('path')}")
    print(f"  exists: {ssh.get('exists')}  in_sync: {ssh.get('in_sync')}")
    print("Ansible inventory")
    inv = report.get("ansible_inventory") or {}
    print(f"  path: {inv.get('path')}")
    print(f"  exists: {inv.get('exists')}  readable: {inv.get('readable')}  "
          f"in_sync: {inv.get('in_sync')}")
    identity = report.get("identity_files") or {}
    print(f"Identity files missing: {len(identity.get('missing') or [])}")
    print("." * 50)
    issues = report.get("issues") or []
    if not issues:
        print("No issues.")
    else:
        print("Issues:")
        for issue in issues:
            print(f"  [{issue.get('level')}] {issue.get('code')}: {issue.get('message')}")


def __main__():
    parser = argparse.ArgumentParser(description='SSH Config and Ansible Inventory Generator !')

    parser.add_argument('--version', action='version', version="sshc, " + "v" + read_pyproject_toml())

    subparser = parser.add_subparsers(dest="command", description="The main command of this CLI tool.",
                                      help="The main commands have their own arguments.", required=True)

    init = subparser.add_parser("init", help="Initiate Host DB !")
    insert = subparser.add_parser("insert", help="Insert host information !")
    delete = subparser.add_parser("delete", help="Delete host information !")
    update = subparser.add_parser("update", help="Update host information !")
    read = subparser.add_parser(
        "read",
        aliases=["list"],
        help="Read / list host database !",
    )
    generate = subparser.add_parser("generate", help="Generate necessary config files !")
    status = subparser.add_parser(
        "status",
        help="Check DB integrity and generated file sync !",
    )

    init.add_argument('--destination', help='Config HOME?',
                        default=default_destination())
    init.add_argument('--dbfile', help='SSHC DB File.',
                        default=default_db_file())

    insert.add_argument('--name', help='Server Name?', required=True)
    insert.add_argument('--host', help='SSH Host?', required=True)
    insert.add_argument('--user', help='SSH User?', default="root")
    insert.add_argument('--port', help='SSH Port?', default=22)
    insert.add_argument('--comment', help='SSH Identity File.', default="No Comment.")
    insert.add_argument('--loglevel', help='SSH Log Level.',
                        choices=["INFO", "DEBUG", "ERROR", "WARNING"],
                        default="INFO")
    insert.add_argument('--compression', help='SSH Connection Compression.',
                        choices=["yes", "no"], default="no")
    insert.add_argument('--groups', nargs='+', help='Which group to include?', default=[])
    insert.add_argument('--identityfile', help='SSH Default Identity File Location. i.e. id_rsa',
                        default=default_identity_file())
    insert.add_argument('--destination', help='Config HOME?',
                        default=default_destination())
    insert.add_argument('--dbfile', help='SSHC DB File.',
                        default=default_db_file())

    delete.add_argument('--hostname', help="Server Host Name?", required=True)
    delete.add_argument('--destination', help='Config HOME?',
                        default=default_destination())
    delete.add_argument('--dbfile', help='SSHC DB File.',
                        default=default_db_file())

    update.add_argument('--name', help='Server Name?', required=True)
    update.add_argument('--host', help='SSH Host?', default=None)
    update.add_argument('--user', help='SSH User?', default=None)
    update.add_argument('--port', help='SSH Port?', default=None)
    update.add_argument('--comment', help='Host comment.', default=None)
    update.add_argument('--loglevel', help='SSH Log Level.',
                        choices=["INFO", "DEBUG", "ERROR", "WARNING"],
                        default=None)
    update.add_argument('--compression', help='SSH Connection Compression.',
                        choices=["yes", "no"], default=None)
    update.add_argument('--groups', nargs='+', help='Which group to include?', default=None)
    update.add_argument('--identityfile', help='SSH Default Identity File Location. i.e. id_rsa',
                        default=None)
    update.add_argument('--destination', help='Config HOME?',
                        default=default_destination())
    update.add_argument('--dbfile', help='SSHC DB File.',
                        default=default_db_file())


    read.add_argument('--hostname', help="Server Host Name?", required=False)
    read.add_argument('--verbose', help="Verbosity?",
                      choices=["yes", "no"], required=False)
    read.add_argument('--destination', help='Config HOME?',
                        default=default_destination())
    read.add_argument('--dbfile', help='SSHC DB File.',
                        default=default_db_file())

    generate.add_argument('--configfile', help='SSH Config File.',
                        default=default_ssh_config_file())
    generate.add_argument('--inventoryfile', help='Ansible Inventory File.',
                        default=default_inventory_file())
    generate.add_argument('--destination', help='Config HOME?',
                        default=default_destination())
    generate.add_argument('--dbfile', help='SSHC DB File.',
                        default=default_db_file())
    generate.add_argument('--filetype', help='Preferred file type for Ansible inventory. '
                                             'Default is json and you can choose yaml too.',
                          choices=["json", "yaml", "yml"], default="json")

    status.add_argument('--configfile', help='SSH Config File.',
                        default=default_ssh_config_file())
    status.add_argument('--inventoryfile', help='Ansible Inventory File.',
                        default=default_inventory_file())
    status.add_argument('--destination', help='Config HOME?',
                        default=default_destination())
    status.add_argument('--dbfile', help='SSHC DB File.',
                        default=default_db_file())
    status.add_argument('--json', dest='as_json', action='store_true',
                        help='Print status as JSON.')

    # Parse the args
    args = parser.parse_args()

    # Catch Main Command
    command = args.command
    # Process Main Command
    if command == "init":
        print("Initiating DB.")
        # Home of the config
        destination = args.destination
        if not os.path.exists(destination):
            print(f"{destination} directory is not ready.")
            os.makedirs(destination)
            print(f"{destination} directory is created.")
        dbfile = args.dbfile
        mjdb(db_file_name=dbfile).create_db()
        print("Done.")
    elif command == "insert":
        print("Inserting DATA to DB.")
        # Home of the config
        destination = args.destination
        if not os.path.exists(destination):
            print(f"{destination} directory is not ready.")
            os.makedirs(destination)
            print(f"{destination} directory is created.")
        dbfile = args.dbfile
        name = str(args.name).lower()
        host = args.host
        port = int(args.port)
        user = args.user
        identityfile = args.identityfile
        loglevel = args.loglevel
        compression = args.compression
        comment = args.comment
        groups = args.groups

        if not name or not host or not port or not user:
            sys.exit("Some required parameters missing.")

        data = {
            "name": name, "host": host, "port": port, "user": user,
            "log_level": loglevel, "compression": compression, "identityfile": identityfile,
            "comment": comment, "groups": groups
        }
        print("Inserting data...")
        inserted = mjdb(db_file_name=dbfile).insert_data(data=data)
        if inserted:
            print("Done.")
        else:
            print("Done (no changes).")
    elif command == "delete":
        # Home of the config
        destination = args.destination
        if not os.path.exists(destination):
            print(f"{destination} directory is not ready.")
            os.makedirs(destination)
            print(f"{destination} directory is created.")
        dbfile = args.dbfile
        hostname = str(args.hostname).lower()
        print(f"Trying to delete host {hostname} from DB.")
        mjdb(db_file_name=dbfile).delete_data(hostname=hostname)
        print("Done.")
    elif command == "update":
        # Home of the config
        destination = args.destination
        if not os.path.exists(destination):
            print(f"{destination} directory is not ready.")
            os.makedirs(destination)
            print(f"{destination} directory is created.")
        dbfile = args.dbfile
        name = str(args.name).lower()

        if not name:
            sys.exit("Some required parameters missing.")

        # Only include fields the user explicitly passed (BUG-002: no default overwrites).
        data = {"name": name}
        if args.host is not None:
            data["host"] = args.host
        if args.port is not None:
            data["port"] = int(args.port)
        if args.user is not None:
            data["user"] = args.user
        if args.identityfile is not None:
            data["identityfile"] = args.identityfile
        if args.loglevel is not None:
            data["log_level"] = args.loglevel
        if args.compression is not None:
            data["compression"] = args.compression
        if args.comment is not None:
            data["comment"] = args.comment
        if args.groups is not None:
            data["groups"] = args.groups

        all_data = mjdb(db_file_name=dbfile).read_all_data()
        existing_names = [x.get("name") for x in all_data]
        if name in existing_names:
            print("Found in DB, so updating data...")
            mjdb(db_file_name=dbfile).update_data(data=data)
        else:
            print("Not found in DB to update, so inserting data...")
            if "host" not in data or "port" not in data:
                sys.exit("Some required parameters missing for insert "
                         "(need --host and --port when the host does not exist).")
            if "user" not in data:
                data["user"] = "root"
            if "log_level" not in data:
                data["log_level"] = "INFO"
            if "compression" not in data:
                data["compression"] = "no"
            if "identityfile" not in data:
                data["identityfile"] = default_identity_file()
            if "comment" not in data:
                data["comment"] = "No Comment."
            if "groups" not in data:
                data["groups"] = []
            mjdb(db_file_name=dbfile).insert_data(data=data)
        print("Done.")
    elif command == "generate":
        print("Generating config files from DB.")
        print("Generating SSH Config File...")
        filetype = args.filetype
        # Home of the config
        destination = args.destination
        if not os.path.exists(destination):
            print(f"{destination} directory is not ready.")
            os.makedirs(destination)
            print(f"{destination} directory is created.")
        dbfile = args.dbfile
        configfile = args.configfile
        if not os.path.exists(configfile):
            print(f"{configfile} file doesn't exists, creating.")
            with open(configfile, 'w', encoding='utf-8') as file:
                file.write("")
            print(f"{configfile} file created.")

        inventoryfile = args.inventoryfile
        if filetype == "json":
            if inventoryfile.endswith("json"):
                if not os.path.exists(inventoryfile):
                    print(f"{inventoryfile} file doesn't exists, creating.")
                    with open(inventoryfile, 'w', encoding='utf-8') as file:
                        file.write("{}")
                    print(f"{inventoryfile} file created.")
            else:
                print(f"Please pass {filetype} inventory file.")
        if filetype in ["yaml", "yml"]:
            if inventoryfile.endswith("yaml") or inventoryfile.endswith("yml"):
                if not os.path.exists(inventoryfile):
                    print(f"{inventoryfile} file doesn't exists, creating.")
                    with open(inventoryfile, 'w', encoding='utf-8') as file:
                        file.write("{}")
                    print(f"{inventoryfile} file created.")
            else:
                print(f"Please pass {filetype} inventory file.")

        the_data = mjdb(db_file_name=dbfile).read_all_data()
        if the_data:
            all_hosts = {}
            groups = []
            cleanup_file(configfile=configfile)
            with open(file=configfile, mode="a+", encoding='utf-8') as thefile:
                thefile.write(f"# Generated At: {datetime.datetime.utcnow()}\n")
                thefile.write("# sshc Version: " + str(read_pyproject_toml()) + "\n\n")
            for i in the_data:
                groups += i.get("groups", [])
                all_hosts[i.get("name")] = {
                    "ansible_host": i.get("host"),
                    "ansible_port": i.get("port"),
                    "ansible_user": i.get("user"),
                    "ansible_ssh_private_key_file": i.get("identityfile")
                }
                generate_host_entry_string(name=i["name"], host=i["host"], port=i["port"],
                                           user=i["user"], log_level=i["log_level"],
                                           compression=i["compression"],
                                           identityfile=i["identityfile"],
                                           configfile=configfile, comment=i["comment"]
                                           )
            groups = list(set(groups))
            children = {}
            for i in groups:
                hosts = {}
                for j in the_data:
                    if i in j.get("groups", []):
                        hosts[j["name"]] = None
                children[i] = {
                    "hosts": hosts
                }
            ansible_inventory_data = {
                "all": {
                    "hosts": all_hosts,
                    "children": children
                },
                "others": {
                    "generated_at": str(datetime.datetime.utcnow()),
                    "sshc_version": str(read_pyproject_toml())
                }
            }
            generate_ansible_inventory_file(data_to_write=ansible_inventory_data,
                                            inventory_file_name=inventoryfile, file_type=filetype)
            print("Done.")
            print("." * 50)
            print(f"SSH Config File: {configfile}")
            print(f"Ansible Inventory: {inventoryfile}")
            print("." * 50)
            print("# How?")
            print(f"ssh -F {configfile}")
            print(f"ansible -i {inventoryfile}")
            print("." * 50)
        else:
            sys.exit("No data in DB.")
    elif command in ("read", "list"):
        print("Trying to read DB.")
        # Home of the config
        destination = args.destination
        if not os.path.exists(destination):
            print(f"{destination} directory is not ready.")
            os.makedirs(destination)
            print(f"{destination} directory is created.")
        dbfile = args.dbfile
        db = mjdb(db_file_name=dbfile)
        if not args.hostname:
            to_return = db.read_all_data()
        else:
            to_return = [x for x in db.read_all_data()
                         if x.get("name") == str(args.hostname)]
        p_p = pprint.PrettyPrinter(indent=4)
        if args.verbose == "yes":
            print("DB metadata:")
            p_p.pprint(db.read_meta())
            print("Hosts:")
            p_p.pprint(to_return)
        elif not to_return:
            print("No hosts found in DB.")
        else:
            to_return_1 = []
            liner = []
            for _ in to_return:
                frmt1 = f'{_.get("name")}\t{_.get("host")}'
                frmt2 = f'$ ssh {_.get("name")}'
                frmt = f"{frmt1}\n{frmt2}"
                to_return_1.append(frmt)
                frmt1ln = len(frmt1)
                frmt2ln = len(frmt2)
                frmtln = frmt1ln if frmt1ln >= frmt2ln else frmt2ln
                liner.append(int((frmtln+((3/frmtln)*100))))
            final_liner = max(liner)
            print("." * final_liner)
            for i in to_return_1:
                print(i)
                print("."*final_liner)
    elif command == "status":
        report = collect_status(
            dbfile=args.dbfile,
            configfile=args.configfile,
            inventoryfile=args.inventoryfile,
        )
        if args.as_json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_status_report(report)
        if not report.get("ok"):
            sys.exit(1)
    else:
        print("There is nothing to execute.")
