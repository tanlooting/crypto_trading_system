import datetime
import logging
from src.brokerage.luno.TradeClient import TradeClient
from src.orders.order_manager import OrderManager
from src.positions.position_manager import PositionManager
from src.events_engine import EventEngine
from src.utils.alerts import Alerts
from src.utils.db_service import DBService
from src.events import (
    TickEvent,
    OrderEvent,
    OrderType,
    OrderDir,
    FillEvent,
    CheckOrderStatusEvent,
)
import uuid

_logger = logging.getLogger("trading_system")


class StrategyManager:
    def __init__(
        self,
        event_engine: EventEngine,
        primary_broker: TradeClient,
        strat_config: dict,
        instrument_list: dict,
        alerts_system: Alerts,
        database
    ):
        self._event_engine = event_engine
        self._broker = primary_broker
        self.strat_config = strat_config
        self.symbols_dict = instrument_list  # {exc: [sym]}
        self._alerts = alerts_system
        self._database = database

        self.strat_dict = {}
        self.sym_strategy_dict = {}  # symbol to strategy
        self.sym_tick_size_dict = self.strat_config["min_tick_size"]
        self.strat_sym_dict = {}
        self.active_symbols = []
        self._sid_oid_dict = {0: []}  # others note in

    def load_strategy(self, strat_dict: dict):
        sid = 1
        for k, v in strat_dict.items():
            v.id = sid
            v.name = k
            sid += 1

            if k in self.strat_config["strategy"].keys():
                v.active = self.strat_config["strategy"][k]["active"]
                v.set_capital(self.strat_config["strategy"][k]["capital"])
                v.set_symbols(self.symbols_dict[k])  # list
                v.set_params(self.strat_config["strategy"][k]['params'])
                if v.active:
                    for sym in v.symbols:
                        self.active_symbols.append(sym)
            self.strat_dict[v.id] = v
            self._sid_oid_dict[v.id] = []  # order id dict

            # subscribe each strategy to the symbols:
            for sym in v.symbols:
                if sym in self.sym_strategy_dict:
                    self.sym_strategy_dict[sym].append(v.id)
                else:
                    self.sym_strategy_dict[sym] = [v.id]

            v.on_init(self)

    def on_tick(self, event: TickEvent):
        """pass market data to each strategy that needs this"""
        if event.code in self.sym_strategy_dict.keys():
            strats = self.sym_strategy_dict[event.code]
            for sid in strats:
                if self.strat_dict[sid].active:
                    self.strat_dict[sid].on_tick(event)

    def place_order(self, event: OrderEvent, check_risk=False):

        # check order
        # if check_risk:
        #     # do something
        #     order_checked = True
        #     if not order_checked:
        #         return

        # generate unique client order id
        oid = str(uuid.uuid4())
        event.oid = oid
        event.order_time = datetime.datetime.now().timestamp() * 1000
        self._sid_oid_dict[event.sid].append(oid)
        # actual place order
        if event.ordertype == OrderType.MKT:
            params = {
                "pair": event.sym,
                "type": event.direction.value,
                "client_order_id": event.oid,
            }
            if event.direction == OrderDir.BID:
                params["counter_volume"] = event.counter_volume
            elif event.direction == OrderDir.ASK:
                params["base_volume"] = event.base_volume

            self._broker.place_market_order(**params)

        elif event.ordertype == OrderType.LMT:

            self._broker.place_limit_order(
                pair=event.sym,
                price=event.price,
                type=event.direction.value,
                volume=event.base_volume,
                client_order_id=event.oid,
                post_only=event.post_only,
            )
        
        new_order = self._broker.get_order(event.oid)
        event.luno_oid = new_order["order_id"]
        self._event_engine.put(event)

    def on_new_order(self, event: OrderEvent):
        if event.sid in self.strat_dict.keys():
            self.strat_dict[event.sid].on_new_order(event)
            _logger.info(f"Order placed: {event}")
            self._alerts.send_telegram_message(f"Order placed: {event}")
        else:
            print("strategy ID doesn't exist. ")

    def on_order_status(self):
        """Check all standing orders"""
        for strat_id in self.strat_dict.keys():
            if self.strat_dict[strat_id].active == True:
                self.strat_dict[strat_id].on_order_status()

    def on_fill(self, event: FillEvent):
        if event.sid in self.strat_dict.keys():
            self.strat_dict[event.sid].on_fill(event)
            _logger.info(f"Order filled: {event}")
            self._database['trades'].insert_one(event._dict())
            self._alerts.send_telegram_message(f"Order filled: {event}")
            
        else:
            print("strategy ID doesn't exist. ")

    def start_strategy(self, sid):
        """Not implemented. Need for GUI"""

    def stop_strategy(self, sid):
        """Not implemented. Need for GUI"""

    def start_all(self):
        """Not implemented. Need for GUI"""

    def stop_all(self):
        """Not implemented. Need for GUI"""

    def flat_order(self):
        pass

    def flat_all(self):
        pass
