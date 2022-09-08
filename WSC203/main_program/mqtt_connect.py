import threading
import pathlib
import json
import logging.config
import config.logging_config as logging_config
import lib.gatewaylib as gatewaylib
import signal
import paho.mqtt.client as mqtt
import time
import uuid
import netifaces


class MQTTpush:
    CPU_TEMPERATURE_PATH = '/sys/class/thermal/thermal_zone0/temp'

    def __init__(self):
        self.cpu_temperature_path = pathlib.Path(self.CPU_TEMPERATURE_PATH)
        self.__uuid = uuid.uuid5(uuid.NAMESPACE_DNS, "wsc")
        logger.info('uuid:{}'.format(self.__uuid))
        self.__dir = str(pathlib.Path(__file__).parent)  # 當前專案目錄
        self.__config_file_path = self.__dir + '/config/config.json'  # config檔路徑
        self.__config_file = pathlib.Path(self.__config_file_path)  # config檔路徑物件
        self.__config = None
        self.__networking = False  # 是否取得網路介面
        self.__stop_event = threading.Event()
        self.__init_config()  # 初始化 Gateway 基礎設定檔
        self.__journal_dict = dict()  # journal紀錄dict
        self.mqtt_client = mqtt.Client()
        self.__init_mqtt()  # 初始化 MQTT

    def __init_config(self):
        """
        config初始化
        """
        # 取得本機網路介面資訊
        interface_dict = self.get_network_interface_info()
        self.__networking = False if interface_dict is None or len(interface_dict) == 0 else True
        # 取得config資料，並更新web config
        if self.__config_file.is_file():
            self.__config = json.loads(self.__config_file.read_text(encoding='utf-8'), encoding='utf-8')
        if 'gateway' in self.__config:
            self.__config['gateway'].update(interface_dict)
        else:
            self.__config['gateway'] = interface_dict
        if not self.__networking:
            logger.error('Error: no network interface!')
        self.__refresh_config()

    def __refresh_config(self):
        interval = 3
        if self.__stop_event.is_set():
            return
        if self.__config is None:
            return
        if not self.__networking:
            gatewaylib.network_restart()
            interface_dict = network_interface.get_network_interface_info()
            self.__networking = False if not interface_dict else True
            if self.__networking:
                self.__config['gateway'].update(interface_dict)
                print('Retrieve network interface')
                logger.info('Retrieve network interface')

        self.__refresh_config_timer = threading.Timer(interval, self.__refresh_config)
        self.__refresh_config_timer.start()

    def __init_mqtt(self):
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.username_pw_set(username=self.__config['mqtt']['username'],
                                         password=self.__config['mqtt']['password'])
        try:
            self.mqtt_client.connect_async(self.__config['mqtt']['host'], self.__config['mqtt']['port'], 30)
            self.mqtt_client.loop_start()
        except Exception as e:
            print('MQTT Broker is not online. Connect later.{}'.format(e))
            logger.error('MQTT Broker is not online. Connect later.{}'.format(e))

    def on_mqtt_connect(self, mq, userdata, flags, rc):
        if rc == 0:
            logger.info('MQTT connect success!')
        self.mqtt_client.subscribe('{}/{}/#'.format(self.__uuid, self.__config['gateway']['mac']), qos=2)

    def on_mqtt_message(self, mq, userdata, msg):
        topic_array = msg.topic.split('/')
        if topic_array[1] != self.__config['gateway']['mac']:
            return
        if topic_array[2] == 'sys':
            try:
                mqtt_dict = json.loads(str(msg.payload, 'utf-8'), encoding='utf-8')
                if topic_array[3] == topic_array[-1] == 'ssh-open':
                    return_code = gatewaylib.ssh_open(mqtt_dict)
                    mq.publish('{}/result'.format(msg.topic), return_code, qos=2)
                    logger.warning('ssh-open! port:{}'.format(mqtt_dict['open_port']))
                elif topic_array[3] == topic_array[-1] == 'ssh-close':
                    return_code = gatewaylib.ssh_close()
                    mq.publish('{}/result'.format(msg.topic), return_code, qos=2)
                    logger.warning('ssh-close!')
                elif topic_array[3] == topic_array[-1] == 'reboot':
                    logger.warning('reboot: mqtt')
                    mq.publish('{}/result'.format(msg.topic), 0, qos=2)
                    gatewaylib.gateway_reboot()  # 需先執行重開的系統指令, 再關閉程式
                    self.close()
                elif topic_array[3] == topic_array[-1] == 'thermal':
                    logger.info('thermal: cpu')
                    mq.publish('{}/result'.format(msg.topic), self.cpu_temperature_path.read_text().strip(), qos=2)
            except Exception as ex:
                logger.error('ex'.format(ex))
                pass
                # mq.publish('{}/result'.format(msg.topic), '{}, data:{}'.format(str(ex), str(msg.payload)), qos=2)

    @staticmethod
    def get_network_interface_info():
        interface_gateway_list = netifaces.gateways()
        if netifaces.AF_INET not in interface_gateway_list:
            return None
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
            'mac': ':'.join(
                [('{:0>2x}'.format((uuid.getnode() >> i) & 0xff)).upper() for i in range(0, 8 * 6, 8)][::-1])
        }

    def run(self):
        while True:
            if self.__stop_event.is_set():
                break

            time.sleep(1)

    def signal_close(self, signum, stack):
        """
        關閉訊號
        """
        logger.warning('Receive stop signal: {}: {}'.format(signum, str(stack)))
        logger.warning('Application prepare to stop...')
        print('Receive stop signal: {}: {}'.format(signum, str(stack)))
        print('Application prepare to stop...')
        self.close()

    def close(self):
        """
        程式關閉
        """
        self.__stop_event.set()
        if self.mqtt_client is not None:
            self.mqtt_client.loop_stop(force=True)
            self.mqtt_client.disconnect()
            self.mqtt_client = None


if __name__ == '__main__':
    logging.config.dictConfig(logging_config.LOGGING_CONFIG)
    logger = logging.getLogger('mqtt')
    logger.propagate = False

    mqtt = MQTTpush()
    signal.signal(signal.SIGTERM, mqtt.signal_close)
    signal.signal(signal.SIGHUP, mqtt.signal_close)
    signal.signal(signal.SIGQUIT, mqtt.signal_close)
    signal.signal(signal.SIGINT, mqtt.signal_close)  # Ctrl-C

    app_service = threading.Thread(target=mqtt.run)
    app_service.start()
