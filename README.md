# ssh-config-ansible-inventory-generator
This tool should help you manage ssh config file with hosts as well as ansible hosts or inventory file.

## Usage

### help

```bash
% python3 sshc.py --help
```

```bash
usage: sshc.py [-h] (--init {yes,no} | --insert {yes,no} | --read {yes,no} | --generate {yes,no})
               [--name NAME] [--host HOST] [--user USER] [--port PORT] [--idf IDF]
               [--comment COMMENT] [--configfile CONFIGFILE] [--groups GROUPS] [--hn HN]

SSH Config and Ansible Inventory Generator !

optional arguments:
  -h, --help            show this help message and exit
  --init {yes,no}       Initialize DB?
  --insert {yes,no}     Insert data?
  --read {yes,no}       Read Inventory?
  --generate {yes,no}   Generate SSH Config from Database?
  --name NAME           Server Name?
  --host HOST           SSH Host?
  --user USER           SSH User?
  --port PORT           SSH Port?
  --idf IDF             SSH Identity File?
  --comment COMMENT     SSH Identity File?
  --configfile CONFIGFILE
                        SSH Config File?
  --groups GROUPS       Which group to include?
  --hn HN               Which Host by giving Host Number?
```

### Need the DB to be initiated for the first time

```bash
% python3 sshc.py --init yes
```

### How to insert host information to the Database?

```bash
% python3 sshc.py --insert yes --name Google --host 8.8.8.8 --port 22 --user groot --idf /home/fahad/fahad.pem --comment "This is the server where you are not authorized to have access." --configfile /home/fahad/.ssh/config --groups google, fun
```

### How to generate ssh config and as well as ansible inventory file

```bash
% python3 sshc.py --generate yes
```
