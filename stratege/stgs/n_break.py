from stratege.type_define import StgUnit
from utils.public import *

N = 2
K = 1
LK = 0.03
class NBreak_1Day(StgUnit):
    def __init__(self,gscc,sim,vail):
        StgUnit.__init__(self,gscc,sim,vail)
        self.range = 0
        self.open = 0

    def run(self):
        if self.vail == False: return
        dc = self.gscc.dc
        cur_price = self.gscc.cur_price
        cur_tm = self.gscc.cur_tm

        if self.stat == 0:
            if std_pd_tm(cur_tm, '1min') == std_pd_tm(cur_tm, "1day"):
                self.range = 0
                HHs = dc.kline_h("1day",N)
                cls = dc.kline("1day",N)
                LLs = dc.kline_l("1day",N)
                HH = max(HHs)
                HC = max(cls)
                LC = min(cls)
                LL = min(LLs)

                self.range = max(HH - LC, HC - LL)
                self.open = cls[-1]

            if self.range != 0:
                ma_60 = dc.ma("1day",60,1)
                ma_20 = dc.ma("1day",20,1)
                if cur_price > self.open + K*self.range   and (ma_20 > ma_60):
                    print("[Debug n_break] [many] tm:%s cur_price:%.3f open:%.3f range:%.3f"%(sjc2localtm(cur_tm),cur_price,self.open,self.range))
                    self.k = LK
                    self.o = self.gscc.create_order(0,1)
                    self.stat = 2
                    self.buy_price = self.o.create_price
                if cur_price < self.open - K*self.range   and (ma_20 < ma_60):
                    print("[Debug n_break] [empty] tm:%s cur_price:%.3f open:%.3f range:%.3f" % (
                    sjc2localtm(cur_tm), cur_price, self.open, self.range))
                    self.k = LK
                    self.stat = 1
                    self.o = self.gscc.create_order(1,1)
                    self.buy_price = self.o.create_price

        # 多单处理逻辑,stat = 2,4,6
        elif self.stat == 2:
            cnd2 = cur_price > self.buy_price * (1 + 3 * self.k)
            cnd3 = cur_price < self.buy_price * (1 - self.k)
            if cnd2 or cnd3:
                self.o = self.gscc.delete_order(self.o)
                self.range = 0
                self.stat = 0
            elif cur_price > self.buy_price * (1 + 2 * self.k):
                self.stat = 6
            elif cur_price > self.buy_price * (1 + 1 * self.k):
                self.stat = 4

        elif self.stat == 4:
            cnd1 = cur_price > self.buy_price * (1 + 3 * self.k)
            cnd2 = cur_price < self.buy_price * 1.002
            if cnd1 or cnd2:
                self.o = self.gscc.delete_order(self.o)
                self.range = 0
                self.stat = 0
            elif cur_price > self.buy_price * (1 + 2 * self.k):
                self.stat = 6

        elif self.stat == 6:
            cnd1 = cur_price > self.buy_price * (1 + 3 * self.k)
            cnd2 = cur_price < self.buy_price * (1 + 1 * self.k)
            if cnd1 or cnd2:
                self.o = self.gscc.delete_order(self.o)
                self.range = 0
                self.stat = 0

        # 空单处理逻辑 stat = 1 3 5
        elif self.stat == 1:
            cnd2 = cur_price > self.buy_price * (1 + self.k)
            cnd3 = cur_price < self.buy_price * (1 - 3 * self.k)
            if cnd2 or cnd3:
                self.o = self.gscc.delete_order(self.o)
                self.range = 0
                self.stat = 0
            elif cur_price < self.buy_price * (1 - 2 * self.k):
                self.stat = 5
            elif cur_price < self.buy_price * (1 - 1 * self.k):
                self.stat = 3

        elif self.stat == 3:
            cnd1 = cur_price < self.buy_price * (1 - 3 * self.k)
            cnd2 = cur_price > self.buy_price * 0.998
            if cnd1 or cnd2:
                self.o = self.gscc.delete_order(self.o)
                self.range = 0
                self.stat = 0
            elif cur_price < self.buy_price * (1 - 2 * self.k):
                self.stat = 5

        elif self.stat == 5:
            cnd1 = cur_price < self.buy_price * (1 - 3 * self.k)
            cnd2 = cur_price > self.buy_price * (1 - 1 * self.k)
            if cnd1 or cnd2:
                self.o = self.gscc.delete_order(self.o)
                self.range = 0
                self.stat = 0
