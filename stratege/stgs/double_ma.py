from stratege.type_define import StgUnit
from orders.ok_swap import OKOrder
from utils.log_config import log_error,log_info
from utils.public import *
from utils.stock_index import NhasM

class DoubleMA(StgUnit):
    def __init__(self,gscc,sim,vail):
        StgUnit.__init__(self,gscc,sim,vail)
        self.o = None
        self.tm_cnt = 0

    def run(self):
        if self.vail == False:return

        time_scale = Cfg["stgs"]["scale"]
        log_info("[DM][%d] begin cycle..."%(self.tm_cnt))
        dc = self.gscc.dc
        cur_tm = self.gscc.cur_tm
        cur_price = self.gscc.cur_price

        #保证每 TIME_SCALE(>5min) 分钟后面的代码只被执行一次
        std_tm = std_pd_tm(cur_tm, time_scale)
        std_tm_5min = std_pd_tm(cur_tm,"5min")
        if std_tm != std_tm_5min:
            log_info("[DM] return because std_tm_5min:%d std_scale:%d"%(std_tm_5min,std_tm))
            return
        base_tm = localtm2sjc("2000-01-01 00:00:00")
        if int((std_tm-base_tm)/pd2int[time_scale]) <= self.tm_cnt:
            log_info("[DM] return because current tm has executed cur_tm_cnt:%d self_tm_cnt:%d"%(int((std_tm-base_tm)/pd2int[time_scale]),self.tm_cnt))
            return
        # 说明中间至少有一个 TIME_SCALE 的时间没有执行!!
        if self.tm_cnt != 0 and int((std_tm-base_tm)/pd2int[time_scale]) > self.tm_cnt+1:
            log_error("[DM] fatal error leak exec less num:%d"%(int((std_tm-base_tm)/pd2int[time_scale]) - self.tm_cnt-1))
        self.tm_cnt = int((std_tm-base_tm)/pd2int[time_scale])


        cl = dc.kline(time_scale,2)
        ma7 = dc.ma(time_scale,5,2)
        ma30 = dc.ma(time_scale,20,2)
        loss = 0.1


        #开多单条件
        cnd1 = ma7[0] < ma30[0] and ma7[1] > ma30[1]
        cnd2 = cur_price > ma7[1] and cur_price < ma30[1] and ma30[1]/ma7[1] < 1.05 and (ma7[1]>ma7[0] or cl[1]>cl[0])
        cnd3 = cur_price > ma7[1] and cur_price > ma30[1] and cur_price/min(ma7[1],ma30[1]) < 1.05
        cond_buy_duo = cnd1# or cnd2 or cnd3

        log_info("[buy duo] cnd1:%s cnd2:%s cnd3:%s"%(cnd1,cnd2,cnd3))
        msg_buy_duo = "[%d%d%d]"%(cnd1,cnd2,cnd3)

        #卖出多单条件
        # 1.价格有效跌破30日均线
        # 2.ma7跌破ma30
        # 3.ma7即将跌破ma30
        # 4.止损
        # 5.盈利超过50%
        N = 1
        M = 1
        __cnd1_cl = dc.kline(time_scale,N)
        __cnd1_ma = dc.ma(time_scale,30,N)
        op_lt = lambda x,y:x<y
        cnd1 = NhasM(__cnd1_cl, __cnd1_ma, op_lt, N, M)
        cnd2 = ma7[0] > ma30[0] and ma7[1] < ma30[1]
        cnd3 = NhasM(cl,ma7,op_lt,2,2) and ma7[1]/ma30[1]<1.02 and (ma7[1] - ma7[0]) < 0
        cnd4 = self.stat == 2 and cur_price/self.o.create_price < (1-loss)
        cnd5 = self.stat == 2 and cur_price / self.o.create_price > 1.5
        cond_sell_duo = cnd2# or cnd2 or cnd3 or cnd4 or cnd5
        log_info("[sell duo] cnd1:%s cnd2:%s cnd3:%s cnd4:%s cnd5:%s" % (cnd1, cnd2, cnd3, cnd4,cnd5))
        msg_sell_duo = "[%d%d%d%d%d]" % (cnd1, cnd2,cnd3,cnd4,cnd5)

        if cond_buy_duo and cond_sell_duo:
            cond_buy_duo = False
            cond_sell_duo = False

        #开空单条件
        cnd1 = ma7[0] > ma30[0] and ma7[1] < ma30[1]
        cnd2 = cur_price < ma7[1] and cur_price > ma30[1] and ma30[1]/ma7[1] > 0.95 and (cl[1]<cl[0] or ma7[1]<ma7[0])
        cnd3 = cur_price < ma7[1] and cur_price < ma30[1] and cur_price / max(ma7[1],ma30[1]) > 0.95
        cond_buy_kong = cnd1# or cnd2 or cnd3
        log_info("[buy kong] cnd1:%s cnd2:%s cnd3:%s" % (cnd1, cnd2,cnd3))
        msg_buy_kong = "[%d%d%d]" % (cnd1, cnd2,cnd3)

        #卖空单条件
        # 1.价格有效突破ma30
        # 2.ma7突破ma30
        # 3.ma7即将突破ma30
        # 4.止损
        # 5.盈利超过25%
        op_gt = lambda x, y: x > y
        cnd1 = NhasM(__cnd1_cl, __cnd1_ma, op_gt, N, M)
        cnd2 = ma7[0] < ma30[0] and ma7[1] > ma30[1]
        cnd3 = NhasM(cl,ma7,op_gt,2,2) and ma7[1]/ma30[1]>0.98 and (ma7[1]-ma7[0])>0
        cnd4 = self.stat == 1 and cur_price/self.o.create_price > (1+loss)
        cnd5 = self.stat == 1 and cur_price/self.o.create_price < 0.75
        cond_sell_kong = cnd2# or cnd2 or cnd3 or cnd4 or cnd5
        log_info("[sell kong] cond cnd1:%s cnd2:%s cnd3:%s cnd4:%s cnd5:%s"%(cnd1,cnd2,cnd3,cnd4,cnd5))
        msg_sell_kong = "[%d%d%d%d%d]" % (cnd1, cnd2,cnd3,cnd4,cnd5)

        if cond_buy_kong and cond_sell_kong:
            cond_sell_kong = False
            cond_buy_kong = False

            
        if self.stat == 0:
            if cond_buy_kong:
                self.o = self.gscc.create_order(self.kong_type,self.use_usdt,msg_buy_kong)
                self.stat = 1
                return
            if cond_buy_duo:
                self.o = self.gscc.create_order(self.duo_type,self.use_usdt,msg_buy_duo)
                self.stat = 2
                return

        elif self.stat == 1:
            if cond_sell_kong:
                self.gscc.delete_order(self.o,msg_sell_kong)
                if cond_buy_duo:
                    self.o = self.gscc.create_order(self.duo_type,self.use_usdt,msg_buy_duo)
                    self.stat = 2
                else:
                    self.o = None
                    self.stat = 0

        elif self.stat == 2:
            if cond_sell_duo:
                self.gscc.delete_order(self.o,msg_sell_duo)
                if cond_buy_kong:
                    self.o = self.gscc.create_order(self.kong_type,self.use_usdt,msg_buy_kong)
                    self.stat = 1
                else:
                    self.o = None
                    self.stat = 0


    def dump_json(self):
        msg = {}
        msg["stat"] = self.stat
        msg["tm_cnt"] = self.tm_cnt
        if self.o and not self.gscc.dc.sim:
            msg["oid"] = self.o.oid
        return msg


    def load_json(self,js):
        self.stat = js["stat"]
        self.tm_cnt = js["tm_cnt"]
        if js.get('oid'):
            oid = js["oid"]
            self.o = OKOrder.load(oid)
            return [self.o]
        return []

