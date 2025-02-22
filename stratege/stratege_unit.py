from stratege.stgs.ma_diffuse import MaDiffuse_1Day
from stratege.stgs.n_break import NBreak_1Day
from stratege.stgs.fix_investment import FixInvestment
from stratege.stgs.single_kline import SingleKline
from stratege.stgs.r_break import RBreak
from stratege.stgs.double_ma import DoubleMA
from stratege.stgs.rsi import RsiHighRateTrade
from stratege.stgs.single_ma import SingleMa


class StrategeMgr:
    """
    所有策略管理的类,依赖DataCenter初始化
    """
    def __init__(self,gscc,is_sim):
        self.stgs = []
        #初始化各种策略,放入stgs
        # self.stgs.append(MaDiffuse_1Day(gscc,is_sim,False))
        # self.stgs.append(NBreak_1Day(gscc,is_sim,False))
        # self.stgs.append(FixInvestment(gscc,is_sim,False))
        # self.stgs.append(SingleKline(gscc,is_sim,False))
        # self.stgs.append(RBreak(gscc,is_sim,False))
        self.stgs.append(DoubleMA(gscc,is_sim,False))
        # self.stgs.append(RsiHighRateTrade(gscc,is_sim,True))
        self.stgs.append(SingleMa(gscc,is_sim,True))

    def run(self):
        for stg in self.stgs:
            stg.run()