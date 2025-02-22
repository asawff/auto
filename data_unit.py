# -*- coding: utf-8 -*-
from utils.public import *
from utils.stock_index import *
from utils.influx_db import InfluxClient
from utils.ok_swap import api

# 线性插值
def line_fill_value(x,y,interval):
    # type:(list,list,int) -> np.array
    if (x[-1]-x[0])%interval != 0:
        raise ValueError("line_fill_value mod not eq 0 x[0]={} x[-1]={} interval={}".format(x[0],x[-1],interval))
    should_num = int((x[-1]-x[0])/interval)+1
    cur_num = len(x)
    if cur_num >= should_num:
        return y
    ret = np.zeros(should_num)
    j = 0
    hole_st = 0
    hole_ed = 0
    for i in range(0,should_num):
        cur_x = i*interval + x[0]
        if cur_x == x[j]:
            ret[i] = y[j]
            j += 1
            if hole_ed != 0:
                less_num = hole_ed - hole_st
                step = 1.0*(ret[i] - ret[hole_st])/(less_num+1)
                for ii in range(hole_st+1,i):
                    ret[ii] = ret[ii-1]+step
                hole_ed = 0
            hole_st = i
        else:
            hole_ed = i
    return ret


class DataCenter:
    def __init__(self,
                 periods,   # ['1min','60min',...]
                 type,      # 'htusdt'
                 sim,       # True False
                 st="",     # '2019-10-29 00:00:00' or 1572278400
                 ed="",     # '2019-10-29 00:00:00' or 1572278400
                 pre_d_len = 60,
                 logger = None,
                 ):
        if logger:
            self.__log_info = logger.info
            self.__log_error = logger.error
        else:
            from utils.log_config import log_error, log_info
            self.__log_info = log_info
            self.__log_error = log_error
        # time
        if sim:
            if isinstance(st, str): st = localtm2sjc(st)
            if isinstance(ed, str) : ed = localtm2sjc(ed)
            self.__ed = ed
            self.sys_cur_tm = std_pd_tm(st, periods[0])
        else:
            self.sys_cur_tm = int(time.time())
            self.__last_commit_id = {}  # 当前系统中已经提交固化的最后kl id
            self.__kline_fetch_mgr = api.get_klines
        self.sys_st_tm = self.sys_cur_tm
        self.type = type
        self.sim = sim
        self.__periods = sorted(periods,key=lambda x:pd2int[x])
        self.__pre_d_len = pre_d_len
        self.__kline = {}
        self.__kline_h = {}
        self.__kline_l = {}
        self.__kline_o = {}
        self.__kline_am = {}
        self.__ori_kline = {}
        self.__ma = {}
        self.__boll = {}
        self.__rsi = {}

        for period in periods:
            self.__kline[period] = np.array([])
            self.__kline_h[period] = np.array([])
            self.__kline_l[period] = np.array([])
            self.__kline_o[period] = np.array([])
            self.__kline_am[period] = np.array([])
            self.__ori_kline[period] = np.array([])

            #初始化Kline
            if self.sim:
                d_st_tm = std_pd_tm(self.sys_st_tm, period) - self.__pre_d_len * pd2int[period]
                d_ed_tm = std_pd_tm(ed, period)
                db = InfluxClient(db_name='mydb',logger=logger)
                _,res,_ = db.query_series('Kline',['time','open','high','low','close','amount'],filters={'t_type':self.type,'period':period},st_timestamp=d_st_tm,ed_timestamp=d_ed_tm)
                need_num = (d_ed_tm - d_st_tm)/pd2int[period]
                if len(res) < 0.9*need_num:
                    print("init DataCenter,kline less 0.9 ! [t_type]=%s [period]=%s [need_num]=%s [real_num]=%s"%(
                        self.type,period,need_num,len(res)
                    ))
                    exit(-1)
                if res[0][0] != d_st_tm or res[-1][0] != d_ed_tm - pd2int[period]:
                    print("init DataCenter,less terminal! [t_type]=%s [period]=%s"%(self.type,period))
                    exit(-1)
                res = np.array(res)
                tm = res[:, 0]
                cl_o = res[:, 1]
                cl_h = res[:, 2]
                cl_l = res[:, 3]
                cl =   res[:, 4]
                amount = res[:,5]
                self.__kline[period] = line_fill_value(tm,cl,pd2int[period])
                self.__kline_o[period] = line_fill_value(tm,cl_o,pd2int[period])
                self.__kline_h[period] = line_fill_value(tm,cl_h,pd2int[period])
                self.__kline_l[period] = line_fill_value(tm,cl_l,pd2int[period])
                self.__kline_am[period] = line_fill_value(tm,amount,pd2int[period])
            else:
                self.__init_no_sim(period)
                
            #初始化指标
            if period != '1min':
                self.__ma[period] = MaCenter(self.__kline[period])
                self.__boll[period] = BOLL(self.__kline[period])
                self.__rsi[period] = RSI(self.__kline[period])
        self.__log_info("[datacenter] init succ type:%s"%(type))


    #获取下一个数据
    def next(self):
        """
        :return: cur_price,cur_time
        """
        if self.sim:
            self.sys_cur_tm += pd2int[self.__periods[0]]
            if self.sys_cur_tm > std_pd_tm(self.__ed,self.__periods[0]):
                print("sim terminated")
                self.sys_cur_tm -= pd2int[self.__periods[0]]
                return -1,-1
            cur_tm = self.sys_cur_tm
            idx = int((std_pd_tm(cur_tm,self.__periods[0])-std_pd_tm(self.sys_st_tm,self.__periods[0]))/pd2int[self.__periods[0]]) + self.__pre_d_len - 1
            cur_price = self.__kline[self.__periods[0]][idx]
        else:
            ori_klines,cur_tm,_ = self.__kline_fetch_mgr.get_klines(self.type,self.__periods[0],50)
            cur_price = ori_klines[-1]["close"]
            self.__update_no_sim(cur_tm,ori_klines)
        return cur_price,cur_tm

    #获取过去历史kline
    def kline(self,period,d_len = -1):
        ed_idx = int((std_pd_tm(self.sys_cur_tm,period) - std_pd_tm(self.sys_st_tm,period)) / pd2int[period]) + self.__pre_d_len
        if d_len > 0:
            st_idx = max(0,ed_idx-d_len)
        else:
            st_idx = self.__pre_d_len
        return self.__kline[period][st_idx:ed_idx]

    def kline_h(self,period,d_len = -1):
        ed_idx = int((std_pd_tm(self.sys_cur_tm,period) - std_pd_tm(self.sys_st_tm,period)) / pd2int[period]) + self.__pre_d_len
        if d_len > 0:
            st_idx = max(0,ed_idx-d_len)
        else:
            st_idx = self.__pre_d_len
        return self.__kline_h[period][st_idx:ed_idx]

    def kline_l(self,period,d_len = -1):
        ed_idx = int((std_pd_tm(self.sys_cur_tm,period) - std_pd_tm(self.sys_st_tm,period)) / pd2int[period]) + self.__pre_d_len
        if d_len > 0:
            st_idx = max(0,ed_idx-d_len)
        else:
            st_idx = self.__pre_d_len
        return self.__kline_l[period][st_idx:ed_idx]

    def kline_o(self,period,d_len = -1):
        ed_idx = int((std_pd_tm(self.sys_cur_tm,period) - std_pd_tm(self.sys_st_tm,period)) / pd2int[period]) + self.__pre_d_len
        if d_len > 0:
            st_idx = max(0,ed_idx-d_len)
        else:
            st_idx = self.__pre_d_len
        return self.__kline_o[period][st_idx:ed_idx]

    #获取过去历史滑动均值
    def ma(self,period,N,d_len = -1):
        ed_idx = int((std_pd_tm(self.sys_cur_tm, period) - std_pd_tm(self.sys_st_tm, period)) / pd2int[period]) + self.__pre_d_len
        if d_len > 0:
            st_idx = max(0, ed_idx - d_len)
        else:
            st_idx = self.__pre_d_len
        return self.__ma[period].get_ma(N,st_idx,ed_idx)

    #获取过去历史boll线 返回 上轨,中线,下轨
    def boll(self,period,d_len = -1):
        ed_idx = int((std_pd_tm(self.sys_cur_tm, period) - std_pd_tm(self.sys_st_tm, period)) / pd2int[
            period]) + self.__pre_d_len
        if d_len > 0:
            st_idx = max(0, ed_idx - d_len)
        else:
            st_idx = self.__pre_d_len
        return self.__boll[period].up[st_idx:ed_idx],self.__boll[period].md[st_idx:ed_idx],self.__boll[period].dn[st_idx:ed_idx]

    def rsi(self,period):
        # type: (self, str) -> RSI
        return self.__rsi.get(period)

    # 唯一更新 __last_commit_id ,sys_cur_tm, kline ,index
    def __update_no_sim(self,cur_tm,update_klines):
        tBeg = int(time.time() * 1000)
        self.__log_info("__update_no_sim tm:%s" % (sjc2localtm(cur_tm)))
        for period in self.__periods:
            if std_pd_tm(cur_tm, period) - pd2int[period] > self.__last_commit_id[period]:
                need_num = int((std_pd_tm(cur_tm, period) - self.__last_commit_id[period]) / pd2int[period] - 1)
                if need_num > 0:
                    ori_klines = []
                    if need_num != 1:
                        self.__log_error("__update_no_sim period:%s leek updata need_num:%d"%(period,need_num))
                    if period == self.__periods[0]:
                        ori_klines = update_klines
                    else:
                        pre_period = self.__periods[self.__periods.index(period)-1]
                        rate = int(pd2int[period]/pd2int[pre_period])
                        need_pre_kline_num = int(need_num * rate)
                        # eg: 在16:01更新4h 需要 15:00 1h的数据
                        if self.__last_commit_id[pre_period] < std_pd_tm(cur_tm, period)-pd2int[pre_period]:
                            self.__log_error("__update_no_sim Fatal Error cur_period:%s per_period:%s pre_commit_id:%s need:%s"%(
                                period, pre_period, self.__last_commit_id[pre_period], std_pd_tm(cur_tm, period)-pd2int[period]
                            ))
                            raise ValueError("__update_no_sim Fatal")
                        pre_idx_ed = len(self.__ori_kline[pre_period])
                        pre_back_commit_id = self.__last_commit_id[pre_period]
                        while pre_idx_ed > 0 and pre_back_commit_id != std_pd_tm(cur_tm, period)-pd2int[pre_period]:
                            pre_idx_ed -= 1
                            pre_back_commit_id -= pd2int[pre_period]
                        per_idx_st = pre_idx_ed - need_pre_kline_num
                        if per_idx_st < 0:
                            self.__log_error("__update_no_sim Fatal Error cur_period:%s pre_period:%s need_pre_kline_num:%d"%(
                                period,pre_period,need_pre_kline_num
                            ))
                            raise ValueError("__update_no_sim Fatal")
                        pre_klines = self.__ori_kline[pre_period][per_idx_st:pre_idx_ed]
                        for i in range(0,need_num):
                            kl = {}
                            kl["id"] = pre_klines[i*rate]["id"]
                            kl["open"] = pre_klines[i*rate]["open"]
                            kl["close"] = pre_klines[(i+1)*rate - 1]["close"]
                            kl["high"] = pre_klines[i*rate]["high"]
                            for j in range(1,rate):
                                kl["high"] = max(kl["high"],pre_klines[i*rate+j]["high"])
                            kl["low"] = pre_klines[i * rate]["low"]
                            for j in range(1, rate):
                                kl["low"] = min(kl["low"], pre_klines[i * rate + j]["low"])
                            kl["amount"] = 0
                            for j in range(0, rate):
                                kl["amount"] += pre_klines[i * rate + j]["amount"]
                            ori_klines.append(kl)
                        self.__log_info("__update_no_sim generate from pre_klines period:%s ori_klines:%s"%(period,ori_klines))
                    while len(ori_klines) > 0 and ori_klines[-1]["id"] >= std_pd_tm(cur_tm, period):
                        del ori_klines[-1]
                    while len(ori_klines) > 0 and ori_klines[0]["id"] <= self.__last_commit_id[period]:
                        del ori_klines[0]
                    if len(ori_klines) == 0:
                        self.__log_error("__update_no_sim fatal error ori_klines become empty")
                    if len(ori_klines) > 0:
                        self.__update_index(ori_klines, period)
                        self.__last_commit_id[period] = max(self.__last_commit_id[period], ori_klines[-1]["id"])
        self.sys_cur_tm = cur_tm
        self.__log_info("__update_no_sim use_tm: %dms" % (int(time.time() * 1000) - tBeg))

    #不依赖sys_cur_tm,依赖__last_commit_id
    def __update_index(self,ori_klines,period):
        for kl in ori_klines:
            if kl["id"] <= self.__last_commit_id[period]:
                continue
            cl = kl["close"]
            cl_o = kl["open"]
            cl_h = kl["high"]
            cl_l = kl["low"]
            amount = kl["amount"]
            self.__kline[period] = np.append(self.__kline[period],cl)
            self.__kline_o[period] = np.append(self.__kline_o[period],cl_o)
            self.__kline_h[period] = np.append(self.__kline_h[period],cl_h)
            self.__kline_l[period] = np.append(self.__kline_l[period],cl_l)
            self.__kline_am[period] = np.append(self.__kline_am[period],amount)
            self.__ori_kline[period] = np.append(self.__ori_kline[period],kl)
            if period == "1min": continue
            self.__ma[period].update(cl)
            self.__boll[period].next(cl,True)
            self.__rsi[period].next(cl,True)

    def __init_no_sim(self,period):
        tBeg = int(time.time())
        self.__last_commit_id[period] = 0
        fetch_len = self.__pre_d_len + 10
        self.__log_info("[__init_no_sim] t_type:%s period:%s begin ..."%(self.type,period))
        klines,cur_tm,_ = self.__kline_fetch_mgr.get_klines(self.type,period,fetch_len)
        self.__log_info("[__init_no_sim] kline resp fetch_len:%d values:%s"%(len(klines),str(klines)))
        while len(klines)>0 and klines[-1]["id"] >= std_pd_tm(self.sys_cur_tm,period):
            del klines[-1]
        self.__log_info("[__init_no_sim] filter rest cur_tm:%d std_tm:%d num:%d"%(self.sys_cur_tm,std_pd_tm(self.sys_cur_tm,period),len(klines)))
        new_len = len(klines)
        for kline in klines[new_len-self.__pre_d_len:new_len]:
            self.__kline[period] = np.append(self.__kline[period],float(kline["close"]))
            self.__kline_h[period] = np.append(self.__kline_h[period],float(kline["high"]))
            self.__kline_l[period] = np.append(self.__kline_l[period],float(kline["low"]))
            self.__kline_o[period] = np.append(self.__kline_o[period],float(kline["open"]))
            self.__kline_am[period] = np.append(self.__kline_am[period],float(kline["amount"]))
            self.__ori_kline[period] = np.append(self.__ori_kline[period],kline)
        self.__last_commit_id[period] = klines[-1]["id"]
        self.__log_info("[__init_no_sim] timeuse:%d"%(int(time.time())-tBeg))

    def d_info(self,query):
        print("[http] query:%s"%(str(query)))
        if "kline" in query.keys():
            period = query["kline"]
            res = {}
            res["kline"] = self.__ori_kline[period].tolist()
            res["last_commit_id"] = self.__last_commit_id[period]
            res["sys_cur_tm"] = self.sys_cur_tm
            res["sys_st_tm"] = self.sys_st_tm
            res["d_len"] = len(res["kline"])
            return res
        elif "ma" in query.keys():
            period = query["ma"]
            d_len = int(query["len"])
            N = int(query["N"])
            res = {}
            res["ma"] = self.ma(period,N,d_len).tolist()
            res["last_update_id"] = self.__last_commit_id[period]
            res["sys_cur_tm"] = self.sys_cur_tm
            return res
        elif "rsi" in query.keys():
            period = query["rsi"]
            exp = query.get("exp")
            res = {}
            res["rsi"] = self.rsi(period).val[-1]
            if exp:
                res["exp_price"] = self.rsi(period).inverse(float(exp))
            return res