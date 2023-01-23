# ssh-config-ansible-inventory-generator
This tool should help you manage ssh config file with hosts as well as ansible hosts or inventory file.

## Usage

### help

```bash
% python3 sshc.py --help
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

### Need the DB to be initiated for the first time

```bash
% sshc init
```

### How to insert host information to the Database?

```bash
% sshc insert --name Google --host 8.8.8.8 --port 22 --user groot --identityfile /home/fahad/fahad.pem --comment "This is the server where you are not authorized to have access." --configfile /home/fahad/.ssh/config --groups google, fun
```

### How to generate ssh config and as well as ansible inventory file

```bash
% python3 sshc.py generate
```