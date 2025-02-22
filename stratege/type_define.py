from utils.public import Cfg
class StgUnit :
    """
    所有单个策略的父类,提供了统一的必要接口
    """
    def __init__(self,gscc,sim = True,vail = True):
        self.gscc = gscc
        self.stat = 0
        self.vail = vail
        self.sim = sim
        if sim:
            self.duo_type = Cfg["simorders"]["duo_type"]
            self.kong_type = Cfg["simorders"]["kong_type"]
            self.use_usdt = Cfg["simorders"]["use_usdt"]
        else:
            self.duo_type = Cfg["okorders"]["duo_type"]
            self.kong_type = Cfg["okorders"]["kong_type"]
            self.use_usdt = Cfg["okorders"]["use_usdt"]

    def run(self):
        ""

    #返回一个json对象
    def dump_json(self):
        return {"stat":self.stat}

    #返回当前使用的order list
    def load_json(self,js):
        self.stat = js["stat"]
        return []

