from utils.a_stock import STOCK_DICT,DbSession,Kline,get_today_kline
from utils.sch_job import DailySchJob
from utils.log_config import Logger
from utils.public import *


logger = Logger("st_info.txt","st_err.txt")

class OrderStatus:
    init = 0
    buy_market = 1
    finish_buy = 2
    sell_market = 3
    finish = 4

class Order:
    def __init__(self,st_code,st_name):
        self.st_code = st_code
        self.st_name = st_name
        self.is_st = 'ST' in st_name
        self.stat = OrderStatus.init
        self.shou = 0
        self.buy_price = 0
        self.sell_price = 0
        self.market_price = 0
        self.market_shou = 0
        self.create_time = ''
        self.finish_time = ''
    def buy(self,yst_price,cur_price,exp_mny,rest_mny,cur_tm):
        ztpercent = 1.1
        if self.is_st:
            ztpercent = 1.05
        ztprice = round(yst_price*ztpercent,2)
        use_marker_order = False
        if cur_price >= ztprice-0.01 and cur_price <= ztprice+0.01:
            use_marker_order = True
        if not use_marker_order:
            while (self.shou + 1)* 100 * cur_price < rest_mny:
                self.shou += 1
                if self.shou * 100 * cur_price > exp_mny:
                    break
            if self.shou > 0:
                self.stat = OrderStatus.finish_buy
                self.buy_price = cur_price
                self.create_time = cur_tm
        else:
            next_ztprice = round(ztprice*ztpercent,2)
            while (self.market_shou+1)*100 * next_ztprice <= rest_mny:
                self.market_shou += 1
                if self.market_shou*100*next_ztprice > exp_mny:
                    break
            if self.market_shou > 0:
                self.stat = OrderStatus.buy_market
                self.market_price = next_ztprice
    def sell(self,yst_price,cur_price,cur_tm):
        dtpercent = 0.9
        if self.is_st:
            dtpercent = 0.95
        dtprice = round(yst_price*dtpercent,2)
        use_marker_order = False
        if cur_price >= dtprice-0.01 and cur_price <= dtprice+0.01:
            use_marker_order = True
        if not use_marker_order:
            self.sell_price = cur_price
            self.stat = OrderStatus.finish
            self.finish_time = cur_tm
        else:
            self.market_shou = self.shou
            self.stat = OrderStatus.sell_market
            self.market_price = round(dtprice*dtpercent,2)
    def profit(self,cur_price):
        buy_fee = 0.0005
        sell_fee = 0.0015
        if self.stat in [OrderStatus.init,OrderStatus.buy_market]:
            return 0
        if self.stat in [OrderStatus.finish_buy , self.stat == OrderStatus.sell_market]:
            return (cur_price - self.buy_price)*100*self.shou - self.shou*100*self.buy_price * buy_fee
        return (self.sell_price - self.buy_price)*100*self.shou - self.shou*100*self.buy_price * buy_fee - self.shou*100*self.sell_price*sell_fee
    def look_mny(self):
        if self.stat in [OrderStatus.init,OrderStatus.finish]:
            return 0
        if self.stat == OrderStatus.buy_market:
            return self.market_shou*100*self.market_price
        return self.buy_price*100*self.shou


def _zt_price(st_code,p):
    st_name = STOCK_DICT[st_code]
    percent = 1.1
    if 'ST' in st_name:
        percent = 1.05
    return round(p*percent,2)

def _dt_price(st_code,p):
    st_name = STOCK_DICT[st_code]
    percent = 0.9
    if 'ST' in st_name:
        percent = 0.95
    return round(p * percent, 2)

def get_today_buy_target(wind):
    result = []
    session = DbSession()
    for st_code in STOCK_DICT:
        kls = session.query(Kline).filter(Kline.type==st_code).order_by(Kline.id.desc()).limit(wind).all()
        if kls:
            yst_close = kls[0].close
            max_20_c = -1
            for kl in kls:
                if kl.close > max_20_c:
                    max_20_c = kl.close
            zt_p = _zt_price(st_code,yst_close)
            if zt_p <= max_20_c:
                continue
            result.append([st_code,max_20_c])
    return result


class Astock():
    def __init__(self):
        self.olist = []
        self.today_sell = [] #for statistic
        self.today_buy = []  #for statistic
        self.dsch = DailySchJob()
        self.init_mny = 50000
        self.can_use_mny = 50000
        self.__buy_wind = 20
        self.__sell_wind = 10

    def hand_mark_order(self):
        ""
    def hand_sell(self):
        session = DbSession()
        sell_list = [] # [(order, sell_price, yst_price)]
        sell_code_list = []
        #检测当日可能卖出的st
        for o in self.current_olist:
            kls = session.query(Kline).filter(Kline.type == o.st_code).order_by(Kline.id.desc()).limit(self.__sell_wind).all()
            if not  kls:
                raise ValueError("{} not find in db".format(o.st_code))
            min_close = 100000000
            for kl in kls:
                if kl.close < min_close:
                    min_close = kl.close
            if _zt_price(o.st_code,kls[0].close) >= min_close:
                continue
            sell_list.append((o,min_close,kls[0].close))
            sell_code_list.append(o.st_code)
        #获取当前价格比较
        if sell_code_list:
            today_kl_infos = get_today_kline(sell_code_list)
            cur_tm_str = datetime.datetime.now().strftime(TM_FORMAT)
            for oinfo in sell_list:
                o = oinfo[0]
                sell_price = oinfo[1]
                yst_price = oinfo[2]
                if not today_kl_infos or not today_kl_infos.get(o.st_code):
                    logger.error("[hand_sell] less st today kl sell_code={}".format(o.st_code))
                    continue
                if today_kl_infos[o.st_code]['close'] < sell_price:
                    #执行卖出
                    ret = o.sell(yst_price,today_kl_infos[o.st_code]['close'],cur_tm_str)




