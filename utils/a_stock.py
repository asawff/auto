from opendatatools import stock
from utils.log_config import Logger
from utils.mysql_wrapper import DbSession, Kline,update_write_db
from utils.public import *

logger = Logger("a_info.txt","a_wf.txt")
STOCK_DICT = {}
_f = open("./csfile/a_stock_code.csv")
for row in _f.read().split('\n'):
    if not row:continue
    fs = row.split(',')
    STOCK_DICT[fs[0]] = fs[1]
_f.close()


def _trans_kline(df):
    result = []
    d_len = df.shape[0]
    for i in range(0, d_len):
        row = df.iloc[i]
        result.append({
            "id": int(row['time'].value / 1e9),
            "open": float(row['open']),
            "high": float(row['high']),
            "low": float(row['low']),
            "close": float(row['last']),
            "amount": float(row['volume']),
        })
    sorted(result, key=lambda kl: kl["id"])
    return result

def get_day_kline(symbol,st,ed=None):
    """
    :param symbol:  000858.SZ
    :param st:  2020-06-30 or datetime or timestamp
    :param ed:  2020-12-15 or datetime or timestamp
    :return:
    """
    if not ed :
        yesterday = datetime.datetime.now()-datetime.timedelta(days=1)
        ed = yesterday.strftime("%Y-%m-%d")
    if isinstance(st,datetime.datetime):
        st = st.strftime("%Y-%m-%d")
    if isinstance(ed,datetime.datetime):
        ed = ed.strftime("%Y-%m-%d")
    if isinstance(st,int):
        st = sjc2localtm(st,"%Y-%m-%d")
    if isinstance(ed,int):
        ed = sjc2localtm(ed,"%Y-%m-%d")
    try:
        result = []
        df, msg = stock.get_daily(symbol, start_date=st, end_date=ed)
        for kl in _trans_kline(df):
            kl["id"] = std_pd_tm(kl["id"],'1day')
            result.append(kl)
        return result
    except Exception as e:
        logger.error("%s"%(e))
        return None

def get_today_kline(symbols):
    try:
        df,_ = stock.get_quote(','.join(symbols))
        d_len = df.shape[0]
        result = {}
        for i in range(0,d_len):
            row = df.iloc[i]
            result[row['symbol']] = [float(row['open']),float(row['high']),float(row['low']),float(row['last'])]
        return result
    except Exception as e:
        logger.error("%s"%(e))
        return {}

# def get_today_kline(symbol):
#     today = datetime.datetime.now().strftime("%Y-%m-%d")
#     try :
#         df, _ = stock.get_kline(symbol, today, '1m')
#         result = _trans_kline(df)
#         if len(result) > 1:
#             return result[1:]
#         else:
#             return None
#     except Exception as e:
#         logger.error("%s"%(e))
#         return None

#从ed开始获取过去N个交易日的时间戳

def _get_last_N_ids(N,ed = None):
    #type: (int,datetime.datetime) -> list
    _holidays = [
        ['20210211','20210217'],
        ['20210403','20210405'],
        ['20210501','20210505'],
        ['20210501','20210505'],
        ['20210612','20210614'],
        ['20210919','20210921'],
        ['20211001','20211007'],
    ]
    for i in range(0,len(_holidays)):
        _holidays[i] = [datetime.datetime.strptime(_holidays[i][0],"%Y%m%d"),datetime.datetime.strptime(_holidays[i][1],"%Y%m%d")]
    now = datetime.datetime.now()
    if now.hour < 15:
        now -= datetime.timedelta(days=1)
    if not ed or ed > now:
        ed = now
    ed = datetime.datetime.strptime(ed.strftime("%Y%m%d"),"%Y%m%d")
    result = []
    while len(result) < N:
        if ed.isoweekday() in [6,7]:
            ed -= datetime.timedelta(days=1)
            continue
        hit_hol = False
        for hol in _holidays:
            if ed >= hol[0] and ed <= hol[1]:
                hit_hol = True
                break
        if hit_hol:
            ed -= datetime.timedelta(days=1)
            continue
        result.append(int(ed.timestamp()))
        ed -= datetime.timedelta(days=1)
    return sorted(result)

def update_db_stock(st_code,N = 30,st_name=''):
    def _check_less_kline(st_code, N, ed):
        need_ids = _get_last_N_ids(N,ed)
        ed_std_sjc = std_pd_tm(int(ed.timestamp()), '1day')
        session = DbSession()
        res = session.query(Kline).filter(Kline.type == st_code).filter(Kline.id <= ed_std_sjc).order_by(Kline.id.desc()).limit(N).all()
        res_ids = set()
        result = []
        for r in res:
            res_ids.add(r.id)
        for id in need_ids:
            if id not in res_ids:
                result.append(id)
        return result
    if time.timezone != -28800:
        raise EnvironmentError("时区不是uct+8")
    ed = datetime.datetime.now()
    if ed.hour < 15:
        ed -= datetime.timedelta(days=1)
    session = DbSession()
    check_res = _check_less_kline(st_code,N,ed)
    check_res_str = []
    for res in check_res:
        check_res_str.append(sjc2localtm(res,"%Y-%m-%d"))
    logger.info("update_db_kl start hand [code]={} [check_res]={}".format(st_code,check_res_str))
    if not check_res:
        return
    st = check_res[0]
    kls = get_day_kline(st_code,st,ed)
    if not kls:
        logger.error("get_stock_kline error||code=%s||N=%s" % (st_code, N))
        return
    num = 0
    for kl in kls:
        id = kl["id"]
        if id not in check_res: continue
        num += 1
        db_kl = Kline()
        db_kl.id = id
        db_kl.open = kl["open"]
        db_kl.close = kl["close"]
        db_kl.high = kl["high"]
        db_kl.low = kl["low"]
        db_kl.amount = kl["amount"]
        db_kl.type = st_code
        db_kl.period = "1day"
        db_kl.commit = "{}|{}".format(sjc2localtm(db_kl.id,"%Y-%m-%d"),st_name)
        session.add(db_kl)
    update_write_db(session)
    logger.info("update_db_kl finish hand [code]={} [num]={}".format(st_code,num))


def update_db_kl(N = 30):
    for st_code in STOCK_DICT:
        logger.info("update "+st_code)
        update_db_stock(st_code,N,STOCK_DICT[st_code])