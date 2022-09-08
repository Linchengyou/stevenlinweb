import subprocess
import gpio
import logging
import time
from pathlib import Path
import threading
from werkzeug.security import generate_password_hash
import sqlite3
from contextlib import closing
import signal


class Reset:
    def __init__(self):
        self.__stop_event = threading.Event()
        self.file_path = '/home/dae/wsc/RESET/'
        self.btn_pin = 64
        self.red_light_pin = 203
        gpio.setwarnings(False)
        gpio.log.setLevel(logging.WARNING)
        gpio.cleanup(self.btn_pin)
        gpio.cleanup(self.red_light_pin)
        gpio.setup(self.red_light_pin, gpio.OUT)
        gpio.setup(self.btn_pin, gpio.IN)
        gpio.set(self.red_light_pin, True)
        self.pass_time = 0
        db_name = 'mydb.db'
        self.db_file_path = '/home/dae/wsc/' + db_name  # DB路徑

    def run(self):
        print('reset button on!')
        while True:
            if self.__stop_event.is_set():
                break
            if gpio.input(self.btn_pin) == 0:
                gpio.set(self.red_light_pin, False)
                begin_time = time.time()
                while True:
                    if self.__stop_event.is_set():
                        break
                    self.pass_time = time.time() - begin_time
                    time.sleep(0.1)
                    if gpio.input(self.btn_pin) == 1:
                        gpio.set(self.red_light_pin, True)
                        break
                    if self.pass_time > 5:
                        print('reset')
                        i = 0
                        u_dict = dict()
                        u_dict['password_hash'] = generate_password_hash('admin')
                        self.update_password('admin', u_dict)
                        subprocess.Popen(
                            'sudo python3 {}network.py static {} {} {} {}'.format(self.file_path, '192.168.1.234',
                                                                                  '255.255.255.0', '192.168.1.1',
                                                                                  '8.8.8.8'), shell=True)
                        # subprocess.Popen('sudo systemctl restart gateway-ssdp.service', shell=True)

                        while i < 6:
                            if self.__stop_event.is_set():
                                break
                            gpio.set(self.red_light_pin, False)
                            time.sleep(0.2)
                            gpio.set(self.red_light_pin, True)
                            time.sleep(0.2)
                            i += 1
                        self.pass_time = 0
                        break
            else:
                time.sleep(0.1)

    def update_password(self, username, update_dict):
        cmd = "UPDATE User SET "
        cmd_list = []
        for key, value in update_dict.items():
            cmd_list.append("{}='{}'".format(key, value))
        cmd = cmd + ','.join(cmd_list) + " WHERE username='{}'".format(username)
        # print(cmd)
        with closing(sqlite3.connect(self.db_file_path)) as con:
            with con:
                with closing(con.cursor()) as cursor:
                    cursor.execute(cmd)

    def signal_close(self, signum, stack):
        """
        關閉訊號
        """
        print('Receive stop signal: {}: {}'.format(signum, str(stack)))
        print('Application prepare to stop...')
        self.close()

    def close(self):
        """
        程式關閉
        """
        self.__stop_event.set()


if __name__ == '__main__':
    a = Reset()
    # a.run()

    signal.signal(signal.SIGTERM, a.signal_close)
    signal.signal(signal.SIGHUP, a.signal_close)
    signal.signal(signal.SIGQUIT, a.signal_close)
    signal.signal(signal.SIGINT, a.signal_close)  # Ctrl-C

    app_service = threading.Thread(target=a.run)
    app_service.start()
