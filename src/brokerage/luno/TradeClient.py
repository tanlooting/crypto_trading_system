from luno_python.client import Client
from dateutil.relativedelta import relativedelta
import datetime
import pandas as pd
import time
from src.events import EventType, Exchange, TickEvent, OrderEvent
from src.events_engine import EventEngine
import logging

_logger = logging.getLogger("trading_system")

ALL_VALID_GRANULARITY = [
    60,
    300,
    900,
    1800,
    3600,
    10800,
    14400,
    28800,
    86400,
    259200,
    604800,
]


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
        auth_config,
        mkt_event_engine: EventEngine,
        action_event_engine: EventEngine,
    ):
        self.id = auth_config["luno_key_id"]
        self.secret = auth_config["luno_key_secret"]
        self.client = Client(api_key_id=self.id, api_key_secret=self.secret)
        self._mkt_queue = mkt_event_engine
        self._action_queue = action_event_engine

    def get_account_details(self):
        pass

    def get_account_summary(self):
        # show all account positions and balances
        try:
            return self.client.get_balances()
        except Exception as e:
            print(e)

    def get_account_capital(self) -> int:
        """Returns cash capital (MYR wallet)
        Does not include any cryptocurrencies.

        Returns:
            int: capital in MYR wallet
        """
        try:
            return self.client.get_balances(assets="MYR")["balance"][0]["balance"]
        except Exception as e:
            print(e)

    def get_markets_info(self):
        """Get all Luno's markets - Only list MYR denominated cryptocurrencies"""
        try:
            r = self.client.markets()["markets"]
            instruments = {}
            for inst in r:
                if inst["counter_currency"] == "MYR":
                    inst_name = inst["market_id"]
                    instruments[inst_name] = {
                        "trading_status": inst["trading_status"],
                        "min_volume": inst["min_volume"],
                        "max_volume": inst["max_volume"],
                        "volume_scale": inst["volume_scale"],
                        "price_scale": inst["price_scale"],
                    }
            # input(json.dumps(instruments, indent = 2))
            return instruments
        except Exception as e:
            print(e)

    def get_account_trades(self, pair):
        trades = pd.DataFrame(self.client.list_user_trades(pair=pair)["trades"])
        trades["timestamp"] = pd.to_datetime(trades["timestamp"], unit="ms")
        return trades

    def get_account_orders(self):
        orders = self.client.list_orders()["orders"]
        return orders

    def get_ohlcv(self, pair: str, count: int, granularity: int) -> pd.DataFrame:
        """
        Granularity (in seconds) - 60 for 1m bars

        Ref:
        https://www.luno.com/en/developers/api#tag/Market/operation/GetCandles
        https://github.com/luno/luno-python/blob/master/luno_python/client.py#L134
        """
        if granularity not in ALL_VALID_GRANULARITY:
            raise NotImplementedError(
                "Selected granularity not supported in luno_python API"
            )

        try:
            # duration, pair, since

            period = count * granularity
            since = int(
                datetime.datetime.timestamp(
                    datetime.datetime.now() - relativedelta(seconds=period)
                )
                * 1000
            )  # convert to ms
            print(
                int(datetime.datetime.timestamp(datetime.datetime.now()) * 1000), since
            )
            ohlcv_dict = self.client.get_candles(granularity, pair, since)["candles"]
            ohlcv = pd.DataFrame(ohlcv_dict)
            ohlcv.columns = ["date", "open", "close", "high", "low", "volume"]
            ohlcv["date"] = pd.to_datetime(ohlcv["date"], unit="ms")
            # ohlcv['date'] = ohlcv['date'].apply(lambda x: self.format_date(x))
            return ohlcv
        except Exception as e:
            print(e)

    def get_historical_ohlcv_data(
        self, instrument: str, start: str, end: str, granularity: int = 3600
    ) -> pd.DataFrame:
        MAX_CANDLES = 1000
        start = TradeClient.format_date(start)
        end = TradeClient.format_date(end)

        if granularity not in ALL_VALID_GRANULARITY:
            raise NotImplementedError(
                "Selected granularity not supported in luno_python API"
            )

        df = pd.DataFrame()
        numeric_columns = ["open", "close", "high", "low", "volume"]
        while start < end:
            ohlcv = pd.DataFrame(
                self.client.get_candles(granularity, instrument, start)["candles"]
            )
            ohlcv.columns = ["date", "open", "close", "high", "low", "volume"]
            ohlcv["date"] = pd.to_datetime(ohlcv["date"], unit="ms")
            ohlcv[numeric_columns] = ohlcv[numeric_columns].apply(
                pd.to_numeric, errors="coerce"
            )
            df = pd.concat([df, ohlcv], axis=0)
            start += MAX_CANDLES * granularity * 1000
            time.sleep(0.2)
        df = df.drop_duplicates(subset=["date"])
        df = df.reset_index(drop=True)
        return df

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

    def get_L2(self, pair: str) -> dict:
        # returns top 100 only. use get_full_L2 to get complete orderbook or use streaming API instead.
        return self.client.get_order_book(pair=pair)

    def get_full_L2(self, pair: str) -> dict:
        # get full orderbook - use streaming API as alternative
        return self.client.get_order_book_full(pair=pair)

    def place_limit_order(
        self,
        pair: str,
        price: float,
        type: str,  # BID or ASK only for buy/sell order respectively
        volume: float,
        base_account_id=None,
        client_order_id=None,
        counter_account_id=None,
        post_only: bool = True,
        stop_direction=None,
        stop_price=None,  # for stop limit
        timestamp=None,
        ttl=None,
    ):

        self.client.post_limit_order(
            pair=pair,
            price=price,
            type=type,
            volume=volume,
            base_account_id=base_account_id,
            client_order_id=client_order_id,
            counter_account_id=counter_account_id,
            post_only=post_only,
            stop_direction=stop_direction,
            stop_price=stop_price,
            timestamp=timestamp,
            ttl=ttl,
        )

    def place_market_order(
        self,
        pair: str,
        type: str,  # direction BID/ASK
        base_account_id=None,
        base_volume=None,
        client_order_id=None,
        counter_account_id=None,
        counter_volume=None,  # how much MYR to use to BTC in the BTC/MYR
        timestamp=None,
        ttl=None,
    ):
        self.client.post_market_order(
            pair,
            type,
            base_account_id,
            base_volume,
            client_order_id,
            counter_account_id,
            counter_volume,
            timestamp,
            ttl,
        )

    def generate_order_id(self):
        """generate a valid unique Client Order Id for posting orders"""
        pass

    def get_order(self, order_id) -> dict:
        return self.client.get_order_v3(client_order_id=order_id)

    def get_order_status(self, order_id) -> str:
        """
        order status includes "AWAITING", "PENDING", "COMPLETE"
        """
        return self.get_order(order_id)["state"]

    def cancel_order(self, order_id):
        self.client.stop_order(order_id=order_id)

    def get_fee_info(self, pair: str) -> dict:
        return self.client.get_fee_info(pair=pair)

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
