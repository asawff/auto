from orders.basic_order import BasicOrder
from utils.ok_swap import take_order,OkOrderOp
from utils.public import *
from utils.log_config import log_error
import json

class OKOrder(BasicOrder):
    def __init__(self,cur_tm = 0, use_usdt = 0,ttype = '',o_type = 0,extro_info = ''):
        BasicOrder.__init__(self,cur_tm, 0, use_usdt,ttype,o_type,extro_info)
        self.fee_rate = 0.0005
        if use_usdt > 0:
            if o_type not in [2,3]:
                return
            op = OkOrderOp.add_many
            if o_type == 3:
                op = OkOrderOp.add_less
            self.init_usdt,self.create_price,oinfo = take_order(ttype,op,use_usdt)
            self.zhang = oinfo.zhang
            self.oid = oinfo.id
            self.save()
        else:
            self.zhang = 0
            self.oid = 0

    def finish_order(self,cur_price,cur_tm,extro_info = ""):
        if super().finish_order(cur_price,cur_tm,extro_info):
            if self.o_type not in [2,3]:
                return
            op = OkOrderOp.dec_many
            if self.o_type == 3:
                op = OkOrderOp.dec_less
            _,self.finish_price,_ = take_order(self.t_type,op,order_amout=self.zhang)
            self.save()

    def get_profit(self,cur_price):
        fee = self.fee_rate
        if self.stat == 1:
            cur_price = self.finish_price
            fee = 0
        if self.o_type  == 2:
            return self.init_usdt * (cur_price/self.create_price - fee-1)
        else:
            return self.init_usdt * (1 - cur_price/self.create_price - fee)

    def save(self):
        fname = Cfg["okorders"]["save_dir"] + str(self.oid) + ".json"
        with open(fname,"w+") as f:
            json.dump(self.__dict__, f)

    @staticmethod
    def load(oid):
        # type:(int) -> OKOrder
        fname = Cfg["okorders"]["save_dir"] + str(oid) + ".json"
        try:
            f = open(fname, 'r')
            json_obj = json.load(f)
            f.close()
        except:
            log_error("[ok_order] load obj from file error fname:%s"%(fname))
        o = OKOrder()
        # ########################
        # {
        #     "fee_rate": 0.0005,
        #     "o_type": 0,
        #     "t_type": "yxtest",
        #     "finish_price": 0,
        #     "finish_tm": 0,
        #     "create_tm": 0,
        #     "create_price": 0,
        #     "init_usdt": 0,
        #     "stat": 0,
        #     "extro_info": "",
        #     "zhang": 0,
        #     "oid": 0
        # }
        # ########################
        o.fee_rate = float(json_obj["fee_rate"])
        o.o_type = int(json_obj["o_type"])
        o.t_type = str(json_obj["t_type"])
        o.create_tm = int(json_obj["create_tm"])
        o.create_price = float(json_obj["create_price"])
        o.finish_tm = int(json_obj["finish_tm"])
        o.finish_price = float(json_obj["finish_price"])
        o.init_usdt = float(json_obj["init_usdt"])
        o.zhang = int(json_obj["zhang"])
        o.oid = int(json_obj["oid"])
        o.extro_info = str(json_obj["extro_info"])
        o.stat = int(json_obj["stat"])
        return o