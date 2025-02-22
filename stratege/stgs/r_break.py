from stratege.type_define import StgUnit
from utils.public import *

Ratio = 0.04
class RBreak(StgUnit):
    def __init__(self,gscc,sim,vail):
        StgUnit.__init__(self,gscc,sim,vail)
        self.up_1 = 0
        self.up_2 = 0
        self.low_1 = 0
        self.low_2 = 0
        self.o = None

    def run(self):
        if self.vail == False:
            return

        dc = self.gscc.dc
        cur_price = self.gscc.cur_price
        cur_tm = self.gscc.cur_tm



        #没有单
        if self.stat == 0:

            if std_pd_tm(cur_tm) == std_pd_tm(cur_tm, "1day"):
                cl_h = dc.kline_h("1day", 1)
                cl_l = dc.kline_l("1day", 1)
                step = (cl_h - cl_l) / 10
                self.up_1 = cl_l + 10 * step
                self.low_1 = cl_l - 0 * step
                self.up_2 = cl_h * (1 + Ratio)
                self.low_2 = cl_l * (1 - Ratio)
                print("[Debug RBreak] tm:%s cl_h:%.2f cl_l:%.2f up2:%.2f up1:%.2f low1:%.2f low2:%.2f" % \
                      (sjc2localtm(cur_tm), cl_h, cl_l, self.up_2, self.up_1, self.low_1, self.low_2))
                # self.stat = 0
                # if type(self.o) != type(None):
                #     self.gscc.delete_order(self.o)
                #     self.o = None

            if cur_price > self.up_1 and cur_price < self.up_2:
                self.o = self.gscc.create_order(1,1)
                self.stat = 1
            elif cur_price < self.low_1 and cur_price > self.low_2:
                self.o = self.gscc.create_order(0,1)
                self.stat = 2

        #持多
        if self.stat == 2:
            if cur_price < self.low_2:
                self.gscc.delete_order(self.o)
                self.o = None
                self.stat = 0
            if cur_price > self.up_1:
                self.gscc.delete_order(self.o)
                if cur_price > self.up_2:
                    self.o = None
                    self.stat = 0
                else:
                    self.o = self.gscc.create_order(1,1)
                    self.stat = 1

        #持空
        if self.stat == 1:
            if cur_price > self.up_2:
                self.gscc.delete_order(self.o)
                self.o = None
                self.stat = 0
            if cur_price < self.low_1:
                self.gscc.delete_order(self.o)
                if cur_price < self.low_2:
                    self.o = None
                    self.stat = 0
                else:
                    self.o = self.gscc.create_order(0,1)
                    self.stat = 2


