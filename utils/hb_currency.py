from hbapi import currency as api
from utils.public import *
from concurrent.futures import ThreadPoolExecutor


def _job_get_history_kline(args):
    # https://api.coincap.io/v2/markets?quoteId=tether
    type_conv = {"btcusdt": "bitcoin", "ethusdt": "ethereum", "ltcusdt": "litecoin", "xrpusdt": "ripple",
                 "eosusdt": "eos", "bchusdt": "bitcoin-cash",
                 "trxusdt": "tron", "htusdt": "huobi-token", "omgusdt": "omisego", "zecusdt": "zcash",
                 "etcusdt": "ethereum-classic", "xmrusdt": "monero"}

    # https://docs.coincap.io/?version=latest#intro
    preiod_conv = {"1min": "m1", "5min": "m5", "15min": "m15", "30min": "m30", "60min": "h1", "4hour": "h4",
                   "1day": "d1",
                   "1week": "w1"}

    url = "http://api.coincap.io/v2/candles"
    params = {"exchange":args['change'],"quoteId":"tether"}
    params["interval"] = preiod_conv[args["period"]]
    params["baseId"] = type_conv[args["type"]]
    params["start"] = 1000 * args["st"]
    params["end"] = 1000 * args["ed"]
    res = api.http_get_request(url, params)
    if res == None:
        args["ret"] = False
        print("[coincap] get kline error %s" % (str(args)))
        return
    for kl in res['data']:
        kl["id"] = int(kl["period"]/1000)
        kl["open"] = float(kl["open"])
        kl["high"] = float(kl["high"])
        kl["low"] = float(kl["low"])
        kl["close"] = float(kl["close"])
        kl["amount"] = float(kl["volume"])
        kl.pop("period")
        kl.pop("volume")
        args["res"].append(kl)
    args['ret'] = True

# 不能用于实时数据的获取
def _get_history_kline(type,period,st,ed = -1,change='huobi',per=500):
    if isinstance(st, str): st = localtm2sjc(st)
    if isinstance(ed,str):ed = localtm2sjc(ed)
    if ed == -1 or ed >=time.time():
        ed = time.time()
    base = localtm2sjc("2011-09-05 00:00:00")
    st_pos = int((st-base-1)/pd2int[period])+1
    ed_pos = int((ed-base-1)/pd2int[period])+1
    num = ed_pos-st_pos
    st = base+st_pos*pd2int[period]
    ed = base+ed_pos*pd2int[period]
    if num <= 0:
        print("[coincap] empty num st:%d ed:%d period:%d"%(st,ed,pd2int[period]))
        return []
    job_num = int(num/per)
    if num%per >0:job_num += 1
    thd_args = []
    with ThreadPoolExecutor(job_num) as pool:
        for i in range(0,job_num):
            args = {"type":type,"period":period,"change":change,"ret":False,"res":[]}
            st_i = st+i*per*pd2int[period]
            ed_i = min(st+(i+1)*per*pd2int[period],ed)
            args["st"] = st_i
            args["ed"] = ed_i
            thd_args.append(args)
            pool.submit(_job_get_history_kline,args)
    res = []
    for arg in thd_args:
        if arg["ret"] == False:
            continue
        res += arg["res"]
    return res



class HbCurrency():
    def __init__(self,logger=None):
        # type:(Logger) -> None
        if logger:
            self.__log_info = logger.info
            self.__log_error = logger.error
        else:
            from utils.log_config import log_error,log_info, Logger
            self.__log_info = log_info
            self.__log_error = log_error
    def __format_tt(self,t_type):
        t_type = t_type.lower()
        if 'btc' in t_type:
            return 'btcusdt'
        if 'eth' in t_type:
            return 'ethusdt'
        if 'ltc' in t_type:
            return 'ltcusdt'
        if 'ht' in t_type:
            return 'htusdt'
    def get_klines(self,t_type,period,size=None,from_tms=None,to_tms=None):
        # type:(str,str,int,int,int) -> (list,int,str)
        t_type = self.__format_tt(t_type)
        try:
            if size:
                klines = api.get_kline(t_type, period, size)
                if not klines or klines["status"] != "ok":
                    return None,None,"resp None [status]={}".format(klines["status"])
                if len(klines["data"]) == 0:
                    return None,None,"kline resp have no data"
                data = []
                for kl in klines["data"]:
                    kl.pop("vol")
                    kl.pop("count")
                    data.append(kl)
                return sorted(data, key=lambda kl: kl["id"]), int(klines["ts"] / 1000),''
            else:
                res = _get_history_kline(t_type,period,from_tms,to_tms)
                if not res:
                    return None, None, "kline resp have no data"
                else:
                    return res,0,''
        except Exception as e:
            return None,None,'{}'.format(e)



