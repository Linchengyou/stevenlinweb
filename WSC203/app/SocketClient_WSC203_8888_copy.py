from ast import main
import socket
import time 
import json

def ShowNum(cmd,data_list):
        temp=[1,0.1,0.01,0.001]
        if cmd[3]<=5:
            UnitNum=temp[1]
            value=(data_list[3] * 256 + data_list[4]) * UnitNum
            print(value)
        elif  48<=cmd[3]<=51:
            UnitNum = temp[2]
            value=(data_list[3] * 256 + data_list[4] + data_list[5] * (256 ** 3) + data_list[6] * (256 ** 2)) * UnitNum
            print(value)
        else:
            UnitNum = temp[0]
            value=0
            print("Not in case.")
        return value
def run():
    HOST = '172.16.1.172'
    PORT = 8888
    # TCP_socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    print(s.getpeername())
    outdata = '喚醒'
    # send 可用於傳送資料過去給串接對象，回傳值為要送出的字數。
    print('send: ' + outdata)
    # s.send(outdata.encode())
    cmd= [[1, 3, 0, 0, 0, 1],[1, 3, 0, 48, 0, 2],[1, 3, 0, 50, 0, 2]]
    label = ["V: ","kWh: ","kVArh: "]
    count=0
    LeavLoop=1
    print('開始抄表')
    temp=[]
    while LeavLoop==1:
        if count>2:
            count=count-3
            print(temp)
            print(json.dumps(temp))
            return json.dumps(temp)
            temp=[]
        # print(cmd[count])
        msg=cmd[count]
        # print(bytes(msg))
        s.send(bytes(msg))
        
        print("等待回復訊息.....")
        #recv 可用於接收資料，回傳值為接收到的資料
        indata = s.recv(1024)
        # print(list(bytes(indata)))
        NUM = ShowNum(cmd[count], list(bytes(indata)))
        temp.append(label[count]+ str(NUM))
        print('recv: ' +label[count]+ str(NUM))
        count=count+1
        time.sleep(0.5)
    s.close()
if __name__ == '__main__':
    run()