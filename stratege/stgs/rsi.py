from utils.ok_swap import marker_order,cancel_marker_order,get_order_info,OkOrderState,zhang2mout,OkOrderOp
from stratege.type_define import StgUnit
from utils.log_config import log_info
from utils.public import *
import  json

UseZhang = {
    'btcusdt' : 10,
    'ethusdt' : 3,
    'ltcusdt' : 2,
}
class RsiHighRateTrade(StgUnit):
    def __init__(self, gscc, sim, vail):
        StgUnit.__init__(self, gscc, sim, vail)
        self.usdt = 0
        self.duo_zhang = 0
        self.kong_zhang = 0
        self.low_buy_oid = 0
        self.low_sell_oid = 0
        self.high_buy_oid = 0
        self.high_sell_oid = 0
        self.low_buy_info = None
        self.low_sell_info = None
        self.high_buy_info = None
        self.high_sell_info = None

    def run(self):
        if self.vail == False or self.sim:
            return
        dc = self.gscc.dc
        rsi_mgr = dc.rsi("1min")
        #获取四个价位
        #
        # ------- high_buy  rsi=0.8   高位开空价
        #
        # ------- low_sell  rsi=0.5   平多价
        # ------- high_sell rsi=0.5   平空价
        #
        #
        # ------- low_buy   rsi=0.8   地位开多价

        t_type = dc.type
        low_buy = format_price(rsi_mgr.inverse(0.25),t_type)
        high_buy = format_price(rsi_mgr.inverse(0.8),t_type)
        low_sell = format_price(rsi_mgr.inverse(0.5),t_type)
        high_sell = format_price(rsi_mgr.inverse(0.5),t_type)
        log_info("RsiHighRateTrade||low_buy=%.2f||low_sell=%.2f||low_buy_oid=%d||low_sell_oid=%d||duo_zhang=%d"%
                 (low_buy,low_sell,self.low_buy_oid,self.low_sell_oid,self.duo_zhang))
        log_info("RsiHighRateTrade||high_buy=%.2f||high_sell=%.2f||high_buy_oid=%d||high_sell_oid=%d||kong_zhang=%d"%
                 (high_buy,high_sell,self.high_buy_oid,self.high_sell_oid,self.kong_zhang))
        #查看订单成交情况 & 计算盈亏 & 取消订单
        if self.low_buy_oid: #
            deal_num = 0
            self.low_buy_info = get_order_info(t_type,self.low_buy_oid)
            if self.low_buy_info:
                if self.low_buy_info.state == OkOrderState.all_deal:
                    deal_num = self.low_buy_info.filled_qty
                    self.low_buy_oid = 0
                elif self.low_buy_info.state == OkOrderState.some_deal:
                    deal_num = self.low_buy_info.filled_qty
                if deal_num > 0:
                    self.duo_zhang += deal_num
                    self.usdt -= 1.0002 * deal_num * zhang2mout[t_type] * self.low_buy_info.real_price
                    log_info("RsiHighRateTrade deal||low_buy||num=%d"%(deal_num))
                if self.low_buy_oid:
                    if cancel_marker_order(t_type,self.low_buy_oid):
                        self.low_buy_oid = 0

        if self.low_sell_oid:
            deal_num = 0
            self.low_sell_info = get_order_info(t_type,self.low_sell_oid)
            if self.low_sell_info:
                if self.low_sell_info.state == OkOrderState.all_deal:
                    deal_num = self.low_sell_info.filled_qty
                    self.low_sell_oid = 0
                elif self.low_sell_info.state == OkOrderState.some_deal:
                    deal_num = self.low_sell_info.filled_qty
                if deal_num >0 :
                    self.duo_zhang -= deal_num
                    self.usdt += 0.9998 * deal_num * zhang2mout[t_type] * self.low_sell_info.real_price
                    log_info("RsiHighRateTrade deal||low_sell||num=%d" % (deal_num))
                if self.low_sell_oid:
                    if cancel_marker_order(t_type,self.low_sell_oid):
                        self.low_sell_oid = 0

        if self.high_buy_oid:
            deal_num = 0
            self.high_buy_info = get_order_info(t_type,self.high_buy_oid)
            if self.high_buy_info:
                if self.high_buy_info.state == OkOrderState.all_deal:
                    deal_num = self.high_buy_info.filled_qty
                    self.high_buy_oid = 0
                elif self.high_buy_info.state == OkOrderState.some_deal:
                    deal_num = self.high_buy_info.filled_qty
                if deal_num > 0:
                    self.kong_zhang += deal_num
                    self.usdt += 0.9998 * deal_num * zhang2mout[t_type] * self.high_buy_info.real_price
                    log_info("RsiHighRateTrade deal||high_buy||num=%d" % (deal_num))
                if self.high_buy_oid:
                    if cancel_marker_order(t_type,self.high_buy_oid):
                        self.high_buy_oid = 0

        if self.high_sell_oid:
            deal_num = 0
            self.high_sell_info = get_order_info(t_type,self.high_sell_oid)
            if self.high_sell_info:
                if self.high_sell_info.state == OkOrderState.all_deal:
                    deal_num = self.high_sell_info.filled_qty
                    self.high_sell_oid = 0
                elif self.high_sell_info.state == OkOrderState.some_deal:
                    deal_num = self.high_sell_info.filled_qty
                if deal_num > 0:
                    self.kong_zhang -= deal_num
                    self.usdt -= 1.0002 * deal_num * zhang2mout[t_type] * self.high_sell_info.real_price
                    log_info("RsiHighRateTrade deal||high_sell||num=%d" % (deal_num))
                if self.high_sell_oid:
                    if cancel_marker_order(t_type,self.high_sell_oid):
                        self.high_sell_oid = 0

        #重新挂单
        if self.low_buy_oid == 0:
            self.low_buy_oid = marker_order(t_type,OkOrderOp.add_many,low_buy,UseZhang[t_type]-self.duo_zhang)
        if self.low_sell_oid == 0:
            self.low_sell_oid = marker_order(t_type,OkOrderOp.dec_many,low_sell,self.duo_zhang)
        if self.high_buy_oid == 0:
            self.high_buy_oid = marker_order(t_type,OkOrderOp.add_less,high_buy,UseZhang[t_type]-self.kong_zhang)
        if self.high_sell_oid == 0:
            self.high_sell_oid = marker_order(t_type,OkOrderOp.dec_less,high_sell,self.kong_zhang)

    def dump_json(self):
        data = {
            "usdt":self.usdt,
            "low_sell_oid":self.low_sell_oid,
            "high_sell_oid":self.high_sell_oid,
            "low_buy_oid":self.low_buy_oid,
            "high_buy_oid":self.high_buy_oid,
            "duo_zhang":self.duo_zhang,
            "kong_zhang":self.kong_zhang,
        }
        return json.dumps(data)
    def load_json(self,js):
        data = json.loads(js)
        self.usdt = float(data["usdt"])
        self.low_sell_oid = int(data["low_sell_oid"])
        self.high_sell_oid = int(data["high_sell_oid"])
        self.low_buy_oid = int(data["low_buy_oid"])
        self.high_buy_oid = int(data["high_buy_oid"])
        self.duo_zhang = int(data["duo_zhang"])
        self.kong_zhang = int(data["kong_zhang"])
        return [self]

    def get_profit(self,cur_price):
        duo_zhang = self.duo_zhang - self.kong_zhang
        amout = zhang2mout[self.gscc.dc.type] * duo_zhang
        ori_usdt = amout * cur_price
        return self.usdt + ori_usdt