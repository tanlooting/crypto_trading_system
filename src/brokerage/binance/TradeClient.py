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

    def get_markets_info(self):
        return self.client.get_exchange_info()

    def get_ohlcv(self, pair: str, granularity: int) -> pd.DataFrame:
        """
        Granularity (in seconds) - 60 for 1m bars

        Ref:
        https://www.luno.com/en/developers/api#tag/Market/operation/GetCandles
        https://github.com/luno/luno-python/blob/master/luno_python/client.py#L134
        """
        if granularity not in list(INTERVAL.keys()):
            raise NotImplementedError(
                "Selected granularity not supported in python-binance API"
            )
        try:
            numeric_columns = ["open", "close", "high", "low", "volume"]
            res = pd.DataFrame(self.client.get_klines(symbol = pair, interval = INTERVAL[granularity]))
            res.columns=['date','open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol','is_best_match']
            res["date"] = pd.to_datetime(res["date"], unit="ms")
            # res = res[res["date"] < pd.to_datetime(end)]
            res = res.drop_duplicates(subset = ["date"])
            res[numeric_columns] = res[numeric_columns].apply(
                pd.to_numeric, errors="coerce")
            res = res.reset_index(drop=True)
            return res[["date"] + numeric_columns]
        except Exception as e:
            print(e)

    def get_historical_ohlcv_data(self, instrument: str ,start: str, end: str, granularity: int = 3600
    ) -> pd.DataFrame:

        """
        Returns historical candlestick data for given symbol and interval
        https://python-binance.readthedocs.io/en/latest/market_data.html#id6 
        """

        if granularity not in list(INTERVAL.keys()):
            raise NotImplementedError(
                "Selected granularity not supported in python-binance API"
            )
        # start_str=str((pd.to_datetime('today')-pd.Timedelta(str(past_days)+' days')).date())

        numeric_columns = ["open", "close", "high", "low", "volume"]
        res=pd.DataFrame(self.client.get_historical_klines(symbol = instrument, 
                                                           start_str = start, 
                                                           interval = INTERVAL[granularity]))
        res.columns=['date','open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol','is_best_match']
        res["date"] = pd.to_datetime(res["date"], unit="ms")
        res = res[res["date"] < pd.to_datetime(end)]
        res = res.drop_duplicates(subset = ["date"])
        res['symbol']=instrument
        res[numeric_columns] = res[numeric_columns].apply(
            pd.to_numeric, errors="coerce")
        res = res.reset_index(drop=True)
        return res[["date"] + numeric_columns]

    def get_ticker(self, pair: str) -> dict:
        ticker = self.client.get_ticker(pair=pair)
        ticker["timestamp"] = int(ticker["timestamp"])
        ticker["ask"] = float(ticker["ask"])
        ticker["bid"] = float(ticker["bid"])
        # ticker["last_trade"] = float(ticker["last_trade"])
        # ticker["rolling_24_hour_volume"] = float(ticker["rolling_24_hour_volume"])
        tick_event = TickEvent(
            sym=pair,
            exchange=Exchange.LUNO,
            code=f"{str(pair)}.{Exchange.LUNO.value}",
            timestamp=ticker["timestamp"],
            bid_p=ticker["bid"],
            ask_p=ticker["ask"],
        )
        self._mkt_queue.put(tick_event)
        return tick_event

    def get_full_L2(self, pair: str) -> dict:
        # get full orderbook - use streaming API as alternative
        return self.client.get_order_book(symbol=pair)

    @staticmethod
    def format_date(date: str):
        """Format date into timestamp in ms
        date format has to be "YYYY-MM-DD"
        """
        yymmdd = date.split("-")
        if len(yymmdd) != 3:
            raise ValueError("Incorrect date format provided. Please use YYYY-MM-DD")
        dt = datetime.datetime(int(yymmdd[0]), int(yymmdd[1]), int(yymmdd[2]), 
                               tzinfo = datetime.timezone.utc)
        return int(datetime.datetime.timestamp(dt) * 1000)
