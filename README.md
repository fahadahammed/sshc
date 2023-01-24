# sshc - SSH Configuration Management Tool with Ansible Inventory Generation
The purpose of this tool is to help you manage ssh config files with hosts as well as ansible inventory file management.

#### Structure

1. Insert host information to a JSON file as a DB.
2. Generate SSH Config file and an Ansible Inventory file.

#### Technology Stack
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

```bash
% pip3 install sshc --upgrade
```

## Usage

### Step 1: Need the DB to be initiated for the first time

```bash
% sshc init
```

### Step 2: Insert host information to the Database

```bash
% sshc insert --name Google --host 8.8.8.8 --port 22 --user groot --identityfile /home/fahad/fahad.pem --comment "This is the server where you are not authorized to have access." --configfile /home/fahad/.ssh/config --groups google, fun
```

### Step 3: Generate ssh config and as well as ansible inventory file

```bash
% python3 sshc.py generate
```
This command will read all the entries in the DB and generate
1. SSH config file in your preferred directory or default one(i.e. $HOME/.ssh/config).
2. Ansible Inventory file will be created at your preferred directory or in default one.

If you do not change default directory, then you will be able to use the SSH configs immediately. But Ansible inventory 
will not be created in its default directory. You need to choose the inventory file or create link file.

For SSH,
```bash
% ssh -F <DIR>/config
```

For Ansible,
```bash
% ansible -i <DIR>/hosts.json all --list-host
```

### Others
Help message of the tool
```bash
% sshc --help
```

```bash
usage: sshc [-h] [--version] [--destination DESTINATION] [--identityfile IDENTITYFILE] [--configfile CONFIGFILE] [--dbfile DBFILE] [--inventoryfile INVENTORYFILE]
            {init,insert,delete,read,generate} ...

SSH Config and Ansible Inventory Generator !

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --destination DESTINATION
                        Config HOME?
  --identityfile IDENTITYFILE
                        SSH Default Identity File Location. i.e. id_rsa
  --configfile CONFIGFILE
                        SSH Config File.
  --dbfile DBFILE       SSHC DB File.
  --inventoryfile INVENTORYFILE
                        Ansible Inventory File.

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

```bash
% sshc delete --hostname <HOSTNAME>
```

### Read DB Data

```bash
% sshc read
```

You can pass verbose too

```bash
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