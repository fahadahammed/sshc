import argparse
import json
import os
import datetime
import sys
import uuid
import pprint


def get_random_id():
    the_id = uuid.uuid4()
    return str(the_id)


def read_pyproject_toml():
    the_pyproject_toml_file = os.path.dirname(os.path.realpath(__file__)) \
                              + os.sep + "pyproject.toml"
    if not os.path.exists(the_pyproject_toml_file):
        the_pyproject_toml_file = the_pyproject_toml_file.replace("/src", "")
    with open(file=the_pyproject_toml_file, mode='r', encoding='utf-8') as tomlfile:
        lines = tomlfile.readlines()
        for line in lines:
            if "version" in line:
                return line.split('"')[-2]
        return ""


class mjdb:
    def __init__(self, db_file_name="sshc_db.json"):
        self.db_file_name = db_file_name

    def create_db(self):
        try:
            if not os.path.exists(self.db_file_name):
                with open(self.db_file_name, 'a', encoding='utf-8') as opened_db:
                    json.dump([], opened_db)
            return True
        except Exception as ex:
            print(ex)
            return False

    def insert_data(self, data):
        if not os.path.exists(self.db_file_name):
            print(f"{self.db_file_name} file doesn't exists. Please initiate DB first.")
            sys.exit()
        try:
            data["id"] = get_random_id()
            existing_data = self.read_all_data()
            to_insert = existing_data + [data]
            all_data = self.read_all_data()
            data_exists = [x for x in all_data if x.get("name") == data.get("name")]
            if not data_exists:
                with open(self.db_file_name, 'w', encoding='utf-8') as opened_db:
                    json.dump(to_insert, opened_db)
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
        if all_data:
            to_insert = []
            for data in all_data:
                if data.get("name") != hostname:
                    to_insert.append(data)
            with open(self.db_file_name, 'w', encoding='utf-8') as opened_db:
                json.dump(to_insert, opened_db)
            return to_insert
        else:
            to_insert = []
            with open(self.db_file_name, 'w', encoding='utf-8') as opened_db:
                json.dump(to_insert, opened_db)
            return to_insert

    def read_all_data(self):
        if not os.path.exists(self.db_file_name):
            print(f"{self.db_file_name} file doesn't exists. Please initiate DB first.")
            sys.exit("DB file doesn't exists. Please initiate first.")
        try:
            with open(self.db_file_name, 'r', encoding='utf-8') as opened_db:
                to_return = json.load(opened_db)
            return to_return
        except Exception as ex:
            print(ex)
            return {}


def cleanup_file(configfile):
    configfiledir = configfile.replace("/" + configfile.split("/")[-1], "")

    try:
        os.remove(configfile)
    except Exception as ex:
        print(ex)
        if len(configfile.split("/")) > 2:
            os.mkdir(configfiledir)
        with open(configfile, "w", encoding='utf-8') as openconfig:
            openconfig.write("")


def insert_timestamp_into_configfile(configfile):
    dt_now = str(datetime.datetime.utcnow())
    with open(configfile, "a", encoding='utf-8') as openconfig:
        openconfig.write("# Generated at: " + dt_now)
        openconfig.write("\n")


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


def generate_ansible_inventory_file(data_to_write, inventory_file_name):
    with open(file=inventory_file_name, mode="w", encoding='utf-8') as thefile:
        json.dump(data_to_write, thefile)


