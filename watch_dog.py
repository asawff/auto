import socket
import threading
import requests
from utils.public import *
from utils.message import seng_msg


class Dog:
    def __init__(self,tms):
        self.cnt = int(time.time())
        self.tms = tms
        threading.Thread(target=self.__loop).start()

    def reset(self):
        self.cnt = int(time.time())

    def __loop(self):
        while True:
            time.sleep(self.tms)
            now = int(time.time())
            if now >= self.cnt+self.tms:
                self.__alarm()
            self.cnt = now


    def __alarm(self):
        msg = "程序暂停! tm:%s"%(sjc2localtm(int(time.time())))
        seng_msg(msg)

def reset_dog():
    try:
        requests.get("http://127.0.0.1:12423")
    except:
        ""

def handle_client(client_socket,dog):
    """处理客户端请求"""
    # 获取客户端请求数据
    request_data = client_socket.recv(1024)
    response = "HTTP/1.1 200 OK\r\n"
    client_socket.send(bytes(response, "utf-8"))
    client_socket.close()
    dog.reset()


if __name__ == "__main__":
    build_succ = False
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while build_succ == False:
        try:
            server_socket.bind(("", 12423))
            server_socket.listen()
            build_succ = True
        except Exception as e:
            print(e)
            time.sleep(2)

    dog = Dog(120)
    while True:
        client_socket, client_address = server_socket.accept()
        handle_client(client_socket,dog)
