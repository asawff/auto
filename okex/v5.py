from .client import Client
from .consts import *


ok_period_dict = {
    '1min':'1m',
    '5min':'5m',
    '60min':'1H',
    '4hour':'4H',
    '1day':'1D'
}

class Swap(Client):
    def __init__(self, api_key, api_seceret_key, passphrase, use_server_time=True):
        Client.__init__(self, api_key, api_seceret_key, passphrase, use_server_time)

    def take_order(self, instrument_id, size, dir,pos_side,order_type,price=None):
        params = {
            'instId': instrument_id,
            'tdMode':'cross', #全仓
            'side':dir, # 订单方向 buy：买 sell：卖

            # 持仓方向，单向持仓模式下此参数非必填，如果填写仅可以选择net；
            # 在双向持仓模式下必填，且仅可选择 long（多）或 short（空）
            'posSide':pos_side,
            'sz': str(size),

            # market：市价单
            # limit：限价单
            # post_only：只做maker单
            # fok：全部成交或立即取消
            # ioc：立即成交并取消剩余
            # optimal_limit_ioc：市价委托立即成交并取消剩余（仅适用交割、永续）
            'ordType':order_type,
        }
        if price:
            params['px'] = price  #可选	委托价格，仅适用于限价单
        return self._request_with_params(POST, '/api/v5/trade/order', params)

    def cancel_order(self,instrument_id,order_id):
        params = {
            'instId': instrument_id,
            'ordId':str(order_id)
        }
        return self._request_with_params(POST,'/api/v5/trade/cancel-order',params)

    def order_info(self,instrument_id,order_id):
        params = {
            'instId': instrument_id,
            'ordId':str(order_id)
        }

        # instType	String	产品类型
            # SPOT：币币
            # MARGIN：币币杠杆
            # SWAP：永续合约
            # FUTURES：交割合约
            # OPTION：期权
        # instId	String	产品ID
        # ccy	String	保证金币种，仅适用于单币种保证金模式下的全仓币币杠杆订单
        # ordId	String	订单ID
        # clOrdId	String	客户自定义订单ID
        # tag	String	订单标签
        # px	String	委托价格
        # sz	String	委托数量
        # pnl	String	收益
        # ordType	String	订单类型
            # market：市价单
            # limit：限价单
            # post_only：只做maker单
            # fok：全部成交或立即取消
            # ioc：立即成交并取消剩余
            # optimal_limit_ioc：市价委托立即成交并取消剩余（仅适用交割、永续）
        # side	String	订单方向
        # posSide	String	持仓方向
        # tdMode	String	交易模式
        # accFillSz	String	累计成交数量
        # fillPx	String	最新成交价格
        # tradeId	String	最新成交ID
        # fillSz	String	最新成交数量
        # fillTime	String	最新成交时间
        # avgPx	String	成交均价
        # state	String	订单状态
            # canceled：撤单成功
            # live：等待成交
            # partially_filled：部分成交
            # filled：完全成交
        # lever	String	杠杆倍数，0.01到125之间的数值，仅适用于 币币杠杆/交割/永续
        # tpTriggerPx	String	止盈触发价
        # tpOrdPx	String	止盈委托价
        # slTriggerPx	String	止损触发价
        # slOrdPx	String	止损委托价
        # feeCcy	String	交易手续费币种
        # fee	String	订单交易手续费，平台向用户收取的交易手续费，手续费扣除为负数。如： -0.01
        # rebateCcy	String	返佣金币种
        # rebate	String	返佣金额，平台向达到指定lv交易等级的用户支付的挂单奖励（返佣），如果没有返佣金，该字段为“”。手续费返佣为正数，如：0.01
        # category	String	订单种类
            # normal：普通委托
            # twap：TWAP自动换币
            # adl：ADL自动减仓
            # full_liquidation：强制平仓
            # partial_liquidation：强制减仓
            # delivery：交割
        # uTime	String	订单状态更新时间，Unix时间戳的毫秒数格式，如：1597026383085
        # cTime	String	订单创建时间，Unix时间戳的毫秒数格式， 如 ：1597026383085
        return self._request_with_params(GET,'/api/v5/trade/order',params)

    def get_pending_orders(self):
        params = {
            'instType':'SWAP',
        }
        return self._request_with_params(GET,'/api/v5/trade/orders-pending',params)


    def get_current_orders(self):
        params = {
            'instType': 'SWAP',
        }
        return self._request_with_params(GET, '/api/v5/account/positions', params)

    def get_klines(self,t_type,period='1min',size=None):
        t_type = t_type.upper()
        if 'BTC' in t_type:
            t_type = 'BTC-USDT-SWAP'
        elif 'ETH' in t_type:
            t_type = 'ETH-USDT-SWAP'
        else:
            raise ValueError("t_type:%s not support"%(t_type))
        period = ok_period_dict[period]
        params = {
            'instId':t_type,
            'bar':period
        }
        if size:
            params['limit'] = str(size)
        resp = self._request_with_params(GET,'/api/v5/market/mark-price-candles',params)
        if not resp or resp.get('code') != '0':
            return None,None,"get kline error [resp]={}".format(resp)
        ret = []
        for kl in resp['data']:
            ret.append({
                'id':int(int(kl[0])/1000),
                'open':float(kl[1]),
                'high':float(kl[2]),
                'low':float(kl[3]),
                'close':float(kl[4]),
                'amount':0,
            })
        ret = sorted(ret,key=lambda x:x['id'])
        return ret,ret[-1]['id'],None