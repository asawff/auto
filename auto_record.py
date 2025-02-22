from utils.hb_currency import  HbCurrency
from utils.public import std_pd_tm,pd2int,localtm2sjc,sjc2localtm
from utils.influx_db import InfluxClient
from utils.log_config import Logger
import time

logger = Logger(info_name='kl_mgr.info',wf_name='kl_mgr.wf')
log_info = logger.info
log_error = logger.error
db = InfluxClient('mydb',logger=logger)
hbcli = HbCurrency(logger=logger)

def update(t_type,period,st_time=None,ed_time=None):
    def _write_kl_db(klines,tags,cur_tm_std):
        for kl in klines:
            if kl["id"] >= cur_tm_std: continue
            kl_tm = kl["id"]
            kl.pop("id")
            db.add_point("Kline",kl,kl_tm,tags)

    if isinstance(st_time,str):
        st_timestamp = localtm2sjc(st_time)
    else:
        st_timestamp = st_time or 0
    if isinstance(ed_time,str):
        ed_timestamp = localtm2sjc(ed_time)
    else:
        ed_timestamp = ed_time or 0
    cur_tm = int(time.time())
    cur_tm_std = std_pd_tm(cur_tm,period)
    if ed_timestamp == 0 or ed_timestamp > cur_tm:
        ed_timestamp = cur_tm
    if not st_timestamp:
        lbs,datas,err = db.get_latest_points('Kline',1,filters={'t_type':t_type,'period':period})
        if err:
            print("_update_kline read db err={}".format(err))
            log_error("_update_kline read db err={}".format(err))
            return
        if datas:
            st_timestamp = datas[0][0] + pd2int[period]
    if not st_timestamp:
        st_timestamp = cur_tm - 365*86400
    st_timestamp = std_pd_tm(st_timestamp,period)
    ed_timestamp = std_pd_tm(ed_timestamp,period)
    nsize = int((cur_tm_std - st_timestamp)/pd2int[period])
    if nsize + 2 <= 2000:
        klines,_,err = hbcli.get_klines(t_type,period,nsize+2)
        if err:
            print("_update_kline get kline err={}".format(err))
            log_error("_update_kline get kline err={}".format(err))
            return
        _write_kl_db(klines,{"t_type":t_type,"period":period},cur_tm_std)
    else:
        sti = st_timestamp
        while sti < ed_timestamp:
            if period in ['1day','4hour']:
                edi = ed_timestamp
            elif period == '60min':
                edi = min(sti + 40*86400,ed_timestamp)
            else:
                edi = min(sti + 10*86400,ed_timestamp)
            klines,_,err = hbcli.get_klines(t_type,period,from_tms=sti,to_tms=edi)
            if err:
                print("_update_kline get kline err={}".format(err))
                log_error("_update_kline get kline err={}".format(err))
                return
            _write_kl_db(klines, {"t_type": t_type, "period": period}, cur_tm_std)
            st_i_str = sjc2localtm(sti)
            ed_i_str = sjc2localtm(edi)
            exp_num = int((edi-sti)/pd2int[period])
            get_num = len(klines)
            print("record kline st:%s ed:%s excep_num :%d get_num:%d succ_rate:%.3f" % (
                st_i_str[0:10], ed_i_str[0:10], exp_num, get_num, get_num / exp_num))
            sti = edi


def export(t_type=None,period=None,st_time=0,ed_time=0):
    if isinstance(st_time,str):
        st_timestamp = localtm2sjc(st_time)
    else:
        st_timestamp = st_time
    if isinstance(ed_time,str):
        ed_timestamp = localtm2sjc(ed_time)
    else:
        ed_timestamp = ed_time
    filters = {}
    if t_type:
        filters['t_type'] = t_type
    if period:
        filters['period'] = period
    fname = 'kl_{}_{}_{}_{}.csv'.format(t_type,period,sjc2localtm(st_timestamp)[0:10],sjc2localtm(ed_timestamp)[0:10])
    x,y,err = db.query_series('Kline',['time','t_type','period','open','high','low','close','amount'],filters=filters,st_timestamp=st_timestamp,ed_timestamp=ed_timestamp)
    if err:
        print(err)
        return
    f = open(fname,'w+')
    for r in y:
        try:
            f.write("%d,%s,%s,%.5f,%.5f,%.5f,%.5f,%.5f\n"%(r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7]))
        except Exception as e:
            print(e)
            print(r)
            break
    f.close()

def f_import(fname):
    f = open(fname)
    dts = f.read().split('\n')
    f.close()
    print('total {}'.format(len(dts)))
    hand = 0
    for d in dts:
        fs = d.split(',')
        _ = db.add_point('Kline',fields={
            'open':float(fs[3]),
            'high':float(fs[4]),
            'low':float(fs[5]),
            'close':float(fs[6]),
            'amount':float(fs[7]),
        },timestamp=int(fs[0]),tags={
            't_type':fs[1],
            'period':fs[2],
        })
        hand += 1
        if hand % 50 == 0:
            print(hand)

def check(t_type,period):
    _,res,_ = db.query_series('Kline',filters={'t_type':t_type,'period':period})
    if not res:
        print('None Data')
        return
    st = res[0][0]
    ed = res[-1][0]
    less_num = (ed - st)/pd2int[period]+1-len(res)
    print('total:{} less:{} st:{} ed:{}'.format(len(res),less_num,sjc2localtm(res[0][0]),sjc2localtm(res[-1][0])))
    if less_num:
        print('=== less datas ===')
        i = 0
        cur = st
        less = []
        while cur <= ed:
            if cur == res[i][0]:
                if less:
                    print('[{} - {}] len:{}'.format(less[0], less[-1], len(less)))
                    less = []
                i += 1
            else:
                less.append('{}'.format(sjc2localtm(cur)))
            cur += pd2int[period]
        if less:
            print('[{} - {}] len:{}'.format(less[0], less[-1], len(less)))


def auto_record(t_tps=None,pds=None):
    log_info('auto_record begin...')
    tBeg = int(time.time()*1000)
    if not t_tps:
        t_tps = ['btcusdt','ethusdt']
    if not pds:
        pds = ['1day','4hour','60min']
    for t_type in t_tps:
        for period in pds:
            log_info('auto_record update {}:{}'.format(t_type,period))
            update(t_type,period)
    log_info('auto_record end use_time:{}'.format(int(time.time()*1000)-tBeg))

if __name__ == '__main__':
    auto_record()
    while True:
        time.sleep(2467)
        auto_record()