import json
import os
import sys
import tempfile
import unittest
from pathlib import Path, PureWindowsPath, PurePosixPath
from unittest import mock

from src.sshc import (
    cleanup_file,
    compute_hosts_sha256,
    confirm_overwrite,
    default_db_file,
    default_destination,
    default_identity_file,
    default_inventory_file,
    default_ssh_config_file,
    get_home_dir,
    get_ssh_dir,
    generate_ansible_inventory_file,
    generate_host_entry_string,
    mjdb,
    read_pyproject_toml,
)


class Test_Basic_Function(unittest.TestCase):
    def test_read_all_data(self):
        with self.assertRaises(SystemExit) as cm:
            mjdb().read_all_data()
        self.assertEqual(cm.exception.code, "DB file doesn't exists. Please initiate first.")

    def test_read_pyproject_toml(self):
        version = read_pyproject_toml()
        self.assertTrue(version)
        self.assertRegex(version, r"^\d+\.\d+\.\d+")


class TestPortablePaths(unittest.TestCase):
    def test_get_home_dir_uses_path_home(self):
        fake_home = Path(tempfile.gettempdir()) / "sshc-fake-home"
        with mock.patch.object(Path, "home", return_value=fake_home):
            self.assertEqual(get_home_dir(), fake_home)

    def test_get_ssh_dir_under_home(self):
        fake_home = Path(tempfile.gettempdir()) / "sshc-fake-home"
        with mock.patch.object(Path, "home", return_value=fake_home):
            self.assertEqual(get_ssh_dir(), fake_home / ".ssh")

    def test_default_paths_do_not_depend_on_home_env(self):
        fake_home = Path(tempfile.gettempdir()) / "sshc-no-home-env"
        env = os.environ.copy()
        env.pop("HOME", None)
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch.object(Path, "home", return_value=fake_home):
                self.assertEqual(default_destination(), str(fake_home / ".ssh"))
                self.assertEqual(default_db_file(), str(fake_home / ".ssh" / "sshc_db.json"))
                self.assertEqual(default_identity_file(), str(fake_home / ".ssh" / "id_rsa"))
                self.assertEqual(
                    default_ssh_config_file(),
                    str(fake_home / ".ssh" / "sshc_ssh_config"),
                )
                self.assertEqual(
                    default_inventory_file(),
                    str(fake_home / ".ssh" / "sshc_ansible_inventory.json"),
                )

    def test_default_paths_join_with_native_separator(self):
        fake_home = Path(tempfile.gettempdir()) / "sshc-sep-home"
        with mock.patch.object(Path, "home", return_value=fake_home):
            destination = default_destination()
            db_file = default_db_file()
        self.assertEqual(Path(db_file), Path(destination) / "sshc_db.json")
        self.assertEqual(Path(destination), fake_home / ".ssh")

    def test_windows_style_home_produces_windows_like_paths(self):
        win_home = PureWindowsPath(r"C:\Users\tester")
        win_ssh = win_home / ".ssh"
        self.assertEqual(str(win_ssh / "sshc_db.json"), r"C:\Users\tester\.ssh\sshc_db.json")
        self.assertEqual(str(win_ssh / "sshc_ssh_config"), r"C:\Users\tester\.ssh\sshc_ssh_config")

    def test_posix_style_home_produces_posix_like_paths(self):
        posix_home = PurePosixPath("/home/tester")
        posix_ssh = posix_home / ".ssh"
        self.assertEqual(str(posix_ssh / "sshc_db.json"), "/home/tester/.ssh/sshc_db.json")


class TestCleanupFile(unittest.TestCase):
    def test_cleanup_removes_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "nested" / "sshc_ssh_config"
            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text("old", encoding="utf-8")
            cleanup_file(str(config))
            self.assertFalse(config.exists())

    def test_cleanup_handles_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "missing_config"
            cleanup_file(str(config))
            self.assertFalse(config.exists())


class TestReadPyprojectPortable(unittest.TestCase):
    def test_reads_repo_root_pyproject(self):
        root = Path(__file__).resolve().parents[1]
        expected = None
        with open(root / "pyproject.toml", encoding="utf-8") as handle:
            for line in handle:
                if "version" in line:
                    expected = line.split('"')[-2]
                    break
        self.assertEqual(read_pyproject_toml(), expected)


