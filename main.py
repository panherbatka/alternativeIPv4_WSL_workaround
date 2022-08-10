import configparser
import ctypes
import os
import sys

from subprocess import Popen, PIPE
from pathlib import Path


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def get_script_dir():
    return Path(__file__).parent.absolute()


def config_file_exist():
    if not os.path.exists(f'{get_script_dir()}/config.ini'):
        print("No config file found. Creating new config.ini")
        create_config()
        return False
    else:
        return True


def create_config():
    """Creates config.ini file"""
    print("Please enter the IP address of the WSL VML:")
    ip = input()
    print("Please enter the distro name of the WSL VML:")
    distro = input()

    config = configparser.ConfigParser()
    config.add_section('Config')
    config.set('Config', 'ip', ip)
    config.set('Config', 'distro', distro)

    with open('config.ini', 'w') as configfile:
        config.write(configfile)


def get_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config


def get_config_value(config, section, key):
    return config.get(section, key)


def check_if_wsl_is_running():
    distro = get_config_value(get_config(
        f'{get_script_dir()}/config.ini'), 'Config', 'distro')

    ps_command = "wsl --list --running"

    with Popen(f'powershell.exe -ExecutionPolicy RemoteSigned -command "{ps_command}"',
               stdout=PIPE, stderr=PIPE) as p:
        output, errors = p.communicate()
    lines = output.decode('utf-16').splitlines()

    if any(distro in s for s in lines):
        return True
    else:
        return False


def start_wsl():
    ip = get_config_value(get_config(
        f'{get_script_dir()}/config.ini'), 'Config', 'ip')

    ps_command = f"""
    Remove-NetIPAddress -InterfaceAlias Ethernet -IPAddress {ip} -PrefixLength 24
    wsl ~ echo "Booting VM"
    New-NetIPAddress -InterfaceAlias Ethernet -IPAddress {ip} -PrefixLength 24
    """

    def run_command(command):
        '''Runs a command in powershell'''
        p = Popen(
            f'powershell.exe -ExecutionPolicy RemoteSigned -command "{command}"', stdout=sys.stdout)
        p.communicate()
    run_command(ps_command)


def kill_wsl():
    ps_command = "wsl --shutdown"

    p = Popen(
        f'powershell.exe -ExecutionPolicy RemoteSigned -command "{ps_command}"', stdout=sys.stdout)
    p.communicate()
    start_wsl()


def main():

    if is_admin():
        print("Workaround for WSL internet connection issue if custom NetIPAddress is used")

        config_file_exist()

        if check_if_wsl_is_running():
            kill_wsl()
        else:
            start_wsl()

    else:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1)


if __name__ == "__main__":
    main()
