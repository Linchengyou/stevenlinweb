import serial
import gpio


# def print(r_data):
#     pass


class Communicate:
    def __init__(self):
        self.serial = serial.Serial(port="/dev/ttyS1", baudrate=9600, timeout=0.3, write_timeout=0.5)
        # gpio.cleanup(6)
        # gpio.setup(6, gpio.OUT)

    def trans_serial(self, cmd):
        if not self.serial.isOpen():
            self.serial.open()

        cmd_crc = self.get_modbus_crc(cmd)
        gpio.set(6, 1)
        self.serial.write(cmd + cmd_crc)
        self.serial.flush()
        gpio.set(6, 0)
        r_data = self.serial.read(256)
        print(r_data)
        data_list = list(r_data)
        print(data_list)
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

    def ShowNum(self, cmd, data_list):
        temp = [1, 0.1, 0.01, 0.001]
        if cmd[3] <= 5:
            UnitNum = temp[1]
            value = (data_list[3] * 256 + data_list[4]) * UnitNum
            print(value)
        elif 48 <= cmd[3] <= 51:
            UnitNum = temp[2]
            value = (data_list[3] * 256 + data_list[4] + data_list[5] * (256 ** 3) + data_list[6] * (
                        256 ** 2)) * UnitNum
            print(value)
        else:
            UnitNum = temp[0]
            value = 0
            print("Not in case.")
        return value

            
if __name__ == '__main__':
    print("--------New---------")
    com = Communicate()
    cmd = [1, 3, 0, 0, 0, 1]
    data_list = com.trans_serial(cmd)
    com.ShowNum(cmd, data_list)
    cmd = [1, 3, 0, 48, 0, 2]
    data_list=com.trans_serial(cmd)
    com.ShowNum(cmd,data_list)
    cmd = [1, 3, 0, 50, 0, 2]
    data_list = com.trans_serial(cmd)
    com.ShowNum(cmd, data_list)