class TestWorkflowOnTempPaths(unittest.TestCase):
    """Exercise CRUD + generate using OS-native temp paths (works on Windows and Linux)."""

    def test_init_insert_generate_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / ".ssh"
            dbfile = destination / "sshc_db.json"
            configfile = destination / "sshc_ssh_config"
            inventoryfile = destination / "sshc_ansible_inventory.json"

            destination.mkdir(parents=True, exist_ok=True)
            db = mjdb(db_file_name=str(dbfile))
            self.assertTrue(db.create_db())
            self.assertTrue(dbfile.is_file())

            host = {
                "name": "server1",
                "host": "192.168.0.100",
                "port": 22,
                "user": "ubuntu",
                "log_level": "INFO",
                "compression": "no",
                "identityfile": str(destination / "id_rsa"),
                "comment": "test host",
                "groups": ["personal"],
            }
            self.assertTrue(db.insert_data(host))
            rows = db.read_all_data()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["name"], "server1")

            cleanup_file(str(configfile))
            with open(configfile, "w", encoding="utf-8") as handle:
                handle.write("# header\n")
            generate_host_entry_string(
                name=host["name"],
                host=host["host"],
                port=host["port"],
                user=host["user"],
                log_level=host["log_level"],
                compression=host["compression"],
                identityfile=host["identityfile"],
                configfile=str(configfile),
                comment=host["comment"],
            )
            content = configfile.read_text(encoding="utf-8")
            self.assertIn("Host server1", content)
            self.assertIn("HostName 192.168.0.100", content)

            inventory = {
                "all": {
                    "hosts": {
                        "server1": {
                            "ansible_host": host["host"],
                            "ansible_port": host["port"],
                            "ansible_user": host["user"],
                            "ansible_ssh_private_key_file": host["identityfile"],
                        }
                    },
                    "children": {"personal": {"hosts": {"server1": None}}},
                }
            }
            generate_ansible_inventory_file(inventory, str(inventoryfile), file_type="json")
            loaded = json.loads(inventoryfile.read_text(encoding="utf-8"))
            self.assertIn("server1", loaded["all"]["hosts"])

            db.delete_data(hostname="server1")
            self.assertEqual(db.read_all_data(), [])


class TestInsertDuplicate(unittest.TestCase):
    def test_duplicate_insert_is_skipped_with_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            dbfile = Path(tmp) / "sshc_db.json"
            db = mjdb(db_file_name=str(dbfile))
            db.create_db()
            host = {
                "name": "duphost",
                "host": "10.0.0.1",
                "port": 22,
                "user": "root",
                "log_level": "INFO",
                "compression": "no",
                "identityfile": "id_rsa",
                "comment": "one",
                "groups": [],
            }
            self.assertTrue(db.insert_data(dict(host)))
            with mock.patch("builtins.print") as mocked_print:
                result = db.insert_data(dict(host))
            self.assertFalse(result)
            self.assertEqual(len(db.read_all_data()), 1)
            printed = " ".join(str(c.args[0]) for c in mocked_print.call_args_list if c.args)
            self.assertIn("already exists", printed)


class TestPartialUpdate(unittest.TestCase):
    def test_update_only_changes_provided_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            dbfile = Path(tmp) / "sshc_db.json"
            db = mjdb(db_file_name=str(dbfile))
            db.create_db()
            original = {
                "name": "server1",
                "host": "192.168.0.100",
                "port": 22,
                "user": "ubuntu",
                "log_level": "INFO",
                "compression": "no",
                "identityfile": "/keys/a.pem",
                "comment": "keep me",
                "groups": ["personal"],
            }
            self.assertTrue(db.insert_data(original))
            original_id = db.read_data("server1")["id"]

            self.assertTrue(db.update_data({"name": "server1", "port": 2222}))
            updated = db.read_data("server1")
            self.assertEqual(updated["port"], 2222)
            self.assertEqual(updated["user"], "ubuntu")
            self.assertEqual(updated["host"], "192.168.0.100")
            self.assertEqual(updated["comment"], "keep me")
            self.assertEqual(updated["groups"], ["personal"])
            self.assertEqual(updated["identityfile"], "/keys/a.pem")
            self.assertEqual(updated["id"], original_id)


