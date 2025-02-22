from stratege.type_define import StgUnit
from utils.public import *


class SingleMa(StgUnit):
    def __init__(self,gscc,sim,vail):
        StgUnit.__init__(self,gscc,sim,vail)
        self.o = None

    def run(self):
        if self.vail == False:
            return
        time_scale = Cfg["stgs"]["scale"]
        dc = self.gscc.dc
        cur_price = self.gscc.cur_price
        cur_tm = self.gscc.cur_tm

        ma_20 = dc.ma(time_scale,20,1)
        p = dc.kline(time_scale,1)


        if self.stat == 0:
            if p > ma_20:
                self.o = self.gscc.create_order(0,1)
                self.stat = 2

        #多单处理逻辑,stat = 2,4,6
        elif self.stat == 2:
            if p < ma_20:
                self.gscc.delete_order(self.o)
                self.o = None
                self.stat = 0
