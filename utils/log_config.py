import logging
import uuid
import threading
from utils.message import MsgHandler

g_uuid = threading.local()
uuid_append = threading.local()

g_uuid.str = ""
uuid_append.str = ""

#[%(filename)s:%(lineno)d]
__form = logging.Formatter(fmt='[%(asctime)s]%(message)s',
                     datefmt='%Y-%m-%d %H:%M:%S')

__fh_info = logging.FileHandler('./log/info.txt','w+')
__fh_wf = logging.FileHandler('./log/wf.txt','w+')

__log_info = logging.getLogger("INFO")
__fh_info.setFormatter(__form)
__log_info.addHandler(__fh_info)
__log_info.setLevel("INFO")
__log_wf = logging.getLogger("WARNING")
__fh_wf.setFormatter(__form)
__log_wf.addHandler(__fh_wf)
__log_wf.setLevel("WARNING")



msg_handler = MsgHandler()


def log_info(s):
    __log_info.info("[%s] %s"%(g_uuid.str + uuid_append.str,s))

def log_error(s):
    if uuid_append.str != "log":
        msg_handler.asyn_send(s)
    __log_wf.error("[%s] %s"%(g_uuid.str + uuid_append.str,s))

def refresh_log_uuid(s = ''):
    global g_uuid
    if s == '':
        ret = uuid.uuid4().hex[0:7]
    else:
        ret = s
    g_uuid.str = ret
    return ret


def set_uuid_append(s):
    global uuid_append
    uuid_append.str = s


class Logger:
    __g_uuid = threading.local()
    __uuid_append = threading.local()
    __g_uuid.str = ""
    __uuid_append.str = ""
    __form = logging.Formatter(fmt='[%(asctime)s]%(message)s',
                               datefmt='%Y-%m-%d %H:%M:%S')
    def __init__(self,info_name,wf_name,use_alarm = False):
        __fh_info = logging.FileHandler('./log/'+info_name, 'w+')
        __fh_wf = logging.FileHandler('./log/'+wf_name, 'w+')
        __log_info = logging.getLogger("INFO")
        __fh_info.setFormatter(self.__form)
        __log_info.addHandler(__fh_info)
        __log_info.setLevel("INFO")
        __log_wf = logging.getLogger("WARNING")
        __fh_wf.setFormatter(self.__form)
        __log_wf.addHandler(__fh_wf)
        __log_wf.setLevel("WARNING")
        self.__log_info = __log_info
        self.__log_wf = __log_wf
        self.__use_alarm = use_alarm
        if use_alarm:
            self.__msg_handler = MsgHandler()

    def info(self,s):
        self.__log_info.info("[%s] %s" % (self.__g_uuid.str + self.__uuid_append.str, s))

    def error(self,s):
        if self.__use_alarm:
            self.__msg_handler.asyn_send(s)
        self.__log_wf.error("[%s] %s" % (self.__g_uuid.str + self.__uuid_append.str, s))

    def set_uuid_append(self,s):
        self.__uuid_append.str = s

    def refresh_uuid(self,s=''):
        if s == '':
            ret = uuid.uuid4().hex[0:7]
        else:
            ret = s
        self.__g_uuid.str = ret
        return ret