class TestReadAllDataErrors(unittest.TestCase):
    def test_invalid_json_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            dbfile = Path(tmp) / "sshc_db.json"
            dbfile.write_text("{not-json", encoding="utf-8")
            db = mjdb(db_file_name=str(dbfile))
            result = db.read_all_data()
            self.assertIsInstance(result, list)
            self.assertEqual(result, [])

    def test_non_list_json_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            dbfile = Path(tmp) / "sshc_db.json"
            dbfile.write_text('{"foo": []}', encoding="utf-8")
            db = mjdb(db_file_name=str(dbfile))
            result = db.read_all_data()
            self.assertIsInstance(result, list)
            self.assertEqual(result, [])


class TestListReadAlias(unittest.TestCase):
    def test_list_and_read_share_handler(self):
        """`list` is an argparse alias of `read`; both hit the same command path."""
        from src.sshc import __main__

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / ".ssh"
            dbfile = destination / "sshc_db.json"
            destination.mkdir(parents=True, exist_ok=True)
            db = mjdb(db_file_name=str(dbfile))
            db.create_db()
            db.insert_data({
                "name": "alias1",
                "host": "10.0.0.2",
                "port": 22,
                "user": "root",
                "log_level": "INFO",
                "compression": "no",
                "identityfile": "id_rsa",
                "comment": "alias test",
                "groups": [],
            })

            for command in ("read", "list"):
                argv = [
                    "sshc",
                    command,
                    "--destination", str(destination),
                    "--dbfile", str(dbfile),
                ]
                with mock.patch.object(sys, "argv", argv):
                    with mock.patch("builtins.print") as mocked_print:
                        __main__()
                printed = "\n".join(
                    str(c.args[0]) for c in mocked_print.call_args_list if c.args
                )
                self.assertIn("alias1", printed)
                self.assertIn("10.0.0.2", printed)

    def test_list_empty_db_does_not_crash(self):
        from src.sshc import __main__

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / ".ssh"
            dbfile = destination / "sshc_db.json"
            destination.mkdir(parents=True, exist_ok=True)
            mjdb(db_file_name=str(dbfile)).create_db()

            argv = [
                "sshc",
                "list",
                "--destination", str(destination),
                "--dbfile", str(dbfile),
            ]
            with mock.patch.object(sys, "argv", argv):
                with mock.patch("builtins.print") as mocked_print:
                    __main__()
            printed = "\n".join(
                str(c.args[0]) for c in mocked_print.call_args_list if c.args
            )
            self.assertIn("No hosts found in DB.", printed)


