import numpy as np
import time
class MA:
    """
    普通滑动窗口均值
    """
    def __init__(self,cln,N):
        """
        :param cln: 用于计算均值的数组
        :param N: 滑动窗口的长度,注意cln中前N-1个数据,直接计算从开头元素到当前位置的均值
        """
        self.__N = N
        self.__wind = np.zeros(N)
        self.__wind_pos = 0
        self.val = np.zeros(len(cln))
        for i in range(0,len(cln)):
            desc_val = self.__wind[self.__wind_pos]
            n = min(i,N)
            self.val[i] = (1.0*self.val[i-1]*n - desc_val +cln[i])/min(i+1,N)
            self.__wind[self.__wind_pos] = cln[i]
            self.__wind_pos = (self.__wind_pos + 1) % self.__N

    def next(self,cl,update=False):
        """
        :param cl:     当前时刻的价格
        :param update: 是否将当前时刻记录到历史数据
        :return:       包含当前时刻的均值
        """
        desc_val = self.__wind[self.__wind_pos]
        n = min(len(self.val),self.__N)
        val_n = (1.0*self.val[-1]*n - desc_val + cl)/min(n+1,self.__N)
        if update:
            self.__wind[self.__wind_pos] = cl
            self.__wind_pos = (self.__wind_pos + 1) % self.__N
            self.val = np.append(self.val,val_n)
        return val_n

    def __getitem__(self, item):
        return self.val[item]

    def __len__(self):
        return len(self.val)

class MaCenter:
    def __init__(self,cln,Ns = list([3,5,7,10,20,30,45,60,120,240])):
        self.__Ns = Ns
        self.__mas = []
        for N in self.__Ns:
            self.__mas.append(MA(cln,N))

    def update(self,cl):
        for ma in self.__mas:
            ma.next(cl,True)

    def get_ma(self,N,st,ed):
        """
        fn : 返回指定级别的均线数据
        :param N:  均线的级别 5、20 、60 ...
        :param st:
        :param ed:
        :return: [st:ed) 这段K线区间的滑动均值
        """
        ma = self.__mas[self.__Ns.index(N)]
        if st < N-1 or st >= ed or ed>len(ma):
            raise ValueError("get_ma st:%d ed:%d len(ma):%d"%(st,ed,len(ma)))
        return ma[st:ed]

    def size(self,N):
        if N not in self.__Ns:
            return -1
        l = len(self.__mas[self.__Ns.index(N)])
        if l < N-1:
            return -1
        return l-N+1

def cal_ema(cln,n):
    res = np.zeros(len(cln))
    res[0] = cln[0]
    for i in range(1,len(cln)):
        res[i] = 1.0*res[i-1]*(n-1)/(n+1) + 2.0*cln[i]/(n+1)
    return res
def cal_ema_next(p,c,n):
    return 1.0*p*(n-1)/(n+1) + 2.0*c/(n+1)

class MACD:
    def __init__(self,cln,S=14,L=26,M=9):
        self.__S = S
        self.__L = L
        self.__M = M
        self.__fast = cal_ema(cln,S)
        self.__slow = cal_ema(cln,L)
        self.dif = self.__fast-self.__slow
        self.dea = cal_ema(self.dif,M)

    def next(self,cl,update = False):
        fast_n = cal_ema_next(self.__fast[-1],cl,self.__S)
        slow_n = cal_ema_next(self.__slow[-1],cl,self.__L)
        dif_n = fast_n-slow_n
        dea_n = cal_ema_next(self.dea[-1],dif_n,self.__M)
        if update:
            self.__fast = np.append(self.__fast,fast_n)
            self.__slow = np.append(self.__slow,slow_n)
            self.dif = np.append(self.dif,dif_n)
            self.dea = np.append(self.dea,dea_n)
        return dif_n,dea_n

