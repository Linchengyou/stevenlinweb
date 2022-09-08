#!/usr/bin/env python3
# coding: UTF-8
# import config.logging_config as logging_config
import logging.config
import serial
import pathlib
import json

baudrate_dict = {1200: 0, 2400: 1, 4800: 2, 9600: 3, 19200: 5, 38400: 6}


class MCUinitialize:
    def __init__(self):
        self.data_MCU_read_vision = [1, 65, 0, 141, 0, 5, 109, 237]  # 讀取MCU版本(with crc)
        self.data_MCU_set_on = [1, 66, 240, 47, 0, 3, 6, 0, 26, 0, 36, 25, 14, 126, 67]  # 寫入MCU設定on(with crc)
        self.data_MCU_set_off = [1, 66, 240, 47, 0, 3, 6, 0, 26, 0, 136, 125, 114, 149, 67]  # 寫入MCU設定off(with crc)
        self.data_MCU_read_mode = [1, 66, 240, 47, 0, 3, 6, 0, 26, 4, 0, 0, 0, 181, 44]  # 讀取MCU模式
        self.serial = None
        # logging.config.dictConfig(logging_config.LOGGING_CONFIG)
        self.logger = logging.getLogger('app.' + __name__)
        # self.logger.propagate = False
        self.config_path = str(pathlib.Path(__file__).parents[1]) + '/config/config.json'  # 設定檔的路徑物件

    # 設定MCU之主流程
    def mcu_process(self, arm_version):
        # 取得MCU版本
        mcu_version = self.get_version()

        while True:
            # 傳送mcu訊息可能會失敗，retry
            if mcu_version != arm_version:
                mcu_version = self.get_version()
            else:
                break

        # 檢查MCU版本
        if mcu_version == arm_version:
            # 取得MCU設定檔
            mcu_config_path = pathlib.Path(self.config_path)
            if mcu_config_path.is_file():
                # mcu設定檔的路徑物件
                mcu_config_list = json.loads(mcu_config_path.read_text(encoding='utf-8'), encoding='utf-8')
                baudrate = baudrate_dict[mcu_config_list['mcu']['baud_rate']]
                command = [1, 66, 240, 47, 0, 3, 6, 0, 26, 2, mcu_config_list['mcu']['mode'],
                           baudrate, mcu_config_list['mcu']['z_config']]
                command_with_crc = command + self.get_modbus_crc(command)
                return self.set_mcu(command_with_crc)
            else:
                self.logger.error('Error: Get MCU config file error! Path:{}'.format(mcu_config_path))
                return False
        else:
            self.logger.error('Error: Version error! MCU version:{}, ARM version:{}'.format(mcu_version, arm_version))
            return False

    def get_version(self):
        # 取得MCU版本
        self.open_serial()
        self.send_data(self.data_MCU_read_vision)
        rtn_v = self.read_data()
        self.close_serial()
        print(rtn_v)
        return rtn_v[3:5].decode("utf-8")

    def set_mcu(self, cmd):
        self.open_serial()
        # 寫入MCU設定on
        self.send_data(self.data_MCU_set_on)
        rtn_set_on = self.read_data().hex()
        rtn_set_on_str = [str(int(rtn_set_on[i:i + 2], 16)) for i in range(0, len(rtn_set_on), 2)]

        if rtn_set_on_str and rtn_set_on_str[0] == '2':
            # 寫入MCU模式
            self.send_data(cmd)
            rtn_set_mcu = self.read_data().hex()
            rtn_set_mcu_str = [str(int(rtn_set_mcu[i:i + 2], 16)) for i in range(0, len(rtn_set_mcu), 2)]
            # 寫入MCU設定off
            self.send_data(self.data_MCU_set_off)
            self.read_data()
            self.close_serial()

            if rtn_set_mcu_str and rtn_set_mcu_str[0] == '2':
                return True
            else:
                self.logger.error('Error: Set MCU mode error! Send data:{},Return data:{}'.format(cmd, rtn_set_mcu_str))
                return False
        else:
            if not self.set_mcu(cmd):
                self.logger.error('Error: Set MCU ON error! Return data:{}'.format(rtn_set_on_str))
                return False

    def open_serial(self):
        self.serial = serial.Serial("/dev/ttyS2", 38400, timeout=0.5, write_timeout=0.5)
        if not self.serial.isOpen():
            self.serial.open()

    def close_serial(self):
        self.serial.close()

    def send_data(self, arr):
        self.serial.write(arr)
        self.serial.flush()

    def read_data(self):
        r_data = self.serial.read(80)
        return r_data

    def get_modbus_crc(self, int_array):
        value = 0xFFFF
        for i in range(len(int_array)):
            value ^= int_array[i]
            for j in range(8):
                if (value & 0x01) == 1:
                    value = (value >> 1) ^ 0xA001
                else:
                    value >>= 1
        return [value & 0xff, (value >> 8) & 0xff]


if __name__ == '__main__':
    ini_mcu = MCUinitialize()
    # ini_mcu.mcu_process('CC')
    print(ini_mcu.get_version())
    ini_mcu.open_serial()
    ini_mcu.send_data(ini_mcu.data_MCU_read_mode)
    a = ini_mcu.read_data().hex()
    print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])