def __main__():
    parser = argparse.ArgumentParser(description='SSH Config and Ansible Inventory Generator !')

    parser.add_argument('--version', action='version', version="sshc, " + "v" + read_pyproject_toml())

    subparser = parser.add_subparsers(dest="command", description="The main command of this CLI tool.",
                                      help="The main commands have their own arguments.", required=True)

    init = subparser.add_parser("init", help="Initiate Host DB !")
    insert = subparser.add_parser("insert", help="Insert host information !")
    delete = subparser.add_parser("delete", help="Delete host information !")
    read = subparser.add_parser("read", help="Read Database !")
    generate = subparser.add_parser("generate", help="Generate necessary config files !")

    init.add_argument('--destination', help='Config HOME?',
                        default=f"{os.getenv('HOME')}/.ssh")
    init.add_argument('--dbfile', help='SSHC DB File.',
                        default=f"{os.getenv('HOME')}/.ssh/sshc_db.json")

    insert.add_argument('--name', help='Server Name?', required=True)
    insert.add_argument('--host', help='SSH Host?', required=True)
    insert.add_argument('--user', help='SSH User?', default="root")
    insert.add_argument('--port', help='SSH Port?', default=22)
    insert.add_argument('--comment', help='SSH Identity File.', default="No Comment.")
    insert.add_argument('--loglevel', help='SSH Log Level.',
                        choices=["INFO", "DEBUG", "ERROR", "WARNING"],
                        default="INFO")
    insert.add_argument('--compression', help='SSH Connection Compression.',
                        choices=["yes", "no"], default="yes")
    insert.add_argument('--groups', nargs='+', help='Which group to include?', default=[])
    insert.add_argument('--identityfile', help='SSH Default Identity File Location. i.e. id_rsa',
                        default=f"{os.getenv('HOME')}/.ssh/id_rsa")
    insert.add_argument('--destination', help='Config HOME?',
                        default=f"{os.getenv('HOME')}/.ssh")
    insert.add_argument('--dbfile', help='SSHC DB File.',
                        default=f"{os.getenv('HOME')}/.ssh/sshc_db.json")

    delete.add_argument('--hostname', help="Server Host Name?", required=True)

    read.add_argument('--hostname', help="Server Host Name?", required=False)
    read.add_argument('--verbose', help="Verbosity?",
                      choices=["yes", "no"], required=False)
    read.add_argument('--destination', help='Config HOME?',
                        default=f"{os.getenv('HOME')}/.ssh")
    read.add_argument('--dbfile', help='SSHC DB File.',
                        default=f"{os.getenv('HOME')}/.ssh/sshc_db.json")

    generate.add_argument('--configfile', help='SSH Config File.',
                        default=f"{os.getenv('HOME')}/.ssh/sshc_ssh_config")
    generate.add_argument('--inventoryfile', help='Ansible Inventory File.',
                        default=f"{os.getenv('HOME')}/.ssh/sshc_ansible_inventory.json")
    generate.add_argument('--destination', help='Config HOME?',
                        default=f"{os.getenv('HOME')}/.ssh")
    generate.add_argument('--dbfile', help='SSHC DB File.',
                        default=f"{os.getenv('HOME')}/.ssh/sshc_db.json")


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

        if not name or not host or not port or not user or not groups:
            sys.exit("Some required parameters missing.")

        data = {
            "name": name, "host": host, "port": port, "user": user,
            "log_level": loglevel, "compression": compression, "identityfile": identityfile,
            "comment": comment, "groups": groups
        }
        print("Inserting data...")
        mjdb(db_file_name=dbfile).insert_data(data=data)
        print("Done.")
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
    elif command == "generate":
        print("Generating config files from DB.")
        print("Generating SSH Config File...")
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
        if not os.path.exists(inventoryfile):
            print(f"{inventoryfile} file doesn't exists, creating.")
            with open(inventoryfile, 'w', encoding='utf-8') as file:
                file.write("{}")
            print(f"{inventoryfile} file created.")
        the_data = mjdb(db_file_name=dbfile).read_all_data()
        if the_data:
            all_hosts = {}
            groups = []
            cleanup_file(configfile=configfile)
            with open(file=configfile, mode="a+", encoding='utf-8') as thefile:
                thefile.write(f"# Generated At: {datetime.datetime.utcnow()}\n\n")
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
                    "generated_at": str(datetime.datetime.utcnow())
                }
            }
            generate_ansible_inventory_file(data_to_write=ansible_inventory_data,
                                            inventory_file_name=inventoryfile)
            print("Done.")
        else:
            sys.exit("No data in DB.")
    elif command == "read":
        print("Trying to read DB.")
        # Home of the config
        destination = args.destination
        if not os.path.exists(destination):
            print(f"{destination} directory is not ready.")
            os.makedirs(destination)
            print(f"{destination} directory is created.")
        dbfile = args.dbfile
        if not args.hostname:
            to_return = mjdb(db_file_name=dbfile).read_all_data()
        else:
            to_return = [x for x in mjdb(db_file_name=dbfile).read_all_data()
                         if x.get("name") == str(args.hostname)]
        p_p = pprint.PrettyPrinter(indent=4)
        if args.verbose == "yes":
            p_p.pprint(to_return)
        else:
            p_p.pprint([f'{x.get("name")} {x.get("host")}' for x in to_return])
    else:
        print("There is nothing to execute.")
