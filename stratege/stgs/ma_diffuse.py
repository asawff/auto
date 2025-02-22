from stratege.type_define import StgUnit
from utils.public import *

MAGIC_NUM = 0.1  #每一单最大止损比例
MAGIC_NUM_2 = 0.05  #每一单最小止损比例


"""
启发，止损止盈可以加上对均线的判断
这样，可以用均线实时反映市场情况
"""
class MaDiffuse_1Day(StgUnit):
    def __init__(self,gscc,sim,vail):
        StgUnit.__init__(self,gscc,sim,vail)
        self.buy_price = 0
        self.k = 0

    def run(self):
        if self.vail == False:
            return

        dc = self.gscc.dc
        cur_price = self.gscc.cur_price
        cur_tm = self.gscc.cur_tm

        cl = dc.kline("1day",3)
        cl_1d = cl[2]
        ma_1d_5 = dc.ma("1day",5,1)
        ma_1d_10 = dc.ma("1day",10,1)
        ma_1d_20 = dc.ma("1day",20,1)
        ma_1d_30 = dc.ma("1day",30,1)
        ma_1d_45 = dc.ma("1day",45,1)
        ma_1d_60 = dc.ma("1day",60,1)

        cnd_cl_20_ma = cl_1d > ma_1d_20

        if self.stat == 0:
            cnd0 = std_pd_tm(cur_tm,'1min') == std_pd_tm(cur_tm,"1day")
            cnd1 = ma_1d_5 > ma_1d_10 and ma_1d_10 > ma_1d_20 and ma_1d_20 > ma_1d_30 and ma_1d_30> ma_1d_45 and ma_1d_45 > ma_1d_60
            self.k = max(cl_1d/ma_1d_20 -1,MAGIC_NUM_2)
            if cnd0 and cnd1 :
                self.o = self.gscc.create_order(0,1)
                self.buy_price = cur_price
                self.stat = 2
                self.k = min(self.k, MAGIC_NUM)
                return

            cnd1 = cl_1d  < ma_1d_5 and cl_1d < ma_1d_10 and cl_1d < ma_1d_60 and False
            self.k = max(ma_1d_5/cl_1d -1,MAGIC_NUM_2)
            if cnd0 and cnd1:
                self.o = self.gscc.create_order(1, 1)
                self.buy_price = cur_price
                self.stat = 1
                self.k = min(self.k,MAGIC_NUM)

        #多单处理逻辑,stat = 2,4,6
        elif self.stat == 2:
            cnd2 = cur_price > self.buy_price*(1 + 3*self.k)
            cnd3 = cur_price < self.buy_price*(1 - self.k)
            if cnd2 or cnd3:
                self.o = self.gscc.delete_order(self.o)
                self.stat = 0
            elif cur_price > self.buy_price*(1 + 2*self.k):
                self.stat = 6
            elif cur_price > self.buy_price*(1 + 1*self.k):
                self.stat = 4

        elif self.stat == 4:
            cnd1 = cur_price > self.buy_price*(1 + 3*self.k)
            cnd2 = cur_price < self.buy_price*1.002
            if cnd1 or cnd2:
                self.o = self.gscc.delete_order(self.o)
                self.stat = 0
            elif cur_price > self.buy_price*(1 + 2*self.k):
                self.stat = 6

        elif self.stat == 6:
            cnd1 = cur_price > self.buy_price*(1 + 3*self.k)
            cnd2 = cur_price < self.buy_price*(1 + 1*self.k)
            if cnd1 or cnd2:
                self.o = self.gscc.delete_order(self.o)
                self.stat = 0

        #空单处理逻辑 stat = 1 3
        elif self.stat == 1:
            cnd2 = cur_price > self.buy_price*(1 + self.k)
            cnd3 = cur_price < self.buy_price*(1 - 2*self.k)
            if cnd2 or cnd3:
                self.o = self.gscc.delete_order(self.o)
                self.stat = 0
            elif cur_price < self.buy_price*(1 - 1*self.k):
                self.stat = 3

        elif self.stat == 3:
            cnd1 = cur_price < self.buy_price * (1 - 2 * self.k)
            cnd2 = cur_price > self.buy_price*0.998
            if cnd1 or cnd2:
                self.o = self.gscc.delete_order(self.o)
                self.stat = 0




