import time
import toml
import math
import datetime
Cfg = toml.load('./csfile/gscc.toml')
TM_FORMAT = "%Y-%m-%d %H:%M:%S"

pd2int = {
    "1min":60,"3min":180,"5min":300,"15min":900,"30min":1800,
    "60min":3600,"4hour":14400,"1day":86400,
    "1week":604800,"30day":2592000}

#返回时间戳在本地时间是星期几
def sjc2localweekday(sjc):
    tm_str = sjc2localtm(sjc)
    tm_dt = datetime.datetime.strptime(tm_str,"%Y-%m-%d %H:%M:%S")
    return tm_dt.isoweekday()

#返回当前时间戳所在周期的id,以本地时间00:00为周期起点
def std_pd_tm(sjc,period='1min'):
    return sjc - (sjc - time.timezone)%pd2int[period]

#本地时间到时间戳
def localtm2sjc(tm):
    timeArray = time.strptime(tm, "%Y-%m-%d %H:%M:%S")
    timeStamp = int(time.mktime(timeArray))
    return timeStamp

#时间戳到本地时间
def sjc2localtm(ts,format = None):
    if not format:
        format = "%Y-%m-%d %H:%M:%S"
    return time.strftime(format,time.localtime(ts))

#utc0时间到时间戳
def utctm2sjc(tm):
    return localtm2sjc(tm) - time.timezone

#时间戳到utc0时间
def sjc2utctm(ts):
    return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(ts + time.timezone))

#时间戳到iso时间
def sjc2isotm(ts):
    return time.strftime('%Y-%m-%dT%H:%M:%S.000Z',time.localtime(ts + time.timezone))

#iso时间到时间戳
def isotm2sjc(tm):
    timeArray = time.strptime(tm, "%Y-%m-%dT%H:%M:%S.000Z")
    timeStamp = int(time.mktime(timeArray))
    return timeStamp - time.timezone

#标准化价格
def format_price(ori_price,t_type,mod = 0):
    """
    :param ori_price:
    :param t_type:  btcusdt,ltc..
    :param mod: 0 round, 1 upper ,-1 floor
    :return:
    """
    if "btc" in t_type or "BTC" in t_type:
        xiaoshu = 1
    elif "eth" in t_type or "ETH" in t_type:
        xiaoshu = 2
    elif "ltc" in t_type or "LTC" in t_type:
        xiaoshu = 2
    else:
        raise ValueError("t_type not support")
    ori_price = ori_price*10**xiaoshu
    if mod == 0:
        ret = round(ori_price)
    elif mod == 1:
        ret = math.floor(ori_price)+1
    else:
        ret = math.floor(ori_price)
    return ret/10**xiaoshu