import os
import subprocess
import logging

from .key_input import KeyInput

class PTerminal():
    def __init__(self, exec_command_func, **kwargs):
        self._username: str = ""
        self._hostname: str = ""
        self._path: str = ""

        self.terminal: str = ""

        self.exec_command_func = exec_command_func

        if 'check' in kwargs:
            self.check = kwargs['check']
        else:
            self.check = False
        if 'timeout' in kwargs:
            self.timeout = kwargs['timeout']
        else:
            self.timeout = 3
        
        self.logger = logging.getLogger()
        
        self.key_input = KeyInput()
    
    @property
    def username(self):
        return self._username
    
    @username.setter
    def username(self, value: str):
        self._username = value
        self._update_template()
    
    @property
    def hostname(self):
        return self._hostname
    
    @hostname.setter
    def hostname(self, value: str):
        self._hostname = value
        self._update_template()
    
    @property
    def path(self):
        return self._path
    
    @path.setter
    def path(self, value: str):
        self._path = value

        if self._path != '/':
            self._path = self._path.rstrip('/')
        
        if self.username == 'root':
            self._path = self._path.replace("~", f"/{self.username}")
        else:
            self._path = self._path.replace("~", f"/home/{self.username}")

        self._update_template()
    

    def _update_template(self):
        # 这个方法用来在属性改变时更新 template

        if self._username == 'root':
            print_path = self._path.replace(f'/{self._username}', '~')
        else:
            print_path = self._path.replace(f'/home/{self._username}', '~')

        '''
        self.terminal = f"\033[32m┌──(\033[0m\033[34m{self._username}\033[0m\033[33m㉿\033[0m\033[31m{self._hostname}\033[0m\033[32m)-[\033[0m{print_path}\033[32m]\033[0m\n"  + \
                         "\033[32m└─\033[0m\033[34m$ \033[0m"
        '''
        self.terminal = f"\x1b[32m┌──(\x1b[0m\x1b[34m{self._username}\x1b[0m\x1b[33m㉿\x1b[0m\x1b[31m{self._hostname}\x1b[0m\x1b[32m)-[\x1b[0m{print_path}\x1b[32m]\x1b[0m\n"  + \
                         "\x1b[32m└─\x1b[0m\x1b[34m$ \x1b[0m"

    async def run(self):

        self.logger.info("[terminal] Pseudo terminal starts...")

        # 更新属性
        result = await self.exec_command_func('whoami', check=self.check, timeout=self.timeout)
        self.username = result.stdout.strip()
        result = await self.exec_command_func('hostname', check=self.check, timeout=self.timeout)
        self.hostname = result.stdout.strip()
        result = await self.exec_command_func('pwd', check=self.check, timeout=self.timeout)
        self.path = result.stdout.strip()

        # 打印当前模板
        while True:
            cmd = await self.key_input.input(self.terminal)
            cmd = cmd.strip()

            # step1
            if cmd == 'exit':
                break
            elif cmd == 'clear' or cmd == 'cls':
                if os.name == 'posix':
                    os.system('clear')
                    continue
                elif os.name == 'nt':
                    os.system('cls')
                    continue
                
            # step2
            old_path = self.path
            if len(cmd) >= 2 and cmd[:2] == "cd":
                input_path = cmd.replace('cd', '').strip()

                if input_path == "":
                    new_path = self.path
                elif input_path == "." or input_path == "./":
                    new_path = self.path
                elif ".." in input_path:
                    if "../" in input_path:
                        temp_count = input_path.count("../")
                        temp_path = input_path.split('../')[-1]
                    else:
                        temp_count = 1
                        temp_path = ""
                    for _ in range(temp_count):
                        self.path = os.path.dirname(self.path)
                    new_path = os.path.join(self.path, temp_path)
                elif input_path.startswith('/'):
                    new_path = input_path
                elif input_path.startswith('~'):
                    new_path = input_path

                else:
                    if input_path.startswith('./'):
                        input_path = input_path.lstrip('./')
                    new_path = os.path.join(self.path, input_path)
                

                if self.username == 'root':
                    new_path = new_path.replace("~", f"/{self.username}")
                else:
                    new_path = new_path.replace("~", f"/home/{self.username}")

                
                cmd = f"cd {new_path}"
                self.path = new_path
            else:
                cmd = f"cd {self.path} && {cmd}"
            
            # step3
            try:
                result = await self.exec_command_func(cmd, check=self.check, timeout=self.timeout)
                if result.stdout:
                    out = result.stdout.rstrip('\n')
                    print(f"[+] START Stdout:\n{out}\n[+] END\n")
                if result.stderr:
                    err = result.stderr.rstrip('\n')
                    self.logger.error(f"\n[-] START Stderr:\n{err}\n[-] END\n")
                if result.returncode != 0:
                    self.path = old_path
            except Exception as ex:
                self.logger.error(f"[terminal] {cmd} Not Found or Exception, {ex = }")

# test
def run_shell_command(command):
    # 执行命令并获取输出
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    
    # 获取命令的标准输出
    output = result.stdout
    
    # 获取命令的标准错误
    error = result.stderr
    
    # 获取命令的返回码
    returncode = result.returncode
    
    return result

if __name__ == '__main__':
    p_terminal = PTerminal(run_shell_command)
    p_terminal.run()