class TestDbMetadata(unittest.TestCase):
    def _sample_host(self, name="server1"):
        return {
            "name": name,
            "host": "192.168.0.100",
            "port": 22,
            "user": "ubuntu",
            "log_level": "INFO",
            "compression": "no",
            "identityfile": "id_rsa",
            "comment": "meta test",
            "groups": ["personal"],
        }

    def test_create_db_writes_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            dbfile = Path(tmp) / "sshc_db.json"
            db = mjdb(db_file_name=str(dbfile))
            self.assertTrue(db.create_db())
            raw = json.loads(dbfile.read_text(encoding="utf-8"))
            self.assertIn("meta", raw)
            self.assertIn("hosts", raw)
            self.assertEqual(raw["hosts"], [])
            meta = raw["meta"]
            self.assertEqual(meta["update_count"], 0)
            self.assertEqual(meta["hosts_sha256"], compute_hosts_sha256([]))
            self.assertTrue(meta["created_at"])
            self.assertTrue(meta["created_with_sshc_version"])
            self.assertEqual(meta["created_with_sshc_version"], meta["updated_with_sshc_version"])

    def test_create_db_upgrades_legacy_array(self):
        with tempfile.TemporaryDirectory() as tmp:
            dbfile = Path(tmp) / "sshc_db.json"
            legacy = [{
                "id": "abc",
                "name": "legacy1",
                "host": "10.0.0.9",
                "port": 22,
                "user": "root",
                "log_level": "INFO",
                "compression": "no",
                "identityfile": "id_rsa",
                "comment": "old",
                "groups": [],
            }]
            dbfile.write_text(json.dumps(legacy), encoding="utf-8")
            db = mjdb(db_file_name=str(dbfile))
            self.assertTrue(db.create_db())
            raw = json.loads(dbfile.read_text(encoding="utf-8"))
            self.assertIsInstance(raw, dict)
            self.assertIn("meta", raw)
            self.assertEqual(len(raw["hosts"]), 1)
            self.assertEqual(raw["hosts"][0]["name"], "legacy1")
            self.assertEqual(raw["meta"]["hosts_sha256"], compute_hosts_sha256(raw["hosts"]))
            self.assertEqual(raw["meta"]["update_count"], 0)

    def test_create_db_upgrades_empty_legacy_array(self):
        with tempfile.TemporaryDirectory() as tmp:
            dbfile = Path(tmp) / "sshc_db.json"
            dbfile.write_text("[]", encoding="utf-8")
            db = mjdb(db_file_name=str(dbfile))
            self.assertTrue(db.create_db())
            raw = json.loads(dbfile.read_text(encoding="utf-8"))
            self.assertEqual(raw["hosts"], [])
            self.assertIn("created_at", raw["meta"])
            self.assertEqual(raw["meta"]["hosts_sha256"], compute_hosts_sha256([]))

    def test_mutations_bump_update_count_and_checksum(self):
        with tempfile.TemporaryDirectory() as tmp:
            dbfile = Path(tmp) / "sshc_db.json"
            db = mjdb(db_file_name=str(dbfile))
            db.create_db()
            self.assertEqual(db.read_meta()["update_count"], 0)

            self.assertTrue(db.insert_data(self._sample_host()))
            meta_after_insert = db.read_meta()
            self.assertEqual(meta_after_insert["update_count"], 1)
            self.assertEqual(
                meta_after_insert["hosts_sha256"],
                compute_hosts_sha256(db.read_all_data()),
            )

            self.assertTrue(db.update_data({"name": "server1", "port": 2222}))
            meta_after_update = db.read_meta()
            self.assertEqual(meta_after_update["update_count"], 2)
            self.assertEqual(
                meta_after_update["hosts_sha256"],
                compute_hosts_sha256(db.read_all_data()),
            )

            db.delete_data("server1")
            meta_after_delete = db.read_meta()
            self.assertEqual(meta_after_delete["update_count"], 3)
            self.assertEqual(meta_after_delete["hosts_sha256"], compute_hosts_sha256([]))
            self.assertEqual(meta_after_delete["created_at"], meta_after_insert["created_at"])

    def test_legacy_array_db_still_readable_and_upgrades_on_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            dbfile = Path(tmp) / "sshc_db.json"
            legacy_hosts = [{
                "id": "abc",
                "name": "legacy1",
                "host": "10.0.0.9",
                "port": 22,
                "user": "root",
                "log_level": "INFO",
                "compression": "no",
                "identityfile": "id_rsa",
                "comment": "old",
                "groups": [],
            }]
            dbfile.write_text(json.dumps(legacy_hosts), encoding="utf-8")
            db = mjdb(db_file_name=str(dbfile))
            self.assertEqual(len(db.read_all_data()), 1)

            self.assertTrue(db.insert_data(self._sample_host("new1")))
            raw = json.loads(dbfile.read_text(encoding="utf-8"))
            self.assertIsInstance(raw, dict)
            self.assertIn("meta", raw)
            self.assertEqual(len(raw["hosts"]), 2)
            self.assertEqual(raw["meta"]["update_count"], 1)
            self.assertEqual(raw["meta"]["hosts_sha256"], compute_hosts_sha256(raw["hosts"]))

    def test_checksum_mismatch_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            dbfile = Path(tmp) / "sshc_db.json"
            db = mjdb(db_file_name=str(dbfile))
            db.create_db()
            db.insert_data(self._sample_host())
            raw = json.loads(dbfile.read_text(encoding="utf-8"))
            raw["meta"]["hosts_sha256"] = "0" * 64
            dbfile.write_text(json.dumps(raw), encoding="utf-8")
            with mock.patch("builtins.print") as mocked_print:
                hosts = db.read_all_data()
            self.assertEqual(len(hosts), 1)
            printed = " ".join(str(c.args[0]) for c in mocked_print.call_args_list if c.args)
            self.assertIn("integrity check failed", printed)