# def create_order(symbol,amout,buy,price = 0):
#     """
#     :arg amout: 只有在市场价买时才是usdt,其余均为ht
#     :arg buy: 0 表示卖
#               1 表示买
#     :arg price: 默认0 以市场价交易
#                 非0 限价交易
#     :return oid: -1 表示失败
#     """
#     log_info("create_order||amout=%f||buy=%d||price=%f"%(amout,buy,price))
#     if buy:
#         if price:
#             type = "buy-limit"
#         else:
#             type = "buy-market"
#     else:
#         if price:
#             type = "sell-limit"
#         else:
#             type = "sell-market"
#     try:
#         resp = api.send_order(amout,symbol,type,price)
#     except:
#         log_error("Create order failed!")
#         return -1
#     if not resp:
#         log_error("Create order resp is null")
#         return -1
#     if resp["status"] != "ok":
#         print(resp)
#         log_error("Create order resp status false||err-code=%s" % resp["err-code"])
#         return -1
#     oid = int(resp["data"])
#     while True:
#         if get_order_info(oid) != -1:
#             break
#         time.sleep(1)
#         log_error("Create order get order info failed")
#     return oid

#返回订单是否完全成交,成交usdt数量,成交ht数量
# -1 异常
#  0 未成交
#  1 成交
# def get_order_info(oid):
#     """
#     info["data"]中内容：
#     字段               是否必须   类型      含义
#     account-id	        true	long	账户 ID
#     amount	            true	string	订单数量
#     canceled-at	        false	long	订单撤销时间
#     created-at	        true	long	订单创建时间
#     field-amount        true	string	已成交数量
#     field-cash-amount   true	string	已成交总金额
#     field-fees	        true	string	已成交手续费（买入为币，卖出为钱）
#     finished-at	        false	long	订单变为终结态的时间，不是成交时间，包含“已撤单”状态
#     id	    true	long	订单ID
#     price	true	string	订单价格
#     source	true	string	订单来源	api
#     state	true	string	订单状态	submitting , submitted 已提交, partial-filled 部分成交, partial-canceled 部分成交撤销, filled 完全成交, canceled 已撤销
#     symbol	true	string	交易对	btcusdt, ethbtc, rcneth ...
#     type	true	string	订单类型	buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖, buy-ioc：IOC买单, sell-ioc：IOC卖单
#     """
#     try :
#         info  = api.order_info(oid)
#     except:
#         log_error("get order info error||oid=%d" % oid)
#         return -1,-1
#     if info["status"] != "ok":
#         log_error("get order info resp status not ok||oid=%d" % oid)
#         return -1,-1
#     data = info["data"]
#     if info["data"]["state"] == "filled":
#         usdt_amout = float(info["data"]["field-cash-amount"])
#         amout = float(info["data"]["field-amount"])
#         fee_amout = float(data["field-fees"])
#         if data["type"] in ("buy-market", "buy-limit", "buy-ioc"): #buy
#             amout -= fee_amout
#         else:     #sell
#             usdt_amout -= fee_amout
#         return 1,usdt_amout,amout
#     else:
#         return 0,-1
#
# def cancel_order(order_id):
#     log_info("cancel_order||oid=%d" % order_id)
#     if order_id == 0: return 0
#     try:
#         resp = api.cancel_order(order_id)
#     except:
#         log_error("Cancel order faild||oid=%d"%order_id)
#         return -1
#     if not resp:
#         log_error("cancel order resp is null")
#         return -1
#     if resp["status"] != "ok":
#         log_error("cancel order resp status false||err-code=%s" % resp["err-code"])
#         return -1
#     get_order_info(order_id,True)
#     return 0