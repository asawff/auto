from data_unit import DataCenter
import threading
from syscntl.gscc import GSCC


from watch_dog import reset_dog
from utils.log_config import *
from utils.http_tool import *
from utils.public import *


import numpy as np
import matplotlib.pyplot as plt
st_tm = '2021-01-01 00:00:00'
ed_tm = '2021-07-25 00:00:00'
sim_period = '1day'
sim_t_type = 'btcusdt'
dc = DataCenter(
    st=st_tm,
    ed=ed_tm,
    periods=[sim_period],
    type=sim_t_type,
    sim=True,
    pre_d_len=60,
)
Cfg["stgs"]["scale"] = sim_period


gscc = GSCC(dc)
while gscc.cur_price >= 0:
    gscc.run()


ods = gscc.dead_orders
duo_order_cnt = 0
profit_duo_order_cnt = 0
duo_income = 0
duo_profit = 0

kong_order_cnt = 0
profit_kong_order_cnt = 0
kong_income = 0
kong_profit = 0

for o in ods:
    if o.o_type %2 == 0:
        duo_order_cnt += 1
        duo_income += o.get_profit(0)
        if o.get_profit(0) > 0:
            profit_duo_order_cnt += 1
            duo_profit += o.get_profit(0)
    else:
        kong_order_cnt += 1
        kong_income += o.get_profit(0)
        if o.get_profit(0) > 0:
            profit_kong_order_cnt += 1
            kong_profit += o.get_profit(0)


print("订单总数量:%d 盈利单数量:%d 总收入:%.2f 多收入:%.2f 空收入:%.2f"%(len(ods),profit_kong_order_cnt+profit_duo_order_cnt,duo_income+kong_income,duo_income,kong_income))
print("多单数量:%d 盈利单数量:%d 总收入:%.2f 盈利单收入:%.2f"%(duo_order_cnt,profit_duo_order_cnt,duo_income,duo_profit))
print("空单数量:%d 盈利单数量:%d 总收入:%.2f 盈利单收入:%.2f"%(kong_order_cnt,profit_kong_order_cnt,kong_income,kong_profit))



fig,axs = plt.subplots(nrows=2,ncols=1)

axs[0].grid(True)
ma7 = dc.ma(sim_period,7)
ma30 = dc.ma(sim_period,30)
axs[0].plot(ma7,'r')
axs[0].plot(ma30,'b')
axs[0].plot(dc.kline(sim_period),'black')

axs[1].grid(True)
axs[1].plot(np.array(gscc.profit_rec)/(max(1,len(gscc.cur_orders))))
plt.show()
exit(0)

'''

dc_btc = DataCenter(
    periods=["5min","60min","1day"],
    type='btcusdt',
    sim=False,
)
#
# dc_ltc = DataCenter(
#     st="",
#     ed="",
#     periods=["5min","60min","4hour","1day"],
#     type='ltcusdt',
#     sim=Cfg["sim"],
# )
#
# dc_eth = DataCenter(
#     st="",
#     ed="",
#     periods=["5min","60min","4hour","1day"],
#     type='ethusdt',
#     sim=Cfg["sim"],
# )
class HttpHandler(HttpBaseHandler):
    regist_handler = {
        "/" :lambda x:{"msg":" debug tool"},
        "/btc":dc_btc.d_info,
    }
start_http_server(HttpHandler,10001)

dcs = [dc_btc]#,dc_eth,dc_ltc]
gsccs = []

for dc in dcs:
    gsccs.append(GSCC(dc))

if Cfg["use_save_init"]:
    for gscc in gsccs:
        gscc.load()

def run_gscc(gscc,log_uuid):
    refresh_log_uuid(log_uuid)
    set_uuid_append(gscc.dc.type[0:3])
    gscc.run()
    gscc.save()

cnt = 1
while True:
    tBeg = int(time.time()*1000)
    log_uuid = refresh_log_uuid()
    log_info("===============Cycle[%d] Begin==========="%(cnt))
    thds = []
    for gscc in gsccs:
        thds.append(threading.Thread(target=run_gscc, args=[gscc,log_uuid]))
    for thd in thds:
        thd.start()
    for thd in thds:
        thd.join()
    cnt += 1
    reset_dog()
    tEnd = int(time.time() * 1000)
    if tEnd - tBeg > 10000:
        msg_handler.asyn_send("[loop time] %dms"%(tEnd - tBeg))
    log_info("Cycle End time:%dms"%(tEnd-tBeg))
    time.sleep(61 - int(tEnd/1000) % 60)  # 每个60s后的第一秒执行

'''