class TestOpensshDefaultConfigInclude(unittest.TestCase):
    def test_adds_include_block_to_default_config(self):
        from src.sshc import (
            SSHC_OPENSSH_INCLUDE_BEGIN,
            update_openssh_config_include,
        )

        with tempfile.TemporaryDirectory() as tmp:
            ssh_dir = Path(tmp) / ".ssh"
            ssh_dir.mkdir(parents=True, exist_ok=True)
            sshc_config = ssh_dir / "sshc_ssh_config"
            sshc_config.write_text("# hosts\n", encoding="utf-8")
            openssh_config = ssh_dir / "config"

            changed, _ = update_openssh_config_include(
                str(sshc_config),
                openssh_config_path=str(openssh_config),
            )
            self.assertTrue(changed)
            content = openssh_config.read_text(encoding="utf-8")
            self.assertIn(SSHC_OPENSSH_INCLUDE_BEGIN, content)
            self.assertIn("Include", content)
            self.assertIn(sshc_config.resolve().as_posix(), content)

            changed_again, msg = update_openssh_config_include(
                str(sshc_config),
                openssh_config_path=str(openssh_config),
            )
            self.assertFalse(changed_again)
            self.assertIn("already includes", msg)

    def test_updates_include_when_sshc_config_path_changes(self):
        from src.sshc import update_openssh_config_include

        with tempfile.TemporaryDirectory() as tmp:
            ssh_dir = Path(tmp) / ".ssh"
            ssh_dir.mkdir(parents=True, exist_ok=True)
            openssh_config = ssh_dir / "config"
            first = ssh_dir / "sshc_ssh_config"
            second = ssh_dir / "other_ssh_config"
            first.write_text("a", encoding="utf-8")
            second.write_text("b", encoding="utf-8")

            update_openssh_config_include(str(first), openssh_config_path=str(openssh_config))
            changed, _ = update_openssh_config_include(
                str(second), openssh_config_path=str(openssh_config)
            )
            self.assertTrue(changed)
            self.assertIn(second.resolve().as_posix(), openssh_config.read_text(encoding="utf-8"))


