#!/usr/bin/env python3
# encoding=utf-8

import gpio
import logging
import threading
import serial
import time
import sys
import pathlib
import json
import datetime
import pytz
sys.path.append(str(pathlib.Path(__file__).parents[1]))
from config import product_info, web_QC_path, APP_NAME, VERSION       


class GatewayTest:
    def __init__(self):
        # gpio pin腳位
        self.btn_pin = 64
        self.tr_pin = 6
        self.green_light_pin = 2
        self.red_light_pin = 203
        self.serial_d = None
        self.serial_m = None
        # self.config_file = pathlib.Path(app_config_path)  # config檔路徑物件
        self.file_version = web_QC_path + 'response_version.txt'     # 版本記錄檔
        self.file_path = web_QC_path + 'response.txt'                # 回傳紀錄檔路徑
        self.data_MCU_set_on = [1, 66, 240, 47, 0, 3, 6, 0, 26, 0, 36, 25, 14, 126, 67]    # 寫入設定on
        self.data_MCU_write_mode = [1, 66, 240, 47, 0, 3, 6, 0, 26, 2, 1, 3, 0, 228, 148]  # 寫入MCU模式
        self.data_MCU_read_vision = [1, 65, 0, 141, 0, 5, 109, 237]                        # 讀取MCU版本
        self.data_light_on = [1, 5, 1, 0, 255, 0, 141, 198]
        self.data_light_off = [1, 5, 1, 0, 0, 0, 204, 54]
        self.button_timer = None
        self.serial_d_initialized = False
        self.task_done = 0

        # 清空檔案
        with open(self.file_path, 'w+') as file1:
            file1.truncate()
        with open(self.file_version, 'w+') as file2:
            file2.truncate()

        # 取消gpio log
        gpio.setwarnings(False)
        gpio.log.setLevel(logging.WARNING)

        gpio.cleanup(self.btn_pin)
        gpio.cleanup(self.tr_pin)
        gpio.cleanup(self.green_light_pin)
        gpio.cleanup(self.red_light_pin)

        # 取得ARM版本
        # if self.config_file.is_file():
        #     self.config = json.loads(self.config_file.read_text(encoding='utf-8'), encoding='utf-8')
        data_dict = dict()
        data_dict['ARM'] = str(APP_NAME) + ' ' + str(VERSION)
        if 'build' in product_info['model']:
            data_dict['ARM'] += ' (Build: {})'.format(product_info['model']['build'])

        # 開啟dbus port，此port需對晶片進行設定
        self.open_serial_d()

        # 取得MCU版本
        if not self.serial_d_initialized:  # 新版硬體似乎會在開機後第一次存取失敗, 故預先執行一次
            self.send_data(self.data_MCU_read_vision)
            self.read_data()
            self.serial_d_initialized = True
        self.send_data(self.data_MCU_read_vision)
        rtn_v = self.read_data()
        print('rtn_v = {}'.format(rtn_v))
        data_dict['MCU'] = rtn_v[3:13].decode('utf-8')
        json_data = json.dumps(data_dict)
        # print(json_data)
        with open(self.file_version, 'a+') as fi:
            fi.write(json_data)

        # 寫入MCU設定on
        self.send_data(self.data_MCU_set_on)
        rtn = self.read_data()
        print('rtn = {}'.format(rtn))

        # 寫入MCU模式
        if rtn and rtn[0] == 2:
            self.send_data(self.data_MCU_write_mode)
            rtn2 = self.read_data()
            if rtn2 and rtn2[0] == 2:
                # 開啟mbus port
                self.open_serial_m()

                # 設定腳位型態
                gpio.setup(self.btn_pin, gpio.IN)
                gpio.setup(self.tr_pin, gpio.OUT)
                gpio.setup(self.green_light_pin, gpio.OUT)
                gpio.setup(self.red_light_pin, gpio.OUT)
                print('mcu ok!')
                with open(self.file_path, 'a+') as fi:
                    fi.write('MCU設定完畢，請開始測試!\n<br /><br />')
            else:
                with open(self.file_path, 'a+') as fi:
                    fi.write('MCU設定寫入有誤!\n<br />')
                sys.exit()
        else:
            with open(self.file_path, 'a+') as fi:
                fi.write('MCU設定開啟有誤!\n<br />')
            sys.exit()

    def open_serial_m(self):
        self.serial_m = serial.Serial('/dev/ttyS1', 9600, timeout=0.3, write_timeout=0.3)
        self.serial_m.inter_byte_timeout = 0.05
        if not self.serial_m.is_open:
            self.serial_m.open()

    def open_serial_d(self):
        self.serial_d = serial.Serial('/dev/ttyS2', 38400, timeout=1, write_timeout=1)
        if not self.serial_d.is_open:
            self.serial_d.open()

    def send_data(self, arr):
        print('write dbus: {}'.format(arr))
        self.serial_d.write(arr)
        self.serial_d.flush()

    def read_data(self):
        r_data = self.serial_d.read(70)
        data_list = list(r_data)
        print('read dbus: {}'.format(data_list))
        return r_data

    def scan(self):
        while True:
            # 按鈕按下
            if (gpio.input(self.btn_pin) == 0) and self.task_done == 0:
                gpio.set(self.green_light_pin, True)
                gpio.set(self.red_light_pin, True)
                self.task_done = 1
                # RS485-1 => RS485-2
                self.mbus_send()
                time.sleep(0.1)
                self.dbus_read()

                time.sleep(0.1)

                # RS485-1 <= RS485-2
                self.dbus_send()
                # time.sleep(0.1)
                self.mbus_read()
                self.task_done = 0
            else:
                gpio.set(self.green_light_pin, False)
                gpio.set(self.red_light_pin, False)

    def mbus_send(self):
        print('mbus_send')
        gpio.set(self.tr_pin, True)                 # 開啟tr_pin
        self.serial_m.write(self.data_light_off)    # 寫入資料
        self.serial_m.flush()                       # 送出
        gpio.set(self.tr_pin, False)                # 關閉tr_pin
        time.sleep(0.005)                           # baud 9600 sleep 5ms
        self.serial_m.reset_input_buffer()

    def dbus_send(self):
        print('dbus_send')
        self.serial_d.write(self.data_light_on)
        self.serial_d.flush()
        self.serial_d.reset_input_buffer()

    def mbus_read(self):
        # 讀取回傳值
        print('mbus_read')
        read_data = self.serial_m.read(70)
        data_list = list(read_data)
        print(data_list)
        if data_list == self.data_light_on:
            with open(self.file_path, 'a+') as fi:
                fi.write(datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y/%m/%d %H:%M:%S') +
                         ' [ RS485-2 => RS485-1 OK! ]\n<br />')
        else:
            with open(self.file_path, 'a+') as fi:
                fi.write(datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y/%m/%d %H:%M:%S') +
                         ' [ RS485-2 => RS485-1 無法傳送資料! ]\n<br />')

    def dbus_read(self):
        # 讀取回傳值
        print('dbus_read')
        read_data = self.serial_d.read(70)
        data_list = list(read_data)
        print(data_list)
        if data_list == self.data_light_off:
            with open(self.file_path, 'a+') as fi:
                fi.write(datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y/%m/%d %H:%M:%S') +
                         ' [ RS485-1 => RS485-2 OK! ]\n<br />')
        else:
            with open(self.file_path, 'a+') as fi:
                fi.write(datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y/%m/%d %H:%M:%S') +
                         ' [ RS485-1 => RS485-2 無法傳送資料! ]\n<br />')


if __name__ == '__main__':
    gtest = GatewayTest()
    gtest.button_timer = threading.Timer(0.1, gtest.scan)
    gtest.button_timer.start()
