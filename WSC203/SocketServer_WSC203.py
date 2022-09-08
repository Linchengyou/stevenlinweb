import socket
import serial
import gpio
import communicate as comun

import threading
HOST = '0.0.0.0'
PORT = 8888
class ClientThread(threading.Thread):
    def __init__(self,clientAddress,clientsocket):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        print ("New connection added: ", clientAddress)
    def run(self):
        lock.acquire()
        print("lock acquire")
        print ("Connection from : ", clientAddress)
        #self.csocket.send(bytes("Hi, This is from Server..",'utf-8'))
        msg = ''
        while True:
            data = self.csocket.recv(1024)
            print(data)
            print(type(data))
            msg = data.decode()
            if msg=='bye' or data==b'':
              break
            elif msg=="喚醒" :
                msg = "醒了"
                self.csocket.send(msg.encode())            
            elif msg== "485" :
                com = comun.Communicate()
                cmd= [[1, 3, 0, 0, 0, 1],[1, 3, 0, 48, 0, 2],[1, 3, 0, 50, 0, 2]]
                label = ["V: ","kWh: ","kVArh: "]
                temp=""
                for i in range(3):
                    data_list = com.trans_serial(cmd[i])
                    NUM = com.ShowNum(cmd[i], data_list)
                    temp=temp+label[i]+str(NUM)+","
                self.csocket.send(temp.encode())
            else:
                print ("from client", msg)
                self.csocket.send(bytes(msg,'UTF-8'))
        print ("Client at ", clientAddress , " disconnected...")
        lock.release()
        print("lock release")
# socket.socket([family[, type[, proto]]])
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
    
    


