import json
import requests
from utils.public import *
from utils.mqueue import ConcurrentQueue
from utils.http_tool import http_post
import threading

def seng_msg(msg):
    resp = http_post(Cfg["msg_url"],{"msgtype": "text","text": {"content": msg}})
    if resp == None or resp["errcode"] != 0:
        print("[seng_msg] error resp:%s"%(resp))

class MsgHandler:
    def __init__(self):
        self.__msg_queue = ConcurrentQueue()
        threading.Thread(target=self.__asyn_sender).start()


    def asyn_send(self,msg):
        self.__msg_queue.put(msg)

    def __asyn_sender(self):
        while True:
            msg = self.__msg_queue.get_with_wait()
            seng_msg(msg)