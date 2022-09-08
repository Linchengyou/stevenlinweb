import socket
import serial
import gpio
HOST = '0.0.0.0'
PORT = 8888

# socket.socket([family[, type[, proto]]])
#family: 套接字家族可以使 AF_UNIX 或者 AF_INET
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 解決Server 伺服器端不正常關閉後再次啟動
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))#綁定連接口
s.listen(5)

print('server start at: %s:%s' % (HOST, PORT))
print('wait for connection...')


conn, addr = s.accept()
print('connected by ' + str(addr))
outdata = "喚醒"
conn.send(outdata.encode())

LeavLoop=1
while LeavLoop==1:
    indata = conn.recv(1024)
    print('recv: ' + indata.decode())
    if indata.decode()=="你好" or indata.decode()=="hello":
        outdata = "你好"
        conn.send(outdata.encode())
    elif indata.decode()=="喚醒" or indata.decode()=="hello":
        outdata = "喚醒"
        conn.send(outdata.encode())
    elif indata.decode() == "離開" or indata.decode() == "exit":
        LeavLoop = 0
    elif indata.decode() == "485" :
        ser = serial.Serial(port="/dev/ttyS1", baudrate=9600, timeout=0.3, write_timeout=0.5)
        cmd= input("輸入[0,0,0,0,0,0]")
        cmd_crc = ser.get_modbus_crc(cmd)
        gpio.set(6, 1)
        ser.serial.write(cmd + cmd_crc)
        ser.serial.flush()
        gpio.set(6, 0)
        r_data = ser.serial.read(256)
        print(r_data)
        data_list = list(r_data)
        print(data_list)
        conn.send(data_list.encode())
    else:
        outdata = input("請回復訊息:")
        conn.send(outdata.encode())

conn.close()