class TestGenerateConfirmOverwrite(unittest.TestCase):
    def test_skips_prompt_when_files_missing_or_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self.assertTrue(confirm_overwrite([base / "a", base / "b"], assume_yes=False))

    def test_accepts_yes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sshc_ssh_config"
            path.write_text("Host x\n", encoding="utf-8")
            with mock.patch("builtins.input", return_value="yes"):
                self.assertTrue(confirm_overwrite([path], assume_yes=False))

    def test_rejects_no(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sshc_ssh_config"
            path.write_text("Host x\n", encoding="utf-8")
            with mock.patch("builtins.input", return_value="n"):
                self.assertFalse(confirm_overwrite([path], assume_yes=False))

    def test_assume_yes_skips_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sshc_ssh_config"
            path.write_text("Host x\n", encoding="utf-8")
            self.assertTrue(confirm_overwrite([path], assume_yes=True))


class TestStatusCommand(unittest.TestCase):
    def _host(self, name="server1", identityfile=None):
        return {
            "name": name,
            "host": "192.168.0.100",
            "port": 22,
            "user": "ubuntu",
            "log_level": "INFO",
            "compression": "no",
            "identityfile": identityfile or "id_rsa",
            "comment": "status test",
            "groups": ["personal"],
        }

    def test_status_empty_db_ok_with_warnings(self):
        from src.sshc import collect_status

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / ".ssh"
            destination.mkdir(parents=True, exist_ok=True)
            dbfile = destination / "sshc_db.json"
            configfile = destination / "sshc_ssh_config"
            inventoryfile = destination / "sshc_ansible_inventory.json"
            mjdb(db_file_name=str(dbfile)).create_db()

            report = collect_status(str(dbfile), str(configfile), str(inventoryfile))
            self.assertTrue(report["ok"])
            self.assertFalse(report["needs_regeneration"])
            self.assertTrue(report["db"]["empty"])
            codes = {i["code"] for i in report["issues"]}
            self.assertIn("db_empty", codes)
            self.assertIn("ssh_config_missing", codes)
            self.assertIn("inventory_missing", codes)
            self.assertTrue(all(i["level"] == "warning" for i in report["issues"]))

    def test_status_detects_integrity_and_needs_regen(self):
        from src.sshc import collect_status, generate_host_entry_string

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / ".ssh"
            destination.mkdir(parents=True, exist_ok=True)
            keyfile = destination / "id_rsa"
            keyfile.write_text("dummy", encoding="utf-8")
            dbfile = destination / "sshc_db.json"
            configfile = destination / "sshc_ssh_config"
            inventoryfile = destination / "sshc_ansible_inventory.json"

            db = mjdb(db_file_name=str(dbfile))
            db.create_db()
            db.insert_data(self._host(identityfile=str(keyfile)))

            # Corrupt checksum
            raw = json.loads(dbfile.read_text(encoding="utf-8"))
            raw["meta"]["hosts_sha256"] = "0" * 64
            dbfile.write_text(json.dumps(raw), encoding="utf-8")

            report = collect_status(str(dbfile), str(configfile), str(inventoryfile))
            self.assertFalse(report["ok"])
            self.assertTrue(report["needs_regeneration"])
            codes = {i["code"] for i in report["issues"]}
            self.assertIn("integrity_mismatch", codes)
            self.assertIn("ssh_config_missing", codes)
            self.assertIn("inventory_missing", codes)
            self.assertIn("needs_regeneration", codes)

            # Generate in-sync artifacts and restore checksum
            hosts = mjdb(db_file_name=str(dbfile)).read_all_data()
            raw = json.loads(dbfile.read_text(encoding="utf-8"))
            raw["meta"]["hosts_sha256"] = compute_hosts_sha256(hosts)
            dbfile.write_text(json.dumps(raw, indent=2), encoding="utf-8")

            configfile.write_text("# header\n", encoding="utf-8")
            h = hosts[0]
            generate_host_entry_string(
                name=h["name"], host=h["host"], port=h["port"], user=h["user"],
                log_level=h["log_level"], compression=h["compression"],
                identityfile=h["identityfile"], configfile=str(configfile),
                comment=h["comment"],
            )
            generate_ansible_inventory_file(
                {
                    "all": {
                        "hosts": {
                            h["name"]: {
                                "ansible_host": h["host"],
                                "ansible_port": h["port"],
                                "ansible_user": h["user"],
                                "ansible_ssh_private_key_file": h["identityfile"],
                            }
                        },
                        "children": {},
                    }
                },
                str(inventoryfile),
                file_type="json",
            )

            report_ok = collect_status(str(dbfile), str(configfile), str(inventoryfile))
            self.assertTrue(report_ok["ok"])
            self.assertFalse(report_ok["needs_regeneration"])
            self.assertTrue(report_ok["ssh_config"]["in_sync"])
            self.assertTrue(report_ok["ansible_inventory"]["in_sync"])

    def test_status_warns_missing_identity_file(self):
        from src.sshc import collect_status

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / ".ssh"
            destination.mkdir(parents=True, exist_ok=True)
            dbfile = destination / "sshc_db.json"
            configfile = destination / "sshc_ssh_config"
            inventoryfile = destination / "sshc_ansible_inventory.json"
            db = mjdb(db_file_name=str(dbfile))
            db.create_db()
            db.insert_data(self._host(identityfile=str(destination / "missing.pem")))

            report = collect_status(str(dbfile), str(configfile), str(inventoryfile))
            codes = {i["code"] for i in report["issues"]}
            self.assertIn("identityfile_missing", codes)
            self.assertEqual(len(report["identity_files"]["missing"]), 1)

    def test_status_cli_json_exit_code(self):
        from src.sshc import __main__

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / ".ssh"
            destination.mkdir(parents=True, exist_ok=True)
            dbfile = destination / "sshc_db.json"
            mjdb(db_file_name=str(dbfile)).create_db()
            argv = [
                "sshc", "status", "--json",
                "--destination", str(destination),
                "--dbfile", str(dbfile),
                "--configfile", str(destination / "sshc_ssh_config"),
                "--inventoryfile", str(destination / "sshc_ansible_inventory.json"),
            ]
            with mock.patch.object(sys, "argv", argv):
                with mock.patch("builtins.print") as mocked_print:
                    __main__()
            payload = mocked_print.call_args.args[0]
            report = json.loads(payload)
            self.assertTrue(report["ok"])


if __name__ == "__main__":
    unittest.main()
