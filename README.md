# sshc - SSH Configuration Management Tool with Ansible Inventory Generation
This tool can help you manage ssh config files with hosts as well as ansible inventory file.

## Why?
### Problem it tried to solve
- Working with a bunch of servers gets messy to track those down.
- Managing Ansible Inventory and also SSH config file separate is redundant.

### Gave solution through
- Uses a JSON file as a common database of hosts.
- Set name, set ports, user, private key when inserting a host information.
- Set groups, do comment on specific host for future understanding.
- Well sorted config files.
- Ansible inventory is managed using JSON file.
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