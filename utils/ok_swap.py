# -*- coding: utf-8 -*-
from okex.v5 import Swap
from utils.public import *
from utils.log_config import *

__api_key = ''
__seceret_key = ''
__passphrase = ''



api = Swap(__api_key,__seceret_key,__passphrase)
zhang2mout = {"BTC-USDT-SWAP":0.01,"ETH-USDT-SWAP":0.1,"LTC-USDT-SWAP":1.0,
              "btcusdt":0.01,"ethusdt":0.1,"ltcusdt":0.1,
              "btc":0.01,"eth":0.1,"ltc":0.1,
              "BTCUSDT":0.01,"ETHUSDT":0.1,"LTCUSDT":0.1,
              "BTC":0.01,"ETH":0.1,"LTC":0.1}

MAX_LEN = 100
def __format_type(type):
    type = str(type).upper()
    if type.__contains__("BTC"):
        type = "BTC"
    elif type.__contains__("ETH"):
        type = "ETH"
    elif type.__contains__("BCH"):
        type = "BCH"
    elif type.__contains__("ETC"):
        type = "ETC"
    elif type.__contains__("LTC"):
        type = "LTC"
    elif type.__contains__("BSV"):
        type = "BSV"
    elif type.__contains__("XRP"):
        type = "XRP"
    else:
        raise RuntimeError("[okeyAPI] type:(%s) error"%(type))
    return type

class OkOrderType:
    market = 'market'         #市价单
    limit = 'limit'           #限价单
    post_only = 'post_only'   #只做Maker
    foc = 'fok'           #全部成交或立即取消
    ioc = 'ioc'           #立即成交并取消剩余
    optimal_limit_ioc = 'optimal_limit_ioc' #市价委托立即成交并取消剩余（仅适用交割、永续）

class OkOrderOp:
    add_many = ('buy','long')
    add_less = ('sell','short')
    dec_many = ('sell','long')
    dec_less = ('buy','short')

class OkOrderState:
    cancel_succ = 'canceled'
    wait_deal = 'live'
    some_deal = 'partially_filled'
    all_deal = 'filled'


class OkOrderInfo:
    def __init__(self):
        self.instrument_id = ''
        self.zhang = 0
        self.create_time = ''
        self.filled_qty = 0
        self.fee_usdt = 0.0
        self.id = 0
        self.real_price = 0.0
        self.op = None
        self.state = ''
    def __str__(self):
        return '''{"instrument_id":"%s","zhang":%d,"create_time":"%s","filled_qty":%d,"fee_usdt":%.5f,"id":%d,"real_price":%.4f,"op":"%s","state":"%s"}''' % \
               (self.instrument_id,self.zhang,self.create_time,self.filled_qty,self.fee_usdt,self.id,self.real_price,self.op,self.state)

def get_order_info(type,oid):
    # type: (str,int) -> OkOrderInfo
    type = __format_type(type)
    type += "-USDT-SWAP"
    try:
        res = api.order_info(instrument_id=type,order_id=oid)
        if res['code'] != '0':
            return None
        res = res['data'][0]
    except Exception as e:
        log_error("[ok_swap] get_order_info except %s" % (str(e)))
        return None
    oinfo = OkOrderInfo()
    oinfo.id = int(oid)
    oinfo.filled_qty = int(res['accFillSz'])
    oinfo.zhang = int(res['sz'])
    oinfo.create_time = int(float(res['cTime'])/1000)
    oinfo.fee_usdt = float(res['fee'])
    oinfo.instrument_id = res['instId']
    oinfo.op = (res['side'],res['posSide'])
    oinfo.state = res['state']
    oinfo.real_price = float(res['avgPx'] or 0)
    return oinfo

def take_order(otype,op,use_usdt=-1.0,order_amout = -1):
    # type:(str,tuple,float,int) -> (float,float,OkOrderInfo)
    otype = __format_type(otype)
    otype += "-USDT-SWAP"

    ori_amout = order_amout
    has_create = False
    order_id = ""
    while True:
        #创建订单
        if has_create == False:
            if ori_amout <= 0:
                # 获取当前价格
                price = 0
                kl, _, err = api.get_klines(otype, "1min", 5)
                if err:
                    log_error("[okAPI] __take_order get_kline [err]={}".format(err))
                    time.sleep(1)
                    continue
                else:
                    price = kl[-1]["close"]
                order_amout = int(use_usdt/price/zhang2mout[otype])
            log_info("[okapi] __take_order call api.take_order [t_type]=%s [zhang]=%d [dir]=%s"%(otype,order_amout,op))
            try:
                res = api.take_order(
                    instrument_id=otype,
                    size=order_amout,
                    dir=op[0],
                    pos_side=op[1],
                    order_type=OkOrderType.market,  # 市价下单
                )
                if not res or res['code'] != '0':
                    log_error("[ok_swap] __take_order res:%s"%(str(res)))
                    time.sleep(2)
                    continue
                else:
                    order_id = res["data"][0]['ordId']
                    has_create = True
            except Exception as e:
                log_error("[ok_swap] __take_order except %s"%(str(e)))
                time.sleep(2)
                continue

        #获取新创建订单信息
        log_info("[okapi] __take_order get_order_info oid:%d"%(int(order_id)))
        oinfo = get_order_info(otype,order_id)
        if not oinfo or oinfo.state != OkOrderState.all_deal:
            log_error("[ok_swap] __take_order oinfo error :%s"%(str(oinfo)))
            time.sleep(2)
            continue
        else:
            ori_usdt = int(oinfo.zhang) * float(oinfo.real_price) * zhang2mout[otype]
            fee = -float(oinfo.fee_usdt)
            amout = float(oinfo.zhang)*zhang2mout[otype]

            #将手续费考虑进入,计算花费/得到的 usdt 和成交均价
            usdt = 0
            if op == OkOrderOp.add_many:   #开多
                usdt = ori_usdt+fee
            elif op == OkOrderOp.add_less: #开空
                usdt = ori_usdt-fee
            elif op == OkOrderOp.dec_many: #平多
                usdt = ori_usdt-fee
            elif op == OkOrderOp.dec_less: #平空
                usdt = ori_usdt+fee
            return usdt,usdt/amout,oinfo

def marker_order(otype,op,price,zhang):
    #type: (str,tuple,float,int) -> int
    otype = __format_type(otype)
    otype += "-USDT-SWAP"
    log_info("_com_request_in||func=marker_order||otype=%s||zhang=%d||price=%.2f||op=%s"%(otype,zhang,price,op))
    try:
        res = api.take_order(
            instrument_id=otype,
            size=zhang,
            dir=op[0],
            pos_side=op[1],
            price=price,
            order_type=OkOrderType.limit
        )
        if not res or res['code'] != '0':
            log_error("[ok_swap] __marker_order res:%s" % (str(res)))
            return 0
        else:
            return res["data"][0]['ordId']
    except Exception as e:
        log_error("[ok_swap] __marker_order except %s" % (str(e)))
    return 0

def cancel_marker_order(otype,oid):
    #type: (str,int) -> bool
    otype = __format_type(otype)
    otype += "-USDT-SWAP"
    log_info("com_request_in||func=cancel_marker_order||otype=%s||oid=%d"%(otype,oid))
    try:
        res = api.cancel_order(
            order_id=str(oid),
            instrument_id=otype,
        )
        if not res or res['code'] != '0':
            log_error("[ok_swap] __cancel_marker_order res:%s" % (str(res)))
            return False
        return True
    except Exception as e:
        log_error("[ok_swap] cancel_marker_order except %s" % (str(e)))
        return False
