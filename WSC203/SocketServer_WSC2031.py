import socket
import serial
import gpio
import communicate as comun

import threading
HOST = '0.0.0.0'
PORT = 8888
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
        LeavLoop=1
        while LeavLoop==1:
            indata = self.socket.recv(1024)
            print('recv: ' + indata.decode())
            if indata.decode()=="你好" or indata.decode()=="hello":
                outdata = "你好"
                self.socket.send(outdata.encode())
            elif indata.decode()=="喚醒" :
                outdata = "醒了"
                self.socket.send(outdata.encode())   
            elif indata.decode()=="離開" or indata.decode()=="exit":
                outdata = "歡迎"
                self.socket.send(outdata.encode())          
            elif indata.decode() == "485" :
                com = comun.Communicate()
                cmd= [[1, 3, 0, 0, 0, 1],[1, 3, 0, 48, 0, 2],[1, 3, 0, 50, 0, 2]]
                label = ["V: ","kWh: ","kVArh: "]
                temp=""
                for i in range(3):
                    data_list = com.trans_serial(cmd[i])
                    NUM = com.ShowNum(cmd[i], data_list)
                    temp=temp+label[i]+str(NUM)+","
                self.socket.send(temp.encode())
            else:
                outdata = input("請回復訊息:")
                self.socket.send(outdata.encode())
        self.conn_socket.pop(self.socket)
        self.socket.close()
        # print('Client {}:{} disconnected.'.format(self.address[0], self.address[1]))


# socket.socket([family[, type[, proto]]])
#family: 套接字家族可以使 AF_UNIX 或者 AF_INET
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 解決Server 伺服器端不正常關閉後再次啟動
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))#綁定連接口
conn,adr = s.accept()

print('server start at: %s:%s' % (HOST, PORT))
print('wait for connection...')

conn_socket = {}
lock = threading.Lock()
print("Waiting for client request..")
while True:
    
    conn_socket[conn] = adr
    if len(conn_socket) > 5 :
        conn_socket.pop(conn)
        conn.close()
    else:
        ser_thread = TServer(conn, adr, lock, conn_socket, 10)
        ser_thread.setDaemon(True)
        ser_thread.start()

