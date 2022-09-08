#!/usr/bin/env python3
# encoding=utf-8

import json
import netifaces
import pathlib
import shlex
import subprocess
import re
import uuid


def get_network_interface_info():
    interface_gateway_list = netifaces.gateways()
    if netifaces.AF_INET not in interface_gateway_list:
        # return None
        default_interface_name = 'eth0'
        is_dhcp = get_network_type()
        if is_dhcp:
            default_interface_gateway = ''
        else:
            default_interface_gateway = get_gateway_ip()
    else:
        default_interface_gateway_tuple = interface_gateway_list[netifaces.AF_INET][0]  # ('172.16.1.254', 'eth0', True)
        default_interface_gateway = default_interface_gateway_tuple[0]
        default_interface_name = default_interface_gateway_tuple[1]

    # {2: [{'netmask': '255.255.255.0', 'broadcast': '172.16.1.255', 'addr': '172.16.1.179'}]}
    netiface_dict = netifaces.ifaddresses(default_interface_name)
    interface_ip = netiface_dict[netifaces.AF_INET][0]['addr']
    interface_netmask = netiface_dict[netifaces.AF_INET][0]['netmask']
    return {
        'name': default_interface_name,
        'ip': interface_ip,
        'netmask': interface_netmask,
        'gateway': default_interface_gateway,
        # 'mac': '.'.join([str((uuid.getnode() >> i) & 0xff) for i in range(0, 8 * 6, 8)][::-1]),
        'mac': ':'.join([('{:0>2x}'.format((uuid.getnode() >> i) & 0xff)).upper() for i in range(0, 8 * 6, 8)][::-1])
    }


def get_dns_server(interface_name):
    resolv_conf_string = pathlib.Path('/etc/resolv.conf').read_text(encoding='utf-8')
    nameserver_list = re.findall(r'^nameserver[\s]+([^#\s]+)$', resolv_conf_string, re.MULTILINE)
    if len(nameserver_list) == 0:
        interface_string = pathlib.Path('/etc/network/interfaces').read_text(encoding='utf-8')
        match_result = re.search(r'^[\s]*dns-nameservers[\s]+([^#\n]+)', interface_string, re.MULTILINE)
        if match_result is not None:
            nameserver_list = [match_result.group(1)]
        else:
            nameserver_list = ['']
    '''
    if len(nameserver_list) == 0:
        interface_command = '/usr/bin/env nmcli dev show {}'.format(interface_name)
        interface_process = subprocess.Popen(shlex.split(interface_command), stdout=subprocess.PIPE)
        dns_cmd_list = shlex.split('/usr/bin/env grep DNS')
        dns_process = subprocess.Popen(dns_cmd_list, stdin=interface_process.stdout, stdout=subprocess.PIPE)
        interface_process.stdout.close()
        awk_command_list = shlex.split("awk '{print $2}'")
        awk_process = subprocess.Popen(awk_command_list, stdin=dns_process.stdout, stdout=subprocess.PIPE)
        dns_process.stdout.close()
        awk_output_string = str(awk_process.communicate()[0], 'utf-8')
        nameserver_list = awk_output_string.strip().split('\n')
    '''
    return nameserver_list


def get_network_type():
    interface_string = pathlib.Path('/etc/network/interfaces').read_text(encoding='utf-8')
    match_result = re.search(r'^iface eth0 inet[\s]+([^#\n]+)$', interface_string, re.MULTILINE)
    is_dhcp = True if match_result is None or match_result.group(1) == 'dhcp' else False
    return is_dhcp


def get_gateway_ip():
    interface_string = pathlib.Path('/etc/network/interfaces').read_text(encoding='utf-8')
    match_result = re.search(r'^[\s]*gateway[\s]+([^#\n]+)', interface_string, re.MULTILINE)
    if match_result is not None:
        return match_result.group(1)
    else:
        return ''


if __name__ == '__main__':
    # interface_dict = get_network_interface_info()
    # if interface_dict is not None and isinstance(interface_dict, dict):
    #    interface_dict['dhcp'] = get_network_type()
    #    interface_dict['dns'] = get_dns_server(interface_dict['name'])
    # interface = json.dumps(interface_dict)
    # print(interface)
    # print(get_gateway_ip())
    interface_dict = get_network_interface_info()
    print(get_dns_server('eth0'))
    dns_server = get_dns_server(interface_dict['name'])[0]
    print(dns_server)
