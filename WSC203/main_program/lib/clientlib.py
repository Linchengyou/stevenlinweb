#!/usr/bin/env python3
# coding: UTF-8
import serial
import gpio
import pathlib
import json
import socket
import time
from lib.db_lib_action import update_action_tmp


class MyTCPClient:
    def __init__(self, target_ip, target_port):
        self.target_ip = target_ip
        self.target_port = target_port
        self.config = getconfig()
        self.red_light = self.config['gpio']['red_light_pin']
        if self.config['mcu']['mode'] == 1:
            self.serial_mode = "MBUS"
        else:
            self.serial_mode = "DBUS"
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conncet_socket()

    def client_forever(self):
        ser_m = MySerial(self.serial_mode)
        # ser_m.open_serial()
        while True:
            try:
                ser_m.open_serial()
                r_data = ser_m.read_data()
            except:
                r_data = None

            if r_data:
                # self.conncet_socket()
                # print('input data:{}'.format(r_data))
                try:
                    self.s.send(bytes(r_data))
                    try:
                        r_data_d = self.s.recv(1024)
                        # print('output data:{}'.format(list(r_data_d)))
                        ser_m.send_data(r_data_d)

                    except Exception as e:
                        # print("read error:{}".format(e))
                        self.s.close()
                        ser_m.reset_input_buffer()
                        self.conncet_socket()

                except Exception as e:
                    # print("{}".format(e))
                    self.s.close()
                    ser_m.reset_input_buffer()
                    self.conncet_socket()
            else:
                pass
                # self.s.close()

    def conncet_socket(self):
        while True:
            try:
                update_action_tmp({'conn_status': 1})
                # self.s = socket.create_connection((self.target_ip, self.target_port),
                #                                   timeout=self.config['setting']['target_timeout'])
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.settimeout(self.config['setting']['target_timeout'])
                self.s.connect((self.target_ip, self.target_port))

                if self.s:
                    # print("successfully connect to {} ,{}".format(self.target_ip, self.target_port))
                    update_action_tmp({'conn_status': 2})
                    break
            except Exception as e:
                # print("{}".format(e))
                # print("retry...")
                update_action_tmp({'conn_status': 3})
                gpio.output(self.red_light, False)  # 設置ready燈號
                time.sleep(5)
                gpio.output(self.red_light, True)  # 設置ready燈號


class MySerial:
    def __init__(self, port_typ):
        self.ser = None
        self.config = getconfig()
        self.port_typ = port_typ

    def reset_input_buffer(self):
        self.ser.reset_input_buffer()

    def open_serial(self):
        if self.port_typ == "DBUS":
            self.ser = serial.Serial(**self.config['uart']['uart2'])
        else:
            self.ser = serial.Serial(**self.config['uart']['uart1'])

        if not self.ser.isOpen():
            self.ser.open()

    def send_data(self, msg):
        if self.port_typ == "DBUS":
            self.ser.write(msg)
            self.ser.flush()
        else:
            gpio.set(self.config['gpio']['tr_pin'], True)  # 開啟tr_pin
            self.ser.write(msg)
            self.ser.flush()
            gpio.set(self.config['gpio']['tr_pin'], False)  # 開啟tr_pin

    def read_data(self):
        # r_data = self.ser.read(1024)
        r_data = b''
        while True:
            r = self.ser.read()
            if len(r) == 0:
                break
            else:
                self.ser.timeout = 0.015
            r_data += r
        # hex_data = r_data.hex()
        # data_list = [int(hex_data[i:i + 2], 16) for i in range(0, len(hex_data), 2)]
        data_list = list(r_data)
        return data_list


def getconfig():
    project_path = str(pathlib.Path(__file__).parents[1])  # 當前專案目錄
    config_file_path = pathlib.Path(project_path + '/config/config.json')  # 基礎設定檔的路徑物件
    config = None  # 基礎設定檔 dict

    if config_file_path.is_file():
        config = json.loads(config_file_path.read_text(encoding='utf-8'), encoding='utf-8')

    return config