class BOLL:
    """
    布林线
    """
    def __init__(self,cls,N=20,k=2):
        tBeg = int(time.time()*1000)
        self.__N = N
        self.__k = k
        self.__wind = np.zeros(N)
        self.__wind_pos = 0
        self.__sum_1 = 0
        self.__sum_2 = 0
        self.md = np.array([])
        self.up = np.array([])
        self.dn = np.array([])
        for i in range(0,len(cls)):
            self.__sum_1 += cls[i] - self.__wind[self.__wind_pos]
            self.__sum_2 += cls[i]**2 - self.__wind[self.__wind_pos]**2
            self.__wind[self.__wind_pos] = cls[i]
            self.__wind_pos = (self.__wind_pos+1)%self.__N
            md = self.__sum_1/self.__N
            std = ((self.__sum_2/self.__N)-md**2)**0.5
            self.md = np.append(self.md,md)
            self.up = np.append(self.up,md+self.__k*std)
            self.dn = np.append(self.dn,md-self.__k*std)
        print("boll len:%d cost:%dms"%(len(cls),time.time()*1000-tBeg))
    def next(self,cl,update = False):
        sum_1 = self.__sum_1 + cl - self.__wind[self.__wind_pos]
        sum_2 = self.__sum_2 + cl**2 - self.__wind[self.__wind_pos]**2
        md = sum_1 / self.__N
        std = ((sum_2 / self.__N) - md ** 2) ** 0.5
        if update:
            self.__sum_1 = sum_1
            self.__sum_2 = sum_2
            self.md = np.append(self.md, md)
            self.up = np.append(self.up, md + self.__k * std)
            self.dn = np.append(self.dn, md - self.__k * std)
        return md + self.__k * std, md, md - self.__k * std
        
class BIAS:
    """
    乖离率
    """
    def __init__(self,cls,N):
        self.__ma = MA(cls,N)
        self.val = cls/self.__ma.val

    def next(self,cl,update=False):
        ma = self.__ma.next(cl,update)
        ret = cl/ma
        if update:
            self.val = np.append(self.val,ret)
        return ret

class ROC:
    """
    变动率指标(PriceRateofChange)
    """
    def __init__(self,cls,N):
        self.__cls = cls
        self.__N = N
        self.val = np.zeros(len(cls))
        for i in range(0,len(cls)):
            if i>=N:
                self.val[i] = (cls[i] - cls[i - N]) / cls[i - N]
    def next(self,cl,update=False):
        if len(self.__cls) < self.__N:
            ret = 0
        else:
            ret = (cl-self.__cls[len(self.__cls)-self.__N])/self.__cls[len(self.__cls)-self.__N]
        if update:
            self.__cls = np.append(self.__cls,cl)
            self.val = np.append(self.val,ret)
        return ret

class RSI:
    """
    RSI指标计算 https://en.wikipedia.org/wiki/Relative_strength_index
    """
    def __init__(self,cln,N=14):
        if len(cln) < N:
            raise ValueError("RSI len(cln):%d less N:%d"%(len(cln),N))
        self.__N = N
        self.val = np.zeros(len(cln))
        self.__up_smma = 0
        self.__down_smma = 0
        self.__last_cl = cln[-1]
        for i in range(1,len(cln)):
            self.__up_smma *= 1.0*(N-1)/N
            self.__down_smma *= 1.0*(N-1)/N
            if cln[i] >= cln[i-1]:
                self.__up_smma += 1.0/N*(cln[i]-cln[i-1])
            else:
                self.__down_smma += 1.0/N*(cln[i-1]-cln[i])
            self.val[i] = self.__up_smma/(self.__up_smma+self.__down_smma)

    def next(self,cl,update=False):
        N = self.__N
        up_smma = self.__up_smma * 1.0*(N-1)/N
        down_smma = self.__down_smma * 1.0*(N-1)/N
        if cl >= self.__last_cl:
            up_smma += 1.0/N*(cl-self.__last_cl)
        else:
            down_smma += 1.0/N*(self.__last_cl-cl)
        ret = up_smma/(up_smma+down_smma)
        if update:
            self.__last_cl = cl
            self.__up_smma = up_smma
            self.__down_smma = down_smma
            self.val = np.append(self.val,ret)
        return ret

    def inverse(self,rsi_exp):
        N = self.__N
        up_smma = self.__up_smma * 1.0 * (N - 1) / N
        down_smma = self.__down_smma * 1.0 * (N - 1) / N
        rsi = up_smma/(up_smma+down_smma)
        if rsi_exp >= rsi:
            return self.__last_cl + N*(rsi_exp*down_smma/(1-rsi_exp)-up_smma)
        else:
            return self.__last_cl - N*(up_smma/rsi_exp-up_smma-down_smma)


def current_ma(cls,N,i):
    """
    计算一个数组,中间某个位置的均值,无状态
    :param cls: 原始数据
    :param N:  滑动窗口长度
    :param i:
    :return: 返回第i个位置的均值
    """
    if i>=len(cls):
        print("[ERROR] current_ma len cls:%d idx:%d"%(len(cls),i))
        return
    if i<N-1:
        return np.mean(cls[0:i+1])
    else:
        return np.mean(cls[i-N+1:i+1])

