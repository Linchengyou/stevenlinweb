#!/usr/bin/env python3
# coding: UTF-8
import gpio
import lib.mculib as mcu
import lib.clientlib as clientlib
from lib.db_lib_action import create_action_table_tmp, drop_action_table_tmp
import sys
# import config.logging_config as logging_config
import logging.config
import socket
import lib.serverlib as servlib
import threading

# logging.config.dictConfig(logging_config.LOGGING_CONFIG)
# logger = logging.getLogger('app')
# logger.propagate = False

drop_action_table_tmp()
create_action_table_tmp()

# if __name__ == '__main__':
# 取得config
config = servlib.getconfig()
tr_pin = config['gpio']['tr_pin']
red_light = config['gpio']['red_light_pin']
green_light = config['gpio']['green_light_pin']
server_port = config['setting']['port']
mode = config['setting']['oper_mode']
target_ip = config['setting']['target_ip']
target_port = config['setting']['target_port']
max_conn = config['setting']['max_conn']
inactivity_time = config['setting']['inactivity_time']
mcu_mode = config['mcu']['mode']

try:
    tcp_alive_check_time = int(config['setting']['tcp_alive_check_time'])
except:
    tcp_alive_check_time = 7

# 取消gpio log
gpio.setwarnings(False)
gpio.log.setLevel(logging.WARNING)

# 設定gpio pin
gpio.cleanup(tr_pin)
gpio.cleanup(red_light)
gpio.cleanup(green_light)

gpio.setup(tr_pin, gpio.OUT)
gpio.setup(red_light, gpio.OUT)
gpio.setup(green_light, gpio.OUT)

gpio.output(red_light, True)
gpio.output(green_light, True)

# 檢查MCU版本並設定MCU
mcu_set = mcu.MCUinitialize()
rtn = mcu_set.mcu_process('CC')
if rtn:
    # 執行模式
    try:
        if mode == 0:
            HOST = ''
            conn_socket = {}
            lock = threading.Lock()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            if tcp_alive_check_time > 0:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 15)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 15)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 4 * tcp_alive_check_time)  # 上限127
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_USER_TIMEOUT, tcp_alive_check_time * 60 * 1000)

            sock.bind((HOST, server_port))
            sock.listen(4)
            gpio.output(green_light, False)  # 設置ready燈號
            print("Server is starting at:{}".format((sock.getsockname())))
            while True:
                (client, adr) = sock.accept()
                conn_socket[client] = adr
                if len(conn_socket) > max_conn and mcu_mode == 1:
                    conn_socket.pop(client)
                    client.close()
                else:
                    ser_thread = servlib.TServer(client, adr, lock, conn_socket, inactivity_time)
                    ser_thread.setDaemon(True)
                    ser_thread.start()
        else:
            server = clientlib.MyTCPClient(target_ip, target_port)
            # print("Client is starting, target:{}".format((target_ip, target_port)))
            server.client_forever()
    except KeyboardInterrupt:
        gpio.output(green_light, True)  # 關閉ready燈號
        sys.exit(0)
    else:
        gpio.output(green_light, False)  # 設置ready燈號
