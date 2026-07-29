# sshc - SSH Configuration Management Tool with Ansible Inventory Generation
This tool can help you manage ssh config files with hosts as well as ansible inventory file.

## What it does?

1. It creates a host database (JSON document with metadata + hosts).
2. Create SSH config from that host database.
3. Create Ansible inventory from that same host database.

### Example of generated SSH config
```ini
# Generated At: 2023-01-24 11:35:25.885044
# sshc Version: 3.0.0

# -- <
Host server1
HostName 192.168.0.100
Port 22
User ubuntu
IdentityFile /home/fahad/.ssh/id_rsa
LogLevel INFO
Compression yes
# Comment: Personal Server: ONE
# -- >

# -- <
Host server2
HostName 10.10.0.102
Port 4522
User root
IdentityFile /home/fahad/.ssh/id_rsa
LogLevel DEBUG
Compression no
# Comment: Personal Server: TWO
# -- >
```
### Example of generated Ansible Inventory
```json
{
    "all": {
        "hosts": {
            "server1": {
                "ansible_host": "192.168.0.100",
                "ansible_port": 22,
                "ansible_user": "ubuntu",
                "ansible_ssh_private_key_file": "/home/fahad/.ssh/id_rsa"
            },
            "server2": {
                "ansible_host": "10.10.0.102",
                "ansible_port": 4522,
                "ansible_user": "root",
                "ansible_ssh_private_key_file": "/home/fahad/.ssh/id_rsa"
            }
        },
        "children": {
            "personal": {
                "hosts": {
                    "server1": null,
                    "server2": null
                }
            },
            "home": {
                "hosts": {
                    "server1": null
                }
            },
            "storage": {
                "hosts": {
                    "server2": null
                }
            }
        }
    },
    "others": {
        "generated_at": "2023-01-24 11:35:25.885044",
        "sshc_version": "3.0.0"
    }
}
```

## Why?
### Problem it tried to solve
- Working with a bunch of servers gets messy to track those down.
- Managing Ansible Inventory and also SSH config file separate is redundant.

### Tried to solve via
- Using a JSON file as a common database of hosts (with creation/update metadata and a SHA-256 integrity checksum).
- Setting name, ports, user, private key, ssh compression, ssh connection log level etc when inserting a host information.
- Set groups, do comment on specific host for host management.
- Well sorted config files.
- Ansible inventory is managed using JSON file (YAML/YML also supported).
- Add host to multiple groups which end up with ansible hosts group.
- Remove and update host entry easily (partial update only changes fields you pass).

## Description
### Structure

1. Insert host information to a JSON file as a DB.
2. Generate SSH Config file and an Ansible Inventory file.

### Technology Stack
1. python
2. json
3. yaml
4. openssh
5. ansible

### Dependency

#### Runtime
- Python 3.7+
- Linux or Windows (paths use the user home directory via `pathlib`, typically `~/.ssh` or `%USERPROFILE%\.ssh`)

#### Development
- Poetry

## Installation

```shell
% pip3 install sshc --upgrade
```

See [CHANGELOG.md](CHANGELOG.md) for release history and unreleased changes.

## Usage

Default files live under your user home `.ssh` directory (cross-platform):

| Artifact | Default path |
|----------|----------------|
| Host DB | `<home>/.ssh/sshc_db.json` |
| SSH config | `<home>/.ssh/sshc_ssh_config` |
| Ansible inventory | `<home>/.ssh/sshc_ansible_inventory.json` |

On Linux/macOS that is usually `$HOME/.ssh/...`. On Windows it is typically `%USERPROFILE%\.ssh\...`.

### Step 1: Need the DB to be initiated for the first time
#### Pattern
```shell
usage: sshc init [-h] [--destination DESTINATION] [--dbfile DBFILE]

options:
  -h, --help            show this help message and exit
  --destination DESTINATION
                        Config HOME?
  --dbfile DBFILE       SSHC DB File.

```

#### Example
```shell
% sshc init
```

This creates `<home>/.ssh/sshc_db.json` as a document with `meta` (created/updated timestamps and sshc versions, `update_count`, `hosts_sha256`) and an empty `hosts` array.

If the DB file already exists as a legacy JSON array (`[]` or a list of hosts), `init` upgrades it in place to the document format and adds metadata without deleting hosts.

### Step 2: Insert host information to the Database
#### Pattern
```shell
usage: sshc insert [-h] --name NAME --host HOST [--user USER] [--port PORT] [--comment COMMENT] [--loglevel {INFO,DEBUG,ERROR,WARNING}] [--compression {yes,no}]
                   [--groups GROUPS [GROUPS ...]] [--identityfile IDENTITYFILE] [--destination DESTINATION] [--dbfile DBFILE]

options:
  -h, --help            show this help message and exit
  --name NAME           Server Name?
  --host HOST           SSH Host?
  --user USER           SSH User? (default: root)
  --port PORT           SSH Port? (default: 22)
  --comment COMMENT     Host comment.
  --loglevel {INFO,DEBUG,ERROR,WARNING}
                        SSH Log Level.
  --compression {yes,no}
                        SSH Connection Compression.
  --groups GROUPS [GROUPS ...]
                        Which groups to include? (space-separated)
  --identityfile IDENTITYFILE
                        SSH identity file location (default: <home>/.ssh/id_rsa)
  --destination DESTINATION
                        Config HOME?
  --dbfile DBFILE       SSHC DB File.
```

#### Example
```shell
% sshc insert --name Google --host 8.8.8.8 --port 22 --user groot --identityfile /home/fahad/fahad.pem --comment "This is the server where you are not authorized to have access." --groups google fun
```

If a host `name` already exists, insert is skipped and a message is printed.

