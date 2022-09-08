#!/usr/bin/env python3
# encoding=utf-8

import netifaces
import pathlib
import shlex
import subprocess
import sys

if sys.platform != 'linux':
    print('Not linux')
    exit()

if len(sys.argv) == 1:
    current_program = pathlib.Path(__file__).name
    usage = '''
Usage:
        {0} wifi your_ssid your_psk
        {0} dhcp
        {0} static your_address your_netmask your_gateway your_dns
'''
    print(usage.format(current_program))
    exit()

setting = sys.argv[1]
data = []
interface_gateway_list = netifaces.gateways()
if netifaces.AF_INET not in interface_gateway_list:
    default_interface_name = 'eth0'
else:
    default_network_interface_tuple = netifaces.gateways()[netifaces.AF_INET][0]
    default_interface_name = default_network_interface_tuple[1]

# subprocess.call(shlex.split('/usr/bin/env sudo pkill dhclient'))
# subprocess.call(shlex.split('/usr/bin/env sudo ip route flush table default'))
# subprocess.call(shlex.split('/usr/bin/env sudo ip link set down dev {}'.format(default_interface_name)))
subprocess.call(shlex.split('/usr/bin/env sudo ip addr flush {}'.format(default_interface_name)))
filename = '/etc/network/interfaces'

if setting == 'wifi':  # wifi
    ssid = sys.argv[2]
    psk = sys.argv[3]
    data.append('source-directory /etc/network/interfaces.d')
    data.append('auto lo')
    data.append('iface lo inet loopback')
    data.append('')
    data.append('auto {}'.format(default_interface_name))
    data.append('iface {} inet dhcp'.format(default_interface_name))
    data.append('allow-hotplug wlan0')
    data.append('')
    data.append('auto wlan0')
    data.append('iface wlan0 inet dhcp')
    data.append('wpa-ssid "{0}"'.format(ssid))
    data.append('wpa-psk "{0}"'.format(psk))
    data.append('')
elif setting == 'dhcp':  # dhcp
    data.append('source /etc/network/interfaces.d/*')
    data.append('')
    data.append('auto lo')
    data.append('iface lo inet loopback')
    data.append('')
    data.append('auto {}'.format(default_interface_name))
    data.append('iface {} inet dhcp'.format(default_interface_name))
    data.append('')
elif setting == 'static':  # static
    address = sys.argv[2]
    netmask = sys.argv[3]
    gateway = sys.argv[4]
    dns1 = sys.argv[5] if len(sys.argv) > 5 else ''
    dns2 = sys.argv[6] if len(sys.argv) > 6 else ''
    dns = list(filter(None, ([dns1, dns2])))
    data.append('source /etc/network/interfaces.d/*')
    data.append('')
    data.append('auto lo')
    data.append('iface lo inet loopback')
    data.append('')
    data.append('auto {}'.format(default_interface_name))
    data.append('iface {} inet static'.format(default_interface_name))
    data.append('    address {0}'.format(address))
    data.append('    netmask {0}'.format(netmask))
    data.append('    gateway {0}'.format(gateway))
    if len(dns) > 0:
        data.append('    dns-nameservers {}'.format(' '.join(dns)))
    data.append('')

if len(data) > 0:
    interface_content = '\n'.join(data)
    pathlib.Path(filename).write_text(interface_content, 'utf-8')
    subprocess.call(shlex.split('/usr/bin/env sudo ifdown -a'))
    subprocess.call(shlex.split('/usr/bin/env sudo ifup -a'))
    # subprocess.call(shlex.split('/usr/bin/env sudo systemctl restart NetworkManager'))
    # subprocess.call(shlex.split('/usr/bin/env sudo systemctl restart network-manager'))
    print('done')
else:
    print('Nothing')
