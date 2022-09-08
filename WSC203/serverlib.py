import threading
import pathlib
import json
import gpio
import serial
import datetime
import time


def getconfig():
    project_path = str(pathlib.Path(__file__).parents[1])  # 當前專案目錄
    config_file_path = pathlib.Path(project_path + '/config/config.json')  # 基礎設定檔的路徑物件
    config = None  # 基礎設定檔 dict

    if config_file_path.is_file():
        config = json.loads(config_file_path.read_text(encoding='utf-8'), encoding='utf-8')

    return config


wsc_config = getconfig()
if wsc_config['mcu']['mode'] == 1:
    serial_mode = "MBUS"
else:
    serial_mode = "DBUS"


class TServer(threading.Thread):
    def __init__(self, client_socket, client_adr, lock, conn_socket, inactivity_time):
        threading.Thread.__init__(self)
        self.socket = client_socket
        self.address = client_adr
        self.lock = lock
        self.conn_socket = conn_socket
        self.inactivity_time = inactivity_time

    def run(self):
        if self.inactivity_time > 0:
            self.socket.settimeout(self.inactivity_time)

        # print('Client {}:{} connected.'.format(self.address[0], self.address[1]))
        # print('active_count:{}'.format(threading.active_count() - 1))
        myserial = MySerial(serial_mode)
        while True:
            try:
                msg = self.socket.recv(512)
                if not msg:
                    break

                with self.lock:
                    try:
                        myserial.open_serial()
                        # print("{} data input: {} ".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                        #                                   list(msg)))
                        myserial.send_data(list(msg))
                        rt = myserial.read_data()
                    except Exception as e:
                        rt = []
                try:
                    # print("{} data output: {} ".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), rt))
                    self.socket.send(bytes(rt))
                except Exception as e:
                    break
            except Exception as ex:
                break

        self.conn_socket.pop(self.socket)
        self.socket.close()
        # print('Client {}:{} disconnected.'.format(self.address[0], self.address[1]))


class MySerial:
    def __init__(self, port_typ):
        self.ser = None
        self.port_typ = port_typ
        self.msg_header = None
        self.msg_data = None
        self.msg_length = 0

    def open_serial(self):
        if self.port_typ == "DBUS":
            self.ser = serial.Serial(**wsc_config['uart']['uart2'])
        else:
            self.ser = serial.Serial(**wsc_config['uart']['uart1'])

        if not self.ser.isOpen():
            self.ser.open()

    def send_data(self, msg):
        # modbus_type: 0: MODBUS　1: MODBUS-TCP
        if wsc_config['setting']['modbus_type'] == 1:
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
            gpio.set(wsc_config['gpio']['tr_pin'], True)  # 開啟tr_pin
            self.ser.write(msg)
            # self.ser.flush()
            if wsc_config['uart']['uart1']['baudrate'] in [1200]:
                sleep_timeout = (len(msg) + 1) * 0.001 * 8
            elif wsc_config['uart']['uart1']['baudrate'] in [2400]:
                sleep_timeout = (len(msg) + 1) * 0.001 * 4
            elif wsc_config['uart']['uart1']['baudrate'] in [4800]:
                sleep_timeout = (len(msg) + 1) * 0.001 * 2
            elif wsc_config['uart']['uart1']['baudrate'] in [9600]:
                sleep_timeout = (len(msg) + 1) * 0.001
            elif wsc_config['uart']['uart1']['baudrate'] in [19200]:
                sleep_timeout = (len(msg) + 1) * 0.001 / 2
            else:
                sleep_timeout = (len(msg) + 1) * 0.001 / 4
            time.sleep(sleep_timeout)
            # wiringpi.digitalWrite(1, 0)
            gpio.set(wsc_config['gpio']['tr_pin'], False)  # 開啟tr_pin
            # time.sleep(0.005)
            self.ser.reset_input_buffer()

    def read_data(self):
        r_data = b''
        # print("{} start read ".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")))
        # ini_time = datetime.datetime.now()
        while True:
            r = self.ser.read()
            # print("{} read data: {} ".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), r))
            # print("delte:{}".format(datetime.datetime.now()-ini_time))
            # ini_time = datetime.datetime.now()
            if len(r) == 0:
                break
            else:
                if self.port_typ == "DBUS":
                    self.ser.timeout = 0.015
                # else:
                #     if wsc_config['uart']['uart1']['baudrate'] in [1200, 2400, 4800]:
                #         self.ser.timeout = 0.2
                #     else:
                #         self.ser.timeout = 0.05
            r_data += r
        # r_data = self.ser.read(256)
        data_list = list(r_data)
        # modbus_type: 0: MODBUS　1: MODBUS-TCP
        if wsc_config['setting']['modbus_type'] == 1:
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
