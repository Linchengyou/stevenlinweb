import socket
import serial
import gpio


import threading
HOST = '0.0.0.0'
PORT = 8888
class ClientThread(threading.Thread):
    def __init__(self,clientAddress,clientsocket):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        self.mode = 1
        if self.mode==1:
            self.serial = serial.Serial(port="/dev/ttyS1", baudrate=9600, timeout=0.3, write_timeout=0.5)
        else:
            self.serial = serial.Serial(port="/dev/ttyS2", baudrate=38400, timeout=0.3, write_timeout=0.5)
        print ("New connection added: ", clientAddress)
    def trans_serial(self, cmd):
        if not self.serial.isOpen():
            self.serial.open()

        cmd_crc = self.get_modbus_crc(cmd)
        gpio.set(6, 1)
        self.serial.write(cmd + cmd_crc)
        self.serial.flush()
        gpio.set(6, 0)
        r_data = self.serial.read(256)
        #print(r_data)
        data_list = list(r_data)
        #print(data_list)
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
    def run(self):
        # lock.acquire()
        print("lock acquire")
        print ("Connection from : ", clientAddress)
        #self.csocket.send(bytes("Hi, This is from Server..",'utf-8'))
        msg = ''
        while True:
            data = self.csocket.recv(1024)
            # print("1",data)
            # print("2",type(data))
            msg = list(bytes(data))
            # print("3",msg)
            if msg=='bye' or data==b'':
              break          
            # lock.acquire()
            with lock:
                if msg== [1, 3, 0, 0, 0, 1]:
                    data_list = self.trans_serial(msg)
                    self.csocket.send(bytes(data_list))      
                elif msg== [1, 3, 0, 48, 0, 2]:
                    data_list = self.trans_serial(msg)
                    self.csocket.send(bytes(data_list))      
                elif msg== [1, 3, 0, 50, 0, 2]:
                    data_list = self.trans_serial(msg)
                    self.csocket.send(bytes(data_list))        
                else:
                    print ("from client", msg)
                    self.csocket.send(bytes(msg,'UTF-8'))
            # lock.release()
        print ("Client at ", clientAddress , " disconnected...")
        # lock.release()
        print("lock release")

#family: 套接字家族可以使 AF_UNIX 或者 AF_INET
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 解決Server 伺服器端不正常關閉後再次啟動
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))#綁定連接口
print('server start at: %s:%s' % (HOST, PORT))
print('wait for connection...')

print("Waiting for client request..")
lock = threading.Lock()
while True:
    s.listen(5)
    
    clientsock, clientAddress = s.accept()
    newthread = ClientThread(clientAddress, clientsock)
    newthread.start()
    print('connected by ' + str(clientAddress))
    
    


