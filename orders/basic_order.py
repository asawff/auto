
class BasicOrder:
    """
    订单的基类,不同种类的订单必须有的字段和函数
    o_type: 订单类型,偶数为多单,奇数为空单
        0 : sim多单
        1 : sim空单
        2 : ok usdt永续多单
        3 : ok usdt永续空单
    t_type: 交易的币种类
        btcusdt
        ltcusdt
        ...
    stat: 订单状态
        0 : 成功创建
        1 : 订单结束
    """
    def __init__(self,cur_tm, cur_price, use_usdt,ttype,o_type,extro_info = ""):
        self.fee_rate = 0.005  # 交易手续费
        self.o_type = o_type
        self.t_type = ttype
        self.finish_price = 0
        self.finish_tm = 0
        self.create_tm = cur_tm
        self.create_price = cur_price
        self.init_usdt = use_usdt
        self.stat = 0
        self.extro_info = extro_info

    def get_profit(self,cur_price):
        if self.stat == 1: cur_price = self.finish_price
        r = cur_price/self.create_price
        if self.o_type == 0:
            return self.init_usdt * (r*(1-self.fee_rate)*(1-self.fee_rate) - 1)
        else:
            return self.init_usdt * (1 - r - 2*self.fee_rate + r*self.fee_rate*self.fee_rate)


    def finish_order(self,cur_price,cur_tm,extro_info = ""):
        if self.stat == 0:
            self.finish_price = cur_price
            self.finish_tm = cur_tm
            self.stat = 1
            self.extro_info += " "+extro_info
            return True
        return False