### Step 3: Generate ssh config and as well as ansible inventory file
#### Pattern
```shell
usage: sshc generate [-h] [--configfile CONFIGFILE] [--inventoryfile INVENTORYFILE] [--destination DESTINATION] [--dbfile DBFILE] [--filetype {json,yaml,yml}]

options:
  -h, --help            show this help message and exit
  --configfile CONFIGFILE
                        SSH Config File.
  --inventoryfile INVENTORYFILE
                        Ansible Inventory File.
  --destination DESTINATION
                        Config HOME?
  --dbfile DBFILE       SSHC DB File.
  --filetype {json,yaml,yml}
                        Preferred file type for Ansible inventory. Default is json and you can choose yaml too.
```

#### Example

```shell
% sshc generate
```

This command will read all the entries in the DB and generate
1. SSH config file in your preferred directory or the default (`<home>/.ssh/sshc_ssh_config`).
2. Ansible inventory file in your preferred directory or the default (`<home>/.ssh/sshc_ansible_inventory.json`).

If you stick with the default directory you will find the generated files in:
1. Default Directory: `<home>/.ssh`
2. Generated Ansible Inventory: `<home>/.ssh/sshc_ansible_inventory.json`
3. Generated SSH Config: `<home>/.ssh/sshc_ssh_config`

You can use these configs like below.

For SSH,
```shell
% ssh -F $HOME/.ssh/sshc_ssh_config
```

For Ansible,
```shell
% ansible -i $HOME/.ssh/sshc_ansible_inventory.json all --list-host
```

On Windows (PowerShell), use the same idea with your profile path, for example:
```powershell
ssh -F $env:USERPROFILE\.ssh\sshc_ssh_config
```

**Note: If you choose default SSH config file location and ansible host file location, sshc will replace the file. Be careful.**

#### Recommended Way of Generating Configurations
- There are two terms to keep in mind.
  - SSH default
  - sshc default
- Use sshc default paths which is different from SSH and Ansible default config.
- Use those newly created files(which should be separate than default one) either passing `-F` for SSH and `-i` for Ansible.

### Others
Help message of the tool
```shell
% sshc --help
```

```shell
usage: sshc [-h] [--version] {init,insert,delete,update,read,generate,status} ...

SSH Config and Ansible Inventory Generator !

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit

subcommands:
  The main command of this CLI tool.

  {init,insert,delete,update,read,generate,status}
                        The main commands have their own arguments.
    init                Initiate Host DB !
    insert              Insert host information !
    delete              Delete host information !
    update              Update host information !
    read (list)         Read / list host database !
    generate            Generate necessary config files !
    status              Check DB integrity and generated file sync !
```

### Delete Inserted Data

```shell
% sshc delete --hostname <HOSTNAME>
```

Optional path overrides: `--destination`, `--dbfile`.

### Update Inserted Data

Only fields you pass are changed; omitted fields stay as they are in the DB.

```shell
usage: sshc update [-h] --name NAME [--host HOST] [--user USER] [--port PORT] [--comment COMMENT]
                   [--loglevel {INFO,DEBUG,ERROR,WARNING}] [--compression {yes,no}] [--groups GROUPS [GROUPS ...]]
                   [--identityfile IDENTITYFILE] [--destination DESTINATION] [--dbfile DBFILE]

options:
  -h, --help            show this help message and exit
  --name NAME           Server Name?
  --host HOST           SSH Host?
  --user USER           SSH User?
  --port PORT           SSH Port?
  --comment COMMENT     Host comment (omit to leave unchanged).
  --loglevel {INFO,DEBUG,ERROR,WARNING}
                        SSH Log Level (omit to leave unchanged).
  --compression {yes,no}
                        SSH Connection Compression (omit to leave unchanged).
  --groups GROUPS [GROUPS ...]
                        Which group to include? (omit to leave unchanged)
  --identityfile IDENTITYFILE
                        SSH identity file (omit to leave unchanged)
  --destination DESTINATION
                        Config HOME?
  --dbfile DBFILE       SSHC DB File.
```

#### Example
```shell
% sshc update --name google --port 2222
```

If the host name is not in the DB, update will insert instead (then `--host` and `--port` are required).

### Read / list DB Data

`list` is a synonym for `read` (same options and output).

```shell
% sshc read
% sshc list
```

You can pass verbose too (prints DB metadata and hosts)

```shell
% sshc read --verbose yes
% sshc list --verbose yes
```

### Status / health check

Check DB integrity, emptiness, identity-file paths, and whether SSH config / Ansible inventory match the DB (or need `sshc generate`).

```shell
% sshc status
% sshc status --json
% sshc status --dbfile PATH --configfile PATH --inventoryfile PATH
```

- Exit code `0` when there are no error-level issues (warnings alone are OK).
- Exit code `1` when integrity fails, generated files are missing/out of sync while hosts exist, or the DB is unusable.
- Missing generated files with an **empty** DB are warnings; with hosts present they are errors and set `needs_regeneration`.

## Known issues or Limitations

- Tested on Ubuntu 22.04 and Windows (path handling uses `pathlib.Path.home()`, typically `%USERPROFILE%\.ssh` on Windows).
- OpenSSH client / Ansible availability on Windows depends on your local install; sshc itself generates the config and inventory files portably.

## Getting help
If you have questions, concerns, bug reports and others, please file an issue in this repository's Issue Tracker.

## Getting involved
If you want to contribute to this tool, feel free to fork the repo and create Pull request with your changes.
Keep in mind to
- include better comment to understand.
- create PR to **development** branch.
- check the `Context/` directory for maintainer-oriented architecture notes, gotchas, and todo tracking.

---
## Author
- [Fahad Ahammed - DevOps Enthusiast - Dhaka, Bangladesh](https://github.com/fahadahammed)
