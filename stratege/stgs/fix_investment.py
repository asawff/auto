from stratege.type_define import StgUnit
from utils.public import *

class FixInvestment(StgUnit):
    def __init__(self,gscc,sim,vail):
        StgUnit.__init__(self,gscc,sim,vail)
        self.cnt = 0

    def run(self):
        if self.vail == False:
            return

        cur_tm = self.gscc.cur_tm

        if std_pd_tm(cur_tm,"1min") == std_pd_tm(cur_tm,"1week")+24*3600*2:
            self.gscc.create_order(0,1)
            self.cnt += 1
            print("FixInvestment num:%d  usdt:%.3f"%(self.cnt,self.gscc.cur_equal_usdt))