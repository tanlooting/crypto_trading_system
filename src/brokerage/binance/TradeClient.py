from binance.client import Client
from dateutil.relativedelta import relativedelta
import datetime
import pandas as pd
import time
from src.events import EventType, Exchange, TickEvent, OrderEvent
from src.events_engine import EventEngine

INTERVAL = {
    60 : "1m",
    180 : "3m",
    300 : "5m",
    900 : "15m",
    1800 : "30m",
    3600 : "1h",
    7200 : "2h",
    14400 : "4h",
    21600 : "6h",
    28800 : "8h",
    43200 : "12h",
    86400 : "1d",
    259200 : "3d",
    604800: "1w"
}


class TradeClient:
    """Wrapper functions that interact with Luno API
    For all underlying functions, please refer to: https://github.com/luno/luno-python/blob/master/luno_python/client.py for further details

    1. capital
    2. positions
    3. submit orders
    4. get candlestick & ticker data
    5. get orderbook
    """

    def __init__(
        self,
        mkt_event_engine: EventEngine,
        action_event_engine: EventEngine,
    ):
        self.client = Client()
        self._mkt_queue = mkt_event_engine
        self._action_queue = action_event_engine

    def get_account_details(self):
        pass

    def get_account_summary(self):
        pass

    def get_account_capital(self) -> int:
        pass

    def get_markets_info(self):
        pass

    def get_account_trades(self, pair):
        pass

    def get_account_orders(self):
        pass

    # def get_ohlcv(self, pair: str, count: int, granularity: int) -> pd.DataFrame:
    #     """
    #     Granularity (in seconds) - 60 for 1m bars

    #     Ref:
    #     https://www.luno.com/en/developers/api#tag/Market/operation/GetCandles
    #     https://github.com/luno/luno-python/blob/master/luno_python/client.py#L134
    #     """
    #     if granularity not in ALL_VALID_GRANULARITY:
    #         raise NotImplementedError(
    #             "Selected granularity not supported in luno_python API"
    #         )

    #     try:
    #         # duration, pair, since

    #         period = count * granularity
    #         since = int(
    #             datetime.datetime.timestamp(
    #                 datetime.datetime.now() - relativedelta(seconds=period)
    #             )
    #             * 1000
    #         )  # convert to ms
    #         print(
    #             int(datetime.datetime.timestamp(datetime.datetime.now()) * 1000), since
    #         )
    #         ohlcv_dict = self.client.get_candles(granularity, pair, since)["candles"]
    #         ohlcv = pd.DataFrame(ohlcv_dict)
    #         ohlcv.columns = ["date", "open", "close", "high", "low", "volume"]
    #         ohlcv["date"] = pd.to_datetime(ohlcv["date"], unit="ms")
    #         # ohlcv['date'] = ohlcv['date'].apply(lambda x: self.format_date(x))
    #         return ohlcv
    #     except Exception as e:
    #         print(e)

    def get_historical_ohlc_data(instrument: str ,start: str, end: str, granularity: int = 3600
    ) -> pd.DataFrame:
        # start_ts = tcb.format_date(start)
        # end_ts = tcb.format_date(end)

        """Returns historcal klines from past for given symbol and interval
        past_days: how many days back one wants to download the data"""

        if granularity not in INTERVAL.keys():
            raise NotImplementedError(
                "Selected granularity not supported in python-binance API"
            )
        # start_str=str((pd.to_datetime('today')-pd.Timedelta(str(past_days)+' days')).date())

        numeric_columns = ["open", "close", "high", "low", "volume"]
        res=pd.DataFrame(client.get_historical_klines(symbol=instrument, start_str = start, interval=INTERVAL[granularity]))
        res.columns=['date','open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol','is_best_match']
        res['date']=[dt.datetime.fromtimestamp(x/1000) for x in res["date"]]
        res = res[res["date"] < pd.to_datetime("2023-05-05")]
        # print(pd.to_datetime(end, unit="ms"))
        res = res.drop_duplicates(subset = ["date"])
        res['symbol']=instrument
        res[numeric_columns] = res[numeric_columns].apply(
            pd.to_numeric, errors="coerce")
        res = res.reset_index(drop=True)
        return res[["date"] + numeric_columns]

    # def get_ticker(self, pair: str) -> dict:
    #     ticker = self.client.get_ticker(pair=pair)
    #     ticker["timestamp"] = int(ticker["timestamp"])
    #     ticker["ask"] = float(ticker["ask"])
    #     ticker["bid"] = float(ticker["bid"])
    #     # ticker["last_trade"] = float(ticker["last_trade"])
    #     # ticker["rolling_24_hour_volume"] = float(ticker["rolling_24_hour_volume"])
    #     tick_event = TickEvent(
    #         sym=pair,
    #         exchange=Exchange.LUNO,
    #         code=f"{str(pair)}.{Exchange.LUNO.value}",
    #         timestamp=ticker["timestamp"],
    #         bid_p=ticker["bid"],
    #         ask_p=ticker["ask"],
    #     )
    #     self._mkt_queue.put(tick_event)
    #     return tick_event

    # def get_L2(self, pair: str) -> dict:
    #     # returns top 100 only. use get_full_L2 to get complete orderbook or use streaming API instead.
    #     return self.client.get_order_book(pair=pair)

    # def get_full_L2(self, pair: str) -> dict:
    #     # get full orderbook - use streaming API as alternative
    #     return self.client.get_order_book_full(pair=pair)

    # def place_limit_order(
    #     self,
    #     pair: str,
    #     price: float,
    #     type: str,  # BID or ASK only for buy/sell order respectively
    #     volume: float,
    #     base_account_id=None,
    #     client_order_id=None,
    #     counter_account_id=None,
    #     post_only: bool = True,
    #     stop_direction=None,
    #     stop_price=None,  # for stop limit
    #     timestamp=None,
    #     ttl=None,
    # ):

    #     self.client.post_limit_order(
    #         pair=pair,
    #         price=price,
    #         type=type,
    #         volume=volume,
    #         base_account_id=base_account_id,
    #         client_order_id=client_order_id,
    #         counter_account_id=counter_account_id,
    #         post_only=post_only,
    #         stop_direction=stop_direction,
    #         stop_price=stop_price,
    #         timestamp=timestamp,
    #         ttl=ttl,
    #     )

    # def place_market_order(
    #     self,
    #     pair: str,
    #     type: str,  # direction BID/ASK
    #     base_account_id=None,
    #     base_volume=None,
    #     client_order_id=None,
    #     counter_account_id=None,
    #     counter_volume=None,  # how much MYR to use to BTC in the BTC/MYR
    #     timestamp=None,
    #     ttl=None,
    # ):
    #     self.client.post_market_order(
    #         pair,
    #         type,
    #         base_account_id,
    #         base_volume,
    #         client_order_id,
    #         counter_account_id,
    #         counter_volume,
    #         timestamp,
    #         ttl,
    #     )

    # def generate_order_id(self):
    #     """generate a valid unique Client Order Id for posting orders"""
    #     pass

    # def get_order(self, order_id) -> dict:
    #     return self.client.get_order_v3(client_order_id=order_id)

    # def get_order_status(self, order_id) -> str:
    #     """
    #     order status includes "AWAITING", "PENDING", "COMPLETE"
    #     """
    #     return self.get_order(order_id)["state"]

    # def cancel_order(self, order_id):
    #     self.client.stop_order(order_id=order_id)

    # def get_fee_info(self, pair: str) -> dict:
    #     return self.client.get_fee_info(pair=pair)

    @staticmethod
    def format_date(date: str):
        """Format date into timestamp in ms
        date format has to be "YYYY-MM-DD"
        """
        yymmdd = date.split("-")
        if len(yymmdd) != 3:
            raise ValueError("Incorrect date format provided. Please use YYYY-MM-DD")
        dt = datetime.datetime(int(yymmdd[0]), int(yymmdd[1]), int(yymmdd[2]))
        return int(datetime.datetime.timestamp(dt) * 1000)
