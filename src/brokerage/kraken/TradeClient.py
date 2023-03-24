from dateutil.relativedelta import relativedelta
import datetime
import pandas as pd
import time
import krakenex
from pykrakenapi import KrakenAPI
from src.events import TickEvent, Exchange
from src.events_engine import EventEngine


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
        auth_config: dict,
        mkt_event_engine: EventEngine,
        action_event_engine: EventEngine,
    ):
        self.api_key = auth_config["kraken_api_key"]
        self.private_key = auth_config["kraken_private_key"]
        kraken_api = krakenex.API(key=self.api_key, secret=self.private_key)
        self.client = KrakenAPI(kraken_api)
        self._queue = mkt_event_engine

    def get_ohlcv(self, pair: str, interval: str, since: str) -> pd.DataFrame:
        return self.client.get_ohlc_data(pair=pair, interval=interval, since=since)

    def get_historical_ohlcv_data(
        self, instrument: str, start: str, end: str, granularity: int = 3600
    ) -> pd.DataFrame:
        ...

    def get_ticker(self, pair: str) -> dict:
        ticker = self.client.get_ticker_information(pair=pair)
        ask_p = float(ticker["a"][0][0])
        ask_v = float(ticker["a"][0][2])
        bid_p = float(ticker["b"][0][0])
        bid_v = float(ticker["b"][0][2])
        # mid_price = (ask_p* bid_v + bid_p*ask_v) / (bid_v + ask_v)
        tick_event = TickEvent(
            sym=pair,
            exchange=Exchange.KRAKEN,
            code=f"{str(pair)}.{Exchange.KRAKEN.value}",
            timestamp=datetime.datetime.now().timestamp() * 1000,
            bid_p=bid_p,
            ask_p=ask_p,
            bid_v=bid_v,
            ask_v=ask_v,
        )
        self._queue.put(tick_event)
        return tick_event

    def get_L2(self, pair: str, count: int = 20) -> dict:
        return self.client.get_order_book(pair, count)

    def get_full_L2(self, pair: str) -> dict:
        return

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