def current_move_std(cls,N,i):
    """
    计算一个数组,中间某个位置滑动样本标准差与滑动均值的比值,无状态函数
    :param cls: 原始数据
    :param N: 滑动窗口长度
    :param i:
    :return: 返回第i个位置 滑动样本标准差/滑动均值 的值
    """
    if i>=len(cls):
        print("[ERROR] current_move_std len cls:%d idx:%d"%(len(cls),i))
        return
    if i<1:
        return 0
    elif i<N-1:
        return np.std(cls[0:i+1],ddof=1)/current_ma(cls,N,i)
    else:
        return np.std(cls[i-N+1:i+1],ddof=1)/current_ma(cls,N,i)


class Histogram:
    """
    直方图工具
    """
    def __init__(self,cls):
        self.bst = min(cls)
        self.bed = max(cls)+0.001
        self.step = (self.bed-self.bst)/100
        #print("[Debug Histogram] bst:%.3f bed:%.3f step:%.3f"%(self.bst,self.bed,self.step))
        self.bucket = np.zeros(100).astype(int)
        for cl in cls:
            idx = int((cl-self.bst)/self.step)
            self.bucket[idx] += 1

        self.bucket_sum = np.zeros(100)

        for i in range(0,100):
            self.bucket_sum[i] = self.bucket[i]+self.bucket_sum[i-1]
        if len(cls) != self.bucket_sum[-1]:
            print("Fatal error in cal Histogram")
            exit(-1)
        self.bucket_sum = self.bucket_sum/len(cls)

    def get_value_by_ratio(self,ratio):
        if ratio <= 0:
            return self.bst
        elif ratio >= 1:
            return self.bed
        idx = -1
        ret = 0
        while idx+1<100 and ratio >= self.bucket_sum[idx+1]:
            idx += 1
        if idx == -1:
            ret =  self.bst + ratio/self.bucket_sum[0] * self.step
        elif idx == 99:
            ret =  self.bed
        else:
            ret =  self.bst + (idx + (ratio-self.bucket_sum[idx])/self.bucket[idx+1])*self.step
        #print("[Debug Histogram] get_value_by_ratio ratio:%.2f idx:%d ret:%.3f" % (ratio, idx, ret))
        return ret


    def get_ratio_by_value(self,value):
        if value < self.bst:
            return 0
        if value > self.bed:
            return 1
        idx = int((value-self.bst)/self.step)
        if idx > 0:
            ret = self.bucket_sum[idx-1]
            value_rst = value - (self.bst + idx*self.step)
            ret += self.bucket[idx] * value_rst/self.step
        else:
            ret =self.bucket[0] * value/self.step
        #print("[Debug Histogram] get_ratio_by_value idx:%d buk1:%.3f buk2:%.3f"%(idx,self.bucket_sum[idx],self.bucket_sum[idx-1]))
        return ret


# N个数据中,有M满足条件
def NhasM(a1,a2,op,N,M):
    cnt = 0
    for i in range(0,N):
        if op(a1[i],a2[i]):
            cnt += 1
    return cnt >= M

