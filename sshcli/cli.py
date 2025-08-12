import click
import asyncio

from .ssh.ssh_manager import *
from .ssh.ssh_cli import SSHCli

sshcli_version_message = f"""
SSH-%(prog)s version %(version)s
Author: {sshcli_author}
Email: {sshcli_author_email}
Github: {sshcli_git_url}
""".strip()

# Main command group
@click.group()
@click.option('-hf', '--hosts-file', default='hosts.txt', help='Path to the hosts file [Example: txt or json file] (default: hosts.txt)')
@click.option('-ns', '--network-segment', default='', help='CIDR block [Example: 192.168.1.1/24] (default: "")')
@click.option('-name', '--username', default='root', help='SSH username (default: root)')
@click.option('-pwd', '--password', default='', help='SSH password (default: "")')
@click.option('-pkf', '--private-key-file', default='', help='SSH private key file path (default: "")')
@click.option('-p', '--port', default=22, help='The port of the SSH service (default: 22)')
@click.option('-t', '--timeout', default=3, help='Timeout when executing command (default: 3)')
@click.option('-lcf', '--log-config-file', default='', help='Log configuration file path (default: In the conf of the program installation directory)')
@click.option('-level', '--log-level', default='', help='Log level (default: In Log Config File)')
@click.option('--save/--no-save', default=False, help='Save user data (default: False)')
@click.option('-save-udf', '--save-user-datas-file', default='hosts.json', help='Save user data file path (default: "hosts.json")')
@click.option('--proxy/--no-proxy', default=False, help='Set up a proxy (default: False)')
@click.option('-pcf', '--proxy-config-file', default='', help='Network proxy configuration file path (default: In the conf of the program installation directory)')
@click.version_option(f"{sshcli_version}", "-V", "--version", message=f"{sshcli_version_message}")
@click.pass_context
def cli(ctx, hosts_file, network_segment, username, password, private_key_file, port, timeout, log_config_file, log_level, save, save_user_datas_file, proxy, proxy_config_file):
    """
    SSH CLI - Asynchronous batch attack based on ssh connection

    (If you need proxies, combine them with other tools such as proxychains4)
    """
    # Store main command parameters into context for child commands
    ctx.ensure_object(dict)

    ssh_cli = SSHCli(hosts_file=hosts_file, network_segment=network_segment,
                    username=username, password=password,
                    private_key_path=private_key_file,
                    port=port, timeout=timeout, 
                    log_config_file_path=log_config_file, log_level=log_level,
                    is_save=save, save_user_datas_file_path=save_user_datas_file,
                    proxy=proxy, proxy_config_file_path=proxy_config_file)

    ctx.obj['ssh_cli'] = ssh_cli

@click.command()
@click.option('-lpath', '--local-path', required=True, help='File path to be uploaded')
@click.option('-rpath', '--remote-path', required=True, help='The path to upload to')
@click.pass_context
def uploadfile(ctx, local_path, remote_path):
    """Upload file"""
    # Get the parameters from the main command context
    ssh_cli = ctx.obj['ssh_cli']

    # asyncio.run(ssh_cli.upload_file(local_path, remote_path))
    ssh_cli.run_upload_file(local_path, remote_path)

@click.command()
@click.option('-rpath', '--remote-path', required=True, help='The path to which the file needs to be downloaded')
@click.option('-lpath', '--local-path', required=True, help='The path to which you need to download')
@click.pass_context
def downloadfile(ctx, remote_path, local_path):
    """Download file"""
    # Get the parameters from the main command context
    ssh_cli = ctx.obj['ssh_cli']
    # asyncio.run(ssh_cli.download_file(remote_path, local_path))
    ssh_cli.run_download_file(remote_path, local_path)

@click.command()
@click.option('-nname', '--new-username', required=True, help='New username to be created')
@click.option('-npwd', '--new-password', required=True, help='New password to be created')
@click.option('--root/--no-root', default=True, help='Whether the new user should have root privileges (default: True)')
@click.pass_context
def adduser(ctx, new_username, new_password, root):
    """Add a user"""
    # Get the parameters from the main command context
    ssh_cli = ctx.obj['ssh_cli']
    # asyncio.run(ssh_cli.add_user(new_username, new_password, root))
    ssh_cli.run_add_user(new_username, new_password, root)

@click.command()
@click.option('-npwd', '--new-password', required=True, help='New password for the user')
@click.option('--user', default="root", help='Username whose password needs to be changed (default: root)')
@click.pass_context
def changepassword(ctx, new_password, user):
    """Change user's password"""
    # Get the parameters from the main command context
    ssh_cli = ctx.obj['ssh_cli']
    # asyncio.run(ssh_cli.change_passwd(new_password, user))
    ssh_cli.run_change_passwd(new_password, user)

@click.command()
@click.option('-np', '--new-port', required=True, help='Open the port for new sshd connection')
@click.option('--path', default="/tmp", help='Link sshd to the path of su (default: /tmp)')
@click.pass_context
def lnsshd(ctx, new_port, path):
    """Softly connect sshd to su and login with any password."""
    # Get the parameters from the main command context
    ssh_cli = ctx.obj['ssh_cli']
    # asyncio.run(ssh_cli.ln_sshd(new_port, path))
    ssh_cli.run_ln_sshd(new_port, path)

@click.command()
@click.option('-np', '--new-port', required=True, help='Open the port for forward connection')
@click.option('--shell', default="/bin/sh", help='Enable forward connection binding shell (default: /bin/sh)')
@click.pass_context
def bindshell(ctx, new_port, shell):
    """Bind the shell to a port and open a forward connection"""
    # Get the parameters from the main command context
    ssh_cli = ctx.obj['ssh_cli']
    # asyncio.run(ssh_cli.bind_shell(new_port, shell))
    ssh_cli.run_bind_shell(new_port, shell)

@click.command()
@click.option('--uid', default=0, help='The user permission uid to be queried (default: 0)')
@click.option('--path', default="/usr/bin", help='find query path (default: /usr/bin)')
@click.pass_context
def queryperm(ctx, uid, path):
    """Query permissions,Including querying users with specified uid, querying account information that can be logged in remotely, and querying files with suid"""
    # Get the parameters from the main command context
    ssh_cli = ctx.obj['ssh_cli']
    # asyncio.run(ssh_cli.query_permissions(uid, path))
    ssh_cli.run_query_permissions(uid, path)

@click.command()
@click.option('-cmd', '--command', required=True, help='Commands to be executed')
@click.pass_context
def execve(ctx, command):
    """Execute the command"""
    # Get the parameters from the main command context
    ssh_cli = ctx.obj['ssh_cli']
    # asyncio.run(ssh_cli.exec(command))
    ssh_cli.run_execve(command)

@click.command()
@click.pass_context
def interactive(ctx):
    """Enter interactive mode"""
    # Get the parameters from the main command context
    ssh_cli = ctx.obj['ssh_cli']
    # asyncio.run(ssh_cli.interactive())
    ssh_cli.run_interactive()

# Add child commands to the main command group
cli.add_command(uploadfile)
cli.add_command(downloadfile)
cli.add_command(adduser)
cli.add_command(changepassword)
cli.add_command(lnsshd)
cli.add_command(bindshell)
cli.add_command(queryperm)
cli.add_command(execve)
cli.add_command(interactive)
