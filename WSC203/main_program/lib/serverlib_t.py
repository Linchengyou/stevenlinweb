#!/usr/bin/env python3
# coding: UTF-8
import socketserver
import sys
import threading
from time import ctime
import serial
import gpio
from datetime import datetime
import lib.mculib as mcu
import pathlib
import json
import logging.config
from ctypes import *

logger = logging.getLogger('app.' + __name__)
lock = threading.Lock()


class MyTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 2

    def __init__(self, server_address, requesthandler):
        socketserver.TCPServer.__init__(self, server_address, requesthandler)
        self._num_client = 0

    def process_request(self, *args, **kws):
        # print("swap thread")
        self._num_client += 1
        socketserver.ThreadingMixIn.process_request(self, *args, **kws)

    def process_request_thread(self, *args, **kws):
        socketserver.ThreadingMixIn.process_request_thread(self, *args, **kws)
        # print("kill thread")
        self._num_client -= 1

    def get_client_number(self):
        return self._num_client


class MyTCPHandler(socketserver.StreamRequestHandler):
    start_time = None

    def handle(self):
        self.request.settimeout(None)
        myserial = MySerial("DBUS")
        # config = getconfig()
        # cur = threading.current_thread()
        # print('[{}] Client connected from {} and [{}] is handling with him.'
        #       .format(ctime(), self.request.getpeername(), cur.name))
        # print('get_client_number:{}'.format(self.server.get_client_number()))
        if self.server.get_client_number() > 8:
            self.request.close()
            return

        while True:
            self.start_time = datetime.now()
            # 接收ethernet資料
            msg = self.request.recv(1024)
            # gpio.output(config['gpio']['red_light_pin'], True)  # 設置燈號

            if not msg:
                # gpio.output(config['gpio']['red_light_pin'], True)  # 設置燈號
                return
            else:
                # serial port處理
                with lock:
                    myserial.open_serial()
                    data_list = [int(msg.hex()[i:i + 2], 16) for i in range(0, len(msg.hex()), 2)]
                    # logger.debug("data input: {} ".format(data_list))
                    # print("data input: {} ".format(data_list))
                    myserial.send_data(data_list)
                    try:
                        rt = myserial.read_data()
                    except Exception as e:
                        rt = bytes()
                        # logger.error("read error:{}".format(e))
                        # gpio.output(config['gpio']['red_light_pin'], False)  # 設置燈號

                # logger.debug("data output: {} ".format(rt))
                # print("data output: {} ".format(rt))
                try:
                    # logger.debug("from {}:{},socket:{}".format(*self.client_address, self.request))
                    self.wfile.write(bytes(rt))

                except Exception as e:
                    # logger.error("socket wfile to {}:{} error: {} ".format(*self.client_address, e))
                    # gpio.output(config['gpio']['red_light_pin'], True)  # 設置燈號
                    return
            # self.request.close()


class MySerial:
    def __init__(self, port_typ):
        self.ser = None
        self.config = getconfig()
        self.port_typ = port_typ
        self.msg_header = None
        self.msg_data = None
        self.msg_length = 0

    def open_serial(self):
        if self.port_typ == "DBUS":
            self.ser = serial.Serial(**self.config['uart']['uart2'])
            # self.ser.timeout = None
        else:
            self.ser = serial.Serial(**self.config['uart']['uart1'])

        if not self.ser.isOpen():
            self.ser.open()

    def send_data(self, msg):
        # modbus_type: 0: MODBUS　1: MODBUS-TCP
        if self.config['setting']['modbus_type'] == 1:
            self.msg_header = msg[:6]
            self.msg_data = msg[6:]
            data_crc = self.get_modbus_crc(self.msg_data)
            msg = self.msg_data + data_crc

        if self.port_typ == "DBUS":
            self.ser.write(msg)
            self.ser.flush()
        else:
            # wiringpi = cdll.LoadLibrary('libwiringPi.so')
            # wiringpi.wiringPiSetup()
            # wiringpi.pinMode(1, 1)
            # wiringpi.digitalWrite(1, 1)
            gpio.set(self.config['gpio']['tr_pin'], True)  # 開啟tr_pin
            self.ser.write(msg)
            self.ser.flush()
            # wiringpi.digitalWrite(1, 0)
            gpio.set(self.config['gpio']['tr_pin'], False)  # 開啟tr_pin

    def read_data(self):
        # r_data = self.ser.read(256)
        r_data = b''
        while True:
            r = self.ser.read()
            if len(r) == 0:
                break
            else:
                self.ser.timeout = 0.01
            r_data += r

        hex_data = r_data.hex()
        data_list = [int(hex_data[i:i + 2], 16) for i in range(0, len(hex_data), 2)]

        # modbus_type: 0: MODBUS　1: MODBUS-TCP
        if self.config['setting']['modbus_type'] == 1:
            modbus_tcp_data = self.msg_header + data_list[:-2]
            # modbus-tcp 資料長度
            modbus_tcp_data[5] = len(data_list[:-2])
            data_list = modbus_tcp_data

        return data_list

    @staticmethod
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


def getconfig():
    project_path = str(pathlib.Path(__file__).parents[1])  # 當前專案目錄
    config_file_path = pathlib.Path(project_path + '/config/config.json')  # 基礎設定檔的路徑物件
    config = None  # 基礎設定檔 dict

    if config_file_path.is_file():
        config = json.loads(config_file_path.read_text(encoding='utf-8'), encoding='utf-8')

    return config


if __name__ == '__main__':
    # 取消gpio log
    gpio.setwarnings(False)
    gpio.log.setLevel(logging.WARNING)

    # 設定gpio pin 6
    gpio.cleanup(6)
    gpio.setup(6, gpio.OUT)

    # 檢查MCU版本並設定MCU
    mcu_set = mcu.MCUinitialize()
    rtn = mcu_set.mcu_process('CC')

    HOST = ''
    PORT = 4001

    server = MyTCPServer((HOST, PORT), MyTCPHandler)
    ip, port = server.server_address
    print("Server is starting at:", (ip, port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
