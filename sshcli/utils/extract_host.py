import ipaddress
import logging

class Hosts:
    def __init__(self, *, hosts: list[str] = None, hosts_file: str = "", static_port: int = 0, network_segment: str = ""):
        if hosts is None:
            self.hosts = []

        self.hosts_file: str = hosts_file
        self.static_port: int = static_port
        self.network_segment: str = network_segment

        self.ips: list[str] = []
        self.ports: list[int] = []

        self.logger = logging.getLogger()

    def extract(self, *, hosts: list[str] = None, hosts_file: str = "", static_port: int = 0) -> list[str]:
        if hosts != None:
            self.hosts = hosts
            return self.hosts
        
        if hosts_file != "":
            self.hosts_file = hosts_file
        if static_port != 0:
            self.static_port = static_port
        
        temp_hosts_list: list[str] = None
        try:
            with open(self.hosts_file, 'r') as file:
                temp_hosts_list = file.read().strip().split("\n")
        except Exception as ex:
            self.logger.error(f"[extract] {self.hosts_file}: No such file or directory")
            self.logger.error(f"[extract] Exception: {ex}")
            exit(1)

        if temp_hosts_list is not None:
            for host in temp_hosts_list:
                host = host.strip()
                if ":" in host or " " in host:
                    self.hosts.append(host.replace(" ", ":"))
                elif self.static_port != 0:
                    ip = host.split(":")[0]
                    self.hosts.append(f"{ip}:{self.static_port}")
                else:
                    self.logger.error(f"[extract] {host}: Missing port")
        else:
            self.logger.error(f"[extract] {self.hosts_file}: file is empty")
            exit(1)

        return self.hosts
    
    def extract_from_hosts_file(self, hosts_file: str, static_port: int = 0) -> list[str]:
        hosts = self.extract(hosts_file=hosts_file, static_port=static_port)
        self.divide_ip_port_from_hosts()
        return hosts

    def extract_from_network_segment(self, network_segment: str, static_port: int) -> list[str]:
        
        if network_segment is not None and network_segment != "":
            self.network_segment = network_segment

        if "/" not in self.network_segment:
            self.network_segment += "/24"
        
        if static_port is not None and static_port != 0:
            self.static_port = static_port

        network = ipaddress.IPv4Network(self.network_segment, strict=False)
        hosts = list(network.hosts())
        for host in hosts:
            self.hosts.append(f"{str(host)}:{self.static_port}")
        
        return self.hosts

    def generate_hosts_file(self, hosts_file: str = "", write_mode: str = "w", hosts: list[str] = None):
        if hosts is not None:
            self.hosts = hosts
        
        if hosts_file != "":
            self.hosts_file = hosts_file
        
        if self.hosts is not None and len(self.hosts) > 0:
            try:
                with open(self.hosts_file, write_mode) as file:
                    for host in self.hosts:
                        file.write(f"{str(host)}")
                        file.write("\n")
            except Exception as ex:
                self.logger.error(f"[extract] {self.hosts_file}: File cannot be written")
                self.logger.error(f"[extract] Exception: {ex}")
                exit(1)
        else:
            self.logger.error("[extract] Nothing there")
    
    def divide_ip_port_from_hosts(self, hosts: list[str] = None):
        if hosts is not None and hosts != "":
            self.hosts = hosts
        if self.hosts is not None and len(self.hosts) > 0:
            for host in self.hosts:
                if ":" in host:
                    host_list = host.split(":")
                    ip = host_list[0]
                    port = int(host_list[1])
                    self.ips.append(ip)
                    self.ports.append(port)
                else:
                    self.logger.error(f"[extract] {host}: Missing port")
        else:
            self.logger.error("[extract] Nothing there")
