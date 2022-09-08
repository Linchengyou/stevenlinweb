# coding: utf-8
import os
import pathlib
import shlex
import subprocess


def get_modbus_crc(int_array):
    value = 0xFFFF
    for i in range(len(int_array)):
        value ^= int_array[i]
        for j in range(8):
            if (value & 0x01) == 1:
                value = (value >> 1) ^ 0xA001
            else:
                value >>= 1
    return [value & 0xff, (value >> 8) & 0xff]


def gateway_reboot():
    print('System is going to reboot because some reason')
    os.system('/usr/bin/env sudo reboot')


def network_restart():
    print('Network is going to restart')
    os.system('/usr/bin/env sudo ifdown eth0')
    os.system('/usr/bin/env sudo ifup eth0')


def get_ssh_key(user):
    ssh_dir_path = pathlib.Path('/home/{}/.ssh'.format(user))
    if not ssh_dir_path.is_dir():
        ssh_dir_path.mkdir(mode=0o700)

    ssh_key_file_path = ssh_dir_path.joinpath('id_rsa.pub')
    if not ssh_key_file_path.is_file():
        cp = subprocess.run(shlex.split('ssh-keygen -t rsa -N "" -f {}/id_rsa -q'.format(ssh_dir_path.as_posix())))
        if cp.returncode != 0:
            raise OSError
    return ssh_key_file_path.read_text(encoding='utf-8')


def ssh_open(mqtt_dict):
    sub_command_string = \
        '/usr/bin/env ssh -o StrictHostKeyChecking=no -nNT -R {port}:localhost:{open_port} {user}@{host} &'
    sub_command = shlex.quote(sub_command_string.format(**mqtt_dict))
    command = '/usr/bin/env su - dae -c {}'.format(sub_command)
    cp = subprocess.run(command, shell=True)
    return cp.returncode


def ssh_close():
    sub_command = shlex.quote('/usr/bin/env sudo pkill -x ssh')
    command = '/usr/bin/env su - dae -c {}'.format(sub_command)
    cp = subprocess.run(command, shell=True)
    return cp.returncode


def update_ssh_key(content):
    ssh_dir_path = pathlib.Path('/home/{}/.ssh'.format('dae'))
    if not ssh_dir_path.is_dir():
        ssh_dir_path.mkdir(mode=0o700)
    ssh_key_file_path = ssh_dir_path.joinpath('id_rsa')
    ssh_key_file_path.write_text(content, encoding='utf-8')

