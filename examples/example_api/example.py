#!/usr/bin/python3
# -*- coding: utf-8 -*-

from sshcli import SSHCli

if __name__ == '__main__':
    ssh_cli = SSHCli(hosts_file="./hosts.json", log_level='debug')
    ssh_cli.api.interactive()
