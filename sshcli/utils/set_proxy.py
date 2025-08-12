import configparser
import asyncio
import asyncssh
import ssl
import os
import logging

from typing import Optional, Tuple, Type


class Configer:
    def __init__(self, config_file='conf/proxy_config.ini'):
        self.config_file = config_file
    
    def update_config_file(self, config_file):
        self.config_file = config_file
    
    def get_config(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)

        self.http_proxy = self.config.get('proxy', 'http_proxy', fallback=None)
        self.https_proxy = self.config.get('proxy', 'https_proxy', fallback=None)
        self.no_proxy = self.config.get('proxy', 'no_proxy', fallback='').split(',')
        self.proxy_timeout = self.config.getint('proxy', 'timeout', fallback=3)


class HTTPConnectorTunnel:
    def __init__(self, proxy_host: str, proxy_port: int,
                 ssl_context: Optional[ssl.SSLContext] = None) -> None:
        self._proxy_host = proxy_host
        self._proxy_port = proxy_port
        self._ssl_context = ssl_context

    async def create_connection(
            self, protocol_factory: Type[asyncio.BaseProtocol],
            remote_host: str, remote_port: int) -> Tuple[asyncio.BaseTransport,
                                                         asyncio.BaseProtocol]:
        reader, writer = await asyncio.open_connection(
            self._proxy_host, self._proxy_port, ssl=self._ssl_context)

        cmd_connect = f'CONNECT {remote_host}:{remote_port} ' \
                      f'HTTP/1.1\r\n\r\n'.encode('ascii')
        writer.write(cmd_connect)

        line = await reader.readline()
        if not line.startswith(b'HTTP/1.1 200 '):
            raise ConnectionError('Unexpected response: '
                                  f'{line.decode("utf-8", errors="ignore")}')

        async for line in reader:
            if line == b'\r\n':
                 break

        transport = writer.transport
        protocol = protocol_factory()
        transport.set_protocol(protocol)
        protocol.connection_made(transport)
        return transport, protocol

class SSHProxy:
    def __init__(self) -> None:
        self.proxy_list: list[str] = []
        self.no_proxy: list[str] = []
        self.tunnel = None

        self.proxy_ip: str = ''
        self.proxy_port: int = 0

        self.logger = logging.getLogger()
    
    def get_proxy_from_config(self, config_file='conf/proxy_config.ini'):

        self.logger.debug(f"[proxy] Getting proxy from configuration file -> {config_file}")

        config = configparser.ConfigParser()
        config.read(config_file)
        
        http_proxy = config.get('proxy', 'http_proxy', fallback='')
        https_proxy = config.get('proxy', 'https_proxy', fallback='')
        no_proxy = config.get('proxy', 'no_proxy', fallback='').split(',')

        if http_proxy != '':
            self.proxy_list.append(http_proxy)
        
        if https_proxy != '':
            self.proxy_list.append(https_proxy)

        if no_proxy != ['']:
            self.no_proxy = no_proxy

    def get_proxy_from_env(self):

        self.logger.debug('[proxy] Getting proxy from environment variable')

        http_proxy = os.getenv('http_proxy', '').strip()
        https_proxy = os.getenv('https_proxy', '').strip()
        no_proxy = os.getenv('no_proxy', '').strip().split(',')
        
        if http_proxy != '':
            self.proxy_list.append(http_proxy)
        
        if https_proxy != '':
            self.proxy_list.append(https_proxy)

        if no_proxy != ['']:
            self.no_proxy = no_proxy

    def get_proxy(self, config_file='conf/proxy_config.ini'):
        self.get_proxy_from_config(config_file)
        self.get_proxy_from_env()

        if len(self.proxy_list) > 0:
            proxy = self.proxy_list[0]
        else:
            self.logger.error("[proxy] No proxy available")
            raise ValueError('No proxy available')
        
        proxy_ip_port = proxy.split('://')[1].replace('://', '')
        proxy_ip, proxy_port = proxy_ip_port.split(':')

        self.proxy_ip = proxy_ip
        self.proxy_port = int(proxy_port)

        tunnel = HTTPConnectorTunnel(proxy_ip, int(proxy_port))

        self.tunnel = tunnel

        return tunnel
    
    def should_bypass_proxy(self, url):
        self.logger.debug(f'[proxy] Check if the address needs to bypass the proxy -> {url}')
        for domain in self.no_proxy:
            if domain.strip() in url:
                return True
        return False

# test
async def run() -> None:
    tunnel = HTTPConnectorTunnel('192.168.75.142', 9999)
    async with asyncssh.connect('172.17.0.2', 22, username='root', password='root123', tunnel=tunnel) as conn:
        result = await conn.run('ls -l')
        print(result.stdout)

if __name__ == '__main__':

    asyncio.run(run())