class DealDistribution:
    """
    成交量/额 价格分布
    self.__cur_res 某个价格区间上的累计成交量/额
    self.x  价格区间
    self.val 记录每个kl上计算的self.__cur_res快照
    self.val_x 记录每个kl上计算的self.x快照
    """
    def __init__(self, kls, N=1200 ,use_exp=False,use_vol=False,st=0,ed=0,accuracy=1000):
        """
        :param kls: 原始kline 格式:[ {'open':1.0,'high':2.0,'low':0.5,'close':1,'amount':33}, ... ]
        :param N:  当用指数衰减时,衰减的周期. 只在use_exp = True 下参数有意义
        :param use_exp: 是否启用指数衰减
        :param use_vol: 计算成交额/成交量
        :param st: 指定价格区间的启始
        :param ed: 指定价格区间的终止
        :param accuracy: 划分最小价格区间的个数
        """
        self.__st = st or min(kls,key=lambda x:x['low'])['low']
        self.__ed = ed or max(kls,key=lambda x:x['high'])['high']
        self.__cur_ratio = 1.0
        self.__old_ratio = 1.0
        self.__accuracy = accuracy
        self.__use_vol = use_vol
        self.__kls = kls
        self.val = []
        self.val_x = []
        if use_exp:
            self.__cur_ratio = 2.0/(N+1)
            self.__old_ratio = 1.0*(N-1)/(N+1)
        self.x = np.linspace(self.__st, self.__ed, self.__accuracy, endpoint=False)
        self.__step = 1.0*(self.__ed-self.__st)/self.__accuracy
        self.__cur_res = np.zeros(self.__accuracy)
        for i in range(0,len(self.__kls)):
            self.__add_one(self.__kls[i])
            self.val.append(self.__cur_res.copy())
            self.val_x.append(self.x.copy())

    def next(self,kl):
        self.__kls.append(kl)
        if kl['high'] > self.__ed or kl['low'] < self.__st:
            self.__st = min(self.__st,kl['low'])
            self.__ed = max(self.__ed,kl['high'])
            self.x = np.linspace(self.__st, self.__ed, self.__accuracy, endpoint=False)
            self.__step = 1.0 * (self.__ed - self.__st) / self.__accuracy
            self.__cur_res = np.zeros(self.__accuracy)
            for i in range(0,len(self.__kls)):
                self.__add_one(self.__kls[i])
        else:
            self.__add_one(kl)
        self.val_x.append(self.x.copy())
        self.val.append(self.__cur_res.copy())
        return self.x.copy(),self.__cur_res.copy()

    def __add_one(self,kl):
        kl_l = kl['low']
        kl_h = kl['high']
        self.__cur_res *= self.__old_ratio
        amount = kl['amount'] * self.__cur_ratio
        if self.__use_vol:
            amount *= (kl_h+kl_l)/2
        add = amount / ((kl_h - kl_l) / self.__step)
        l_idx = min((kl_l - self.__st) / self.__step, self.__accuracy - 1)
        r_idx = min((kl_h - self.__st) / self.__step, self.__accuracy - 1)
        if int(l_idx) == int(r_idx):
            self.__cur_res[int(l_idx)] += amount
            return
        self.__cur_res[int(l_idx)] += (1 - (l_idx-int(l_idx)))*add
        self.__cur_res[int(r_idx)] += (r_idx - int(r_idx))*add
        for i in range(int(l_idx)+1,int(r_idx)):
            self.__cur_res[i] += add


if __name__ == '__main__':
    import sys
    sys.path.append('./')
    from utils.influx_db import InfluxClient
    from utils.public import *
    import matplotlib.pyplot as plt
    st = localtm2sjc('2021-07-01 00:00:00')
    db = InfluxClient(db_name='mydb')
    keys = ['time','open','high','low','close','amount']
    _,res,_ = db.query_series('Kline',show_fts=keys,filters={'t_type':'btcusdt','period':'60min'},st_timestamp=st)
    kls = []
    for r in res:
        kl = {}
        for i in range(0,len(keys)):
            kl[keys[i]] = r[i]
        kls.append(kl)
    dis = DealDistribution(kls,1200,use_vol=True,use_exp=True,accuracy=5000)
    plt.ion()
    for i in range(0,len(kls)):
        plt.cla()
        y = dis.val[i]
        d_len = len(y)
        while y[d_len-1] == 0:
            d_len -= 1
        ma_y = MA(y[0:d_len],5).val
        plt.plot(dis.x[0:d_len],ma_y,c='b')
        plt.axvline(x=kls[i]['close'],c='r',alpha=1)
        # plt.axvline(x=kls[max(0,i-1)]['close'],c='r',alpha=0.7)
        # plt.axvline(x=kls[max(0,i-2)]['close'],c='indianred',alpha=0.7)
        # plt.axvline(x=kls[max(0,i-3)]['close'],c='indianred',alpha=0.6)
        # plt.axvline(x=kls[max(0,i-4)]['close'],c='tomato',alpha=0.5)
        # plt.axvline(x=kls[max(0,i-5)]['close'],c='lightcoral',alpha=0.4)
        # plt.axvline(x=kls[max(0,i-6)]['close'],c='lightcoral',alpha=0.3)
        # plt.axvline(x=kls[max(0,i-7)]['close'],c='mistyrose',alpha=0.2)
        # plt.axvline(x=kls[max(0,i-8)]['close'],c='mistyrose',alpha=0.1)
        plt.pause(0.0001)
    plt.ioff()
    plt.show()

