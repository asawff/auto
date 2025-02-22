from stratege.type_define import StgUnit
from utils.public import *

MAGIC_NUM = 1  #每一单最大止损比例

class SingleKline(StgUnit):
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

        ma_1d_20 = dc.ma("1day",20,1)
        cl_1h = dc.kline("60min",1)
        cl_1h_o = dc.kline_o("60min",1)
        cl_1d = dc.kline("1day",1)
        bl_ups,bl_mds,_ = dc.boll("60min",2)
        bl_up = bl_ups[0]
        bl_md = bl_mds[0]

        if self.stat == 0:
            cnd0 = std_pd_tm(cur_tm,'1min') == std_pd_tm(cur_tm,"60min")
            cnd1 = (cl_1h/cl_1h_o-1) > MAGIC_NUM*(bl_up/bl_md-1)
            cnd2 = cl_1d > ma_1d_20
            if cnd0 and cnd1 and cnd2:
                self.o = self.gscc.create_order(0,1)
                self.buy_price = cur_price
                self.stat = 2
                self.k = cl_1h/cl_1h_o-1
                return

            cnd1 = (cl_1h_o/cl_1h-1) > MAGIC_NUM*(bl_up/bl_md-1)
            cnd2 = cl_1d < ma_1d_20
            if cnd0 and cnd1 and cnd2:
                self.o = self.gscc.create_order(1, 1)
                self.buy_price = cur_price
                self.stat = 1
                self.k = cl_1h_o/cl_1h-1

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

        #空单处理逻辑 stat = 1 3 5
        elif self.stat == 1:
            cnd2 = cur_price > self.buy_price*(1 + self.k)
            cnd3 = cur_price < self.buy_price*(1 - 3*self.k)
            if cnd2 or cnd3:
                self.o = self.gscc.delete_order(self.o)
                self.stat = 0
            elif cur_price < self.buy_price*(1 - 2*self.k):
                self.stat = 5
            elif cur_price < self.buy_price*(1 - 1*self.k):
                self.stat = 3

        elif self.stat == 3:
            cnd1 = cur_price < self.buy_price * (1 - 3 * self.k)
            cnd2 = cur_price > self.buy_price*0.998
            if cnd1 or cnd2:
                self.o = self.gscc.delete_order(self.o)
                self.stat = 0
            elif cur_price < self.buy_price*(1 - 2*self.k):
                self.stat = 5

        elif self.stat == 5:
            cnd1 = cur_price < self.buy_price * (1 - 3 * self.k)
            cnd2 = cur_price > self.buy_price * (1 - 1*self.k)
            if cnd1 or cnd2:
                self.o = self.gscc.delete_order(self.o)
                self.stat = 0



