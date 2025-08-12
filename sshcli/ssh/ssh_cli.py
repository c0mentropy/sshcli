import click
import yaml
import os
import json
import asyncio

import logging
import logging.config

from ..utils.extract_host import Hosts
from ..utils.inner_dict import InnerDict

from .ssh_manager import *

sshcli_version_message = f"""
SSH-%(prog)s version %(version)s
Author: {sshcli_author}
Email: {sshcli_author_email}
Github: {sshcli_git_url}
""".strip()

# SSHCli Class
class SSHCli:
    def __init__(self, hosts_file: str = "./hosts.txt", network_segment: str = "",
                 username: str = "", password: str = "",
                 private_key_path : str = "",
                 port: int = 22, timeout: int = 3, 
                 log_config_file_path: str = "", log_level: str = "",
                 is_save: bool = False, save_user_datas_file_path: str = './hosts.json',
                 proxy: bool = False, proxy_config_file_path: str = ""):
        
        self.hosts_file = hosts_file
        self.network_segment = network_segment
        self.username = username
        self.password = password

        self.private_key_path = private_key_path

        self.port = port
        self.timeout = timeout

        self.log_config_file_path = log_config_file_path
        self.log_level = log_level

        self.is_save = is_save
        self.save_user_datas_file_path = save_user_datas_file_path

        self.proxy = proxy
        self.proxy_config_file_path = proxy_config_file_path

        self.ssh_manager = None

        current_script_path = os.path.abspath(__file__)
        current_script_dir = os.path.dirname(current_script_path)
        current_script_parent_dir = os.path.dirname(current_script_dir)
        # Log
        if log_config_file_path == "":
            # parent_dir = os.path.dirname(current_script_dir)
            log_config_file_path = os.path.join(current_script_parent_dir, "conf/logging_config.yaml")

        with open(log_config_file_path, 'r') as file:
            log_config = yaml.safe_load(file)

        logging.config.dictConfig(log_config)

        self.logger = logging.getLogger()

        if log_level != "":
            self.set_log_level("root", log_level)
        
        self.logger.info(painting_name)
        self.logger.info(f"[sshcli] logging config file found: {log_config_file_path}")

        self.api = InnerDict()

        # self.api.interactive = self.run_interactive
        methods = [name for name in dir(self) if callable(getattr(self, name))]

        for method_name in methods:
            if "run_" in method_name:
                self.api[method_name.replace("run_", "")] = getattr(self, method_name)

    
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

    async def connect(self):
        
                # Configure
        _, ext = os.path.splitext(self.hosts_file)

        if self.network_segment != "":
            if "/" in self.network_segment:
                extract_hosts = Hosts()
                extract_hosts.extract_from_network_segment(self.network_segment, self.port)
                hosts = extract_hosts.hosts
            else:
                hosts = [self.network_segment]

            ssh_manager = SSHManager(hosts=hosts, 
                                     username=self.username, password=self.password,
                                     private_key_path=self.private_key_path,
                                     port=self.port, timeout=self.timeout, 
                                     log_config_file_path=self.log_config_file_path, log_level=self.log_level, 
                                     proxy=self.proxy, proxy_config_file_path=self.proxy_config_file_path)
        elif ext == '.txt':
            extract_hosts = Hosts()
            extract_hosts.extract_from_hosts_file(self.hosts_file, self.port)

            # Create SSHManager instance with hosts, username, and password
            ssh_manager = SSHManager(hosts=extract_hosts.hosts, 
                                     username=self.username, password=self.password,
                                     private_key_path=self.private_key_path,
                                     port=self.port, timeout=self.timeout, 
                                     log_config_file_path=self.log_config_file_path, log_level=self.log_level,
                                     proxy=self.proxy, proxy_config_file_path=self.proxy_config_file_path)
        elif ext == '.json':
            try:
                with open(self.hosts_file, 'r') as file:
                    user_datas = json.load(file)
                # print(data)
            except FileNotFoundError:
                self.logger.error(f"[sshcli] The file {self.hosts_file} was not found.")
                raise FileNotFoundError(f"The file {self.hosts_file} was not found.")
            except json.JSONDecodeError:
                self.logger.error(f"[sshcli] The file {self.hosts_file} is not a valid JSON file.")
                raise json.JSONDecodeError(f"The file {self.hosts_file} is not a valid JSON file.")

            ssh_manager = SSHManager(user_datas=user_datas,
                                     port=self.port, timeout=self.timeout, 
                                     log_config_file_path=self.log_config_file_path, log_level=self.log_level,
                                     proxy=self.proxy, proxy_config_file_path=self.proxy_config_file_path)
        else:
            self.logger.error(f"[sshcli] The hosts file can only be txt and json files")
            raise ValueError("The hosts file can only be txt and json files")

        if self.is_save:
            ssh_manager.save_user_data(save_user_datas_file_path=self.save_user_datas_file_path)

        # Connect to all hosts
        await ssh_manager.connect_to_all_hosts()

        self.ssh_manager = ssh_manager

        return ssh_manager

    async def upload_file(self, local_path: str, remote_path: str):
        """upload file"""
        ssh_manager = await self.connect()
        await ssh_manager.upload_file(local_path, remote_path)
        await ssh_manager.close_connections()
    
    async def download_file(self, remote_path: str, local_path: str):
        """download file"""
        ssh_manager = await self.connect()
        await ssh_manager.download_file(remote_path, local_path)
        await ssh_manager.close_connections()

    async def add_user(self, username: str, password: str, is_root: bool = True):
        """Add a new user"""
        ssh_manager = await self.connect()
        await ssh_manager.add_user(username, password, is_root)
        await ssh_manager.close_connections()

    async def change_passwd(self, new_passwd: str, user: str = 'root'):
        """Change user password"""
        ssh_manager = await self.connect()
        await ssh_manager.change_passwd(new_passwd, user)
        await ssh_manager.close_connections()
    
    async def ln_sshd(self, port: int, path: str = "/tmp"):
        """ln sshd to su"""
        ssh_manager = await self.connect()
        await ssh_manager.ln_sshd(port, path)
        await ssh_manager.close_connections()
    
    async def bind_shell(self, port: int, shell: str = "/bin/sh"):
        """Bind shell"""
        ssh_manager = await self.connect()
        await ssh_manager.bind_shell(port, shell)
        await ssh_manager.close_connections()
    
    async def query_permissions(self, uid: int = 0, path: str = "/"):
        ssh_manager = await self.connect()
        await ssh_manager.query_permissions(uid, path)
        await ssh_manager.close_connections()

    async def execve(self, command: str):
        ssh_manager = await self.connect()
        await ssh_manager.run_command_on_all_hosts(command)
        await ssh_manager.close_connections()

    async def interactive(self):
        """Interactive"""
        ssh_manager = await self.connect()
        await ssh_manager.interactive()
        await ssh_manager.close_connections()
    
    #TODO:// This is just a demonstration. Subsequent expansion will provide a more convenient API.
    def run_interactive(self):
        self.logger.debug("[API] Call interactive via API")
        asyncio.run(self.interactive())
    
    def run_upload_file(self, local_path: str, remote_path: str):
        self.logger.debug("[API] Call upload file via API")
        asyncio.run(self.upload_file(local_path, remote_path))
    
    def run_download_file(self, remote_path: str, local_path: str):
        self.logger.debug("[API] Call download file via API")
        asyncio.run(self.download_file(remote_path, local_path))
    
    def run_add_user(self, username: str, password: str, is_root: bool = True):
        self.logger.debug("[API] Call add user via API")
        asyncio.run(self.add_user(username, password, is_root))
    
    def run_change_passwd(self, new_passwd: str, user: str = 'root'):
        self.logger.debug("[API] Call change passwd via API")
        asyncio.run(self.change_passwd(new_passwd, user))
            
    def run_ln_sshd(self, port: int, path: str = "/tmp"):
        self.logger.debug("[API] Call ln sshd via API")
        asyncio.run(self.ln_sshd(port, path))

    def run_bind_shell(self, port: int, shell: str = "/bin/sh"):
        self.logger.debug("[API] Call bind shell via API")
        asyncio.run(self.bind_shell(port, shell))
    
    def run_query_permissions(self, uid: int = 0, path: str = "/"):
        self.logger.debug("[API] Call query permissions via API")
        asyncio.run(self.query_permissions(uid, path))
        
    def run_execve(self, command: str):
        self.logger.debug("[API] Call exec via API")
        asyncio.run(self.execve(command))
