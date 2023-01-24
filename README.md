# sshc - SSH Configuration Management Tool with Ansible Inventory Generation
This tool can help you manage ssh config files with hosts as well as ansible inventory file.

## What it does?

1. It creates a host database.
2. Create SSH config from that host database.
3. Create Ansible inventory from that same host database.

### Example of generated SSH config
```ini
# Generated At: 2023-01-24 11:35:25.885044

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
        "generated_at": "2023-01-24 11:35:25.885044"
    }
}
```

## Why?
### Problem it tried to solve
- Working with a bunch of servers gets messy to track those down.
- Managing Ansible Inventory and also SSH config file separate is redundant.

### Tried to solve via
- Using a JSON file as a common database of hosts.
- Setting name, ports, user, private key, ssh compression, ssh connection log level etc when inserting a host information.
- Set groups, do comment on specific host for host management.
- Well sorted config files.
- Ansible inventory is managed using JSON file.
- Add host to multiple groups which end up with ansible hosts group.
- Remove ~~and update~~ host entry easily.

## Description
### Structure

1. Insert host information to a JSON file as a DB.
2. Generate SSH Config file and an Ansible Inventory file.

### Technology Stack
1. python
2. json
3. openssh
4. ansible

### Dependency

#### Runtime
- Python3.7+
- Linux

#### Development
- Poetry

## Installation

```shell
% pip3 install sshc --upgrade
```

## Usage

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

### Step 2: Insert host information to the Database
#### Pattern
```shell
usage: sshc insert [-h] --name NAME --host HOST [--user USER] [--port PORT] [--comment COMMENT] [--loglevel {INFO,DEBUG,ERROR,WARNING}] [--compression {yes,no}]
                   [--groups GROUPS [GROUPS ...]] [--identityfile IDENTITYFILE] [--destination DESTINATION] [--dbfile DBFILE]

options:
  -h, --help            show this help message and exit
  --name NAME           Server Name?
  --host HOST           SSH Host?
  --user USER           SSH User?
  --port PORT           SSH Port?
  --comment COMMENT     SSH Identity File.
  --loglevel {INFO,DEBUG,ERROR,WARNING}
                        SSH Log Level.
  --compression {yes,no}
                        SSH Connection Compression.
  --groups GROUPS [GROUPS ...]
                        Which group to include?
  --identityfile IDENTITYFILE
                        SSH Default Identity File Location. i.e. id_rsa
  --destination DESTINATION
                        Config HOME?
  --dbfile DBFILE       SSHC DB File.
```

#### Example
```shell
% sshc insert --name Google --host 8.8.8.8 --port 22 --user groot --identityfile /home/fahad/fahad.pem --comment "This is the server where you are not authorized to have access." --configfile /home/fahad/.ssh/config --groups google, fun
```

### Step 3: Generate ssh config and as well as ansible inventory file
#### Pattern
```shell
usage: sshc generate [-h] [--configfile CONFIGFILE] [--inventoryfile INVENTORYFILE] [--destination DESTINATION] [--dbfile DBFILE]

options:
  -h, --help            show this help message and exit
  --configfile CONFIGFILE
                        SSH Config File.
  --inventoryfile INVENTORYFILE
                        Ansible Inventory File.
  --destination DESTINATION
                        Config HOME?
  --dbfile DBFILE       SSHC DB File.
```
#### Example

```shell
% python3 sshc.py generate
```

This command will read all the entries in the DB and generate
1. SSH config file in your preferred directory or default one(i.e. $HOME/.ssh/sshc_ssh_config).
2. Ansible Inventory file will be created at your preferred directory or in default one (i.e. $HOME/.ssh/sshc_ansible_inventory.json).

If you stick with default directory you will find the generated files in:
1. Default Directory: `$HOME/.ssh`
2. Generated Ansible Inventory: `$HOME/.ssh/sshc_ansible_inventory.json`
3. Generated SSH Config: `$HOME/.ssh/sshc_ssh_config`

You can use these configs like below.

For SSH,
```shell
% ssh -F $HOME/.ssh/sshc_ssh_config
```

For Ansible,
```shell
% ansible -i $HOME/.ssh/sshc_ansible_inventory.json all --list-host
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
usage: sshc [-h] [--version] {init,insert,delete,read,generate} ...

SSH Config and Ansible Inventory Generator !

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit

subcommands:
  The main command of this CLI tool.

  {init,insert,delete,read,generate}
                        The main commands have their own arguments.
    init                Initiate Host DB !
    insert              Insert host information !
    delete              Delete host information !
    read                Read Database !
    generate            Generate necessary config files !
```

### Delete Inserted Data

```shell
% sshc delete --hostname <HOSTNAME>
```

### Read DB Data

```shell
% sshc read
```

You can pass verbose too

```shell
% sshc read --verbose yes
```

## Known issues or Limitations

- Tested in Ubuntu 22.04
- Windows is not tested

## Getting help
If you have questions, concerns, bug reports and others, please file an issue in this repository's Issue Tracker.

## Getting involved
If you want to contribute to this tool, feel free to fork the repo and create Pull request with your changes.
Keep in mind to
- include better comment to understand.
- create PR to **development** branch.

---
## Author
- [Fahad Ahammed - DevOps Enthusiast - Dhaka, Bangladesh](https://github.com/fahadahammed)