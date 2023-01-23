# ssh-config-ansible-inventory-generator
This tool should help you manage ssh config file with hosts as well as ansible hosts or inventory file.

## Structure

1. Insert host information to a JSON file as a DB.
2. Generate SSH Config file and an Ansible Inventory file.

## Install

```bash
% pip3 install sshc
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
sshc read
```