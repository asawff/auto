from stratege.stratege_unit import StrategeMgr
from orders.ok_swap import OKOrder
from orders.basic_order import BasicOrder
from utils.log_config import log_info
from utils.public import *
import json

#全局状态控制中心
class GSCC :
    global Cfg
    def __init__(self,dc):
        self.stg_mgr =  StrategeMgr(self,dc.sim)
        self.dc = dc
        self.cur_orders = []
        self.dead_orders = []
        self.his_profit = 0
        self.cur_profit = 0
        self.profit_rec = []
        self.cur_tm = 0
        self.cur_price = 0
        self.rec_cnt = 0

    def create_order(self,o_type,use_usdt,extro_info = ""):
        print("Create Order tm:%s cur_price:%.2f o_type:%d"%(sjc2localtm(self.cur_tm),self.cur_price,o_type))
        log_info("Create Order tm:%s cur_price:%.2f o_type:%d"%(sjc2localtm(self.cur_tm),self.cur_price,o_type))

        # 创建sim订单
        if o_type == 0 or o_type == 1:
            o = BasicOrder(self.cur_tm,self.cur_price,use_usdt,self.dc.type,o_type,extro_info)
        # 创建okex usdt-swap订单
        elif o_type == 2 or o_type == 3:
            o = OKOrder(self.cur_tm,use_usdt,self.dc.type,o_type,extro_info)
            # o_type_msg = "多"
            # if o_type == 3: o_type_msg = "空"
            # msg = "[开%s] type:%s usdt:%.2f price:%.2f extro_info:%s tm:%s" % \
            #       (o_type_msg, self.dc.type[0:3], o.init_usdt, o.create_price, extro_info, sjc2localtm(self.cur_tm))
            # msg_handler.asyn_send(msg)

        self.cur_orders.append(o)
        return o

    def delete_order(self,o,extro_info = ""):
        print("Del Order tm:%s cur_price:%.2f"%(sjc2localtm(self.cur_tm),self.cur_price))
        log_info("Del Order tm:%s cur_price:%.2f"%(sjc2localtm(self.cur_tm),self.cur_price))
        o.finish_order(self.cur_price, self.cur_tm, extro_info)
        # if o.o_type == 2 or o.o_type == 3:
        #     o_type_msg = "多"
        #     if o.o_type == 3: o_type_msg = "空"
        #     msg = "[平%s] type:%s profit:%.2f price:%.2f extro_info:%s tm:%s"% \
        #           (o_type_msg,self.dc.type[0:3],o.get_profit(0),o.finish_price,extro_info, sjc2localtm(self.cur_tm))
        #     seng_msg(msg)

        self.his_profit += o.get_profit(self.cur_price)
        self.dead_orders.append(o)
        del self.cur_orders[self.cur_orders.index(o)]

    def run(self):
        self.cur_price, self.cur_tm = self.dc.next()
        if self.cur_price < 0:
            return
        self.stg_mgr.run()
        self.cur_profit = self.his_profit
        for o in self.cur_orders:
            self.cur_profit += o.get_profit(self.cur_price)
        log_info("gscc||cur_profit=%.2f"%(self.cur_profit))
        if self.dc.sim:
            self.profit_rec.append(self.cur_profit)

    def save(self):
        log_info("[gscc] start save...")
        tBeg = int(time.time()*1000)
        with open(Cfg[self.dc.type]["save_file"],"w+") as f:
            save_msg = {}
            save_msg["his_profit"] = self.his_profit
            save_msg["rec_cnt"] = self.rec_cnt
            save_msg["stgs"] = {}
            for stg in self.stg_mgr.stgs:
                stg_name = str(type(stg)).split(".")[-1][0:-2]
                save_msg["stgs"][stg_name] = stg.dump_json()
            json.dump(save_msg,f)
        log_info("[gscc] save succ time:%d"%(int(time.time()*1000)-tBeg))

    def load(self):
        with open(Cfg[self.dc.type]["save_file"], "r") as f:
            save_msg = json.load(f)
            self.his_profit = save_msg["his_profit"]
            self.rec_cnt = save_msg["rec_cnt"]
            for stg in self.stg_mgr.stgs:
                stg_name = str(type(stg)).split(".")[-1][0:-2]
                olist = stg.load_json(save_msg["stgs"][stg_name])
                for o in olist:
                    self.cur_orders.append(o)