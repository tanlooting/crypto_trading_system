import os
import time
import yaml
import importlib
import logging
import datetime
import pathlib
import socket
from logging.handlers import SysLogHandler

from dotenv import dotenv_values
from src.brokerage.luno.luno import Luno
from src.brokerage.kraken.kraken import Kraken
from src.events_engine import EventEngine
from src.events import (
    EventType,
    TickEvent,
    OrderEvent,
    CheckOrderStatusEvent,
    FillEvent,
)
from src.strategies.strategy_manager import StrategyManager


class TradingSystem:
    def __init__(self, strat_config_path: str, heartbeat=1):
        self._auth_config = dotenv_values(".env")
        # set up event_engine
        self.heartbeat = heartbeat
        self.setup_event_engine()
        self.load_strategies(strat_config_path)
        self._logger = self.setup_logger()

        # connect
        self.luno_tc = Luno(
            auth_config=self._auth_config,
            mkt_event_engine=self.mkt_event_engine,
            action_event_engine=self.action_event_engine,
        ).get_trade_client()
        self.kraken_tc = Kraken(
            auth_config=self._auth_config,
            mkt_event_engine=self.mkt_event_engine,
            action_event_engine=self.action_event_engine,
        ).get_trade_client()
        self.setup_managers()

    def load_strategies(self, path):
        """Get all strategies, prepare tickers to load"""
        with open(path, "r") as f:
            self.trading_config = yaml.safe_load(f)

        self.strat_dict = {}
        self.instrument_list = {}

        for _, _, files in os.walk(os.path.abspath("./src/strategies/")):
            for file in files:
                if file.endswith("strategy.py"):
                    s = file.replace(".py", "")

                    try:
                        module = importlib.import_module(f"src.strategies.{s}")
                        for k in dir(module):

                            if k in self.trading_config["strategy"].keys():
                                v = module.__getattribute__(k)
                                _strategy = v()  # strategy class

                                _strategy.set_name(k)

                                self.strat_dict[k] = _strategy

                                self.instrument_list[k] = self.trading_config[
                                    "strategy"
                                ][k]["instruments"]

                    except Exception as e:
                        print(f"Unable to load strategy {s}: {e}")
        print(self.instrument_list)

    def setup_event_engine(self):
        """Set up listeners"""
        self.action_event_engine = EventEngine()
        self.action_event_engine.register_handler(EventType.ORDER, self.order_handler)
        self.action_event_engine.register_handler(EventType.FILL, self.fill_handler)
        self.action_event_engine.register_handler(
            EventType.CHECK_ORDER_STATUS, self.check_order_status_handler
        )
        self.mkt_event_engine = EventEngine()
        self.mkt_event_engine.register_handler(EventType.TICK, self.tick_handler)
        # start engine
        self.mkt_event_engine.start()
        self.action_event_engine.start()

    def setup_managers(self):
        """Set up managers"""

        self.strategy_manager = StrategyManager(
            event_engine=self.action_event_engine,
            primary_broker=self.luno_tc,
            strat_config=self.trading_config,
            instrument_list=self.instrument_list,
        )
        self.strategy_manager.load_strategy(strat_dict=self.strat_dict)

    def run(self):
        """Stream data"""
        while True:
            try:
                # 1) check outstanding orders every tick
                self.action_event_engine.put(CheckOrderStatusEvent())

                # 2) get all tickers
                for inst in list(set(self.strategy_manager.active_symbols)):
                    inst_code = inst.split(".")
                    sym, exc = inst_code[0], inst_code[1]
                    if exc == "luno":
                        ticker = self.luno_tc.get_ticker(sym)
                        self._logger.info(ticker)
                    if exc == "kraken":
                        ticker = self.kraken_tc.get_ticker(sym)

                time.sleep(self.heartbeat)
            except Exception as e:
                print(e)

    def tick_handler(self, event: TickEvent):
        """Tick handler
        When new ticks arrive, it is passed to strategies that require this data.
        """
        self.strategy_manager.on_tick(event)

    def order_handler(self, event: OrderEvent):
        """Order Handler
        once order is placed, they get added into our order_dict, and our standing order set."""
        self.strategy_manager.on_new_order(event)
        # log trades

    def check_order_status_handler(self, event: CheckOrderStatusEvent):
        """Check Order status
        open orders do not get informed on fills on Luno.
        Therefore this helps to check whether order is filled every heartbeat, and
        order_manager will check whether any open orders have been filled.
        """
        self.strategy_manager.on_order_status()

    def fill_handler(self, event: FillEvent):
        self.strategy_manager.on_fill(event)
        # log trades

    def setup_logger(self):
        """Set up logger
        Add PAPERTRAIL_HOST and PAPERTRAIL_PORT in .env file
        """
        date = datetime.date.today()
        _logger = logging.getLogger("trading_system")
        _logger.setLevel(logging.INFO)

        sysloghandler = SysLogHandler(
            address=(
                self._auth_config["papertrail_host"],
                int(self._auth_config["papertrail_port"]),
            )
        )
        log_path = pathlib.Path("./src/logs/")
        if not os.path.exists(log_path):
            os.makedirs(log_path)

        localhandler = logging.FileHandler(log_path / f"{date}.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        localhandler.setFormatter(formatter)
        sysloghandler.setFormatter(formatter)

        _logger.addHandler(localhandler)
        _logger.addHandler(sysloghandler)

        return _logger


if __name__ == "__main__":
    trader = TradingSystem(
        strat_config_path="./src/configs/global_strategy_config.yaml",
        heartbeat=1,  # need to change to async
    )
    trader.run()
