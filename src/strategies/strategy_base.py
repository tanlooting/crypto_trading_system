from abc import ABC
from src.strategies.strategy_manager import StrategyManager
from src.orders.order_manager import OrderManager
from src.positions.position_manager import PositionManager
from src.events import TickEvent, OrderEvent, CheckOrderStatusEvent, FillEvent
import copy


class StrategyBase(ABC):
    def __init__(self):
        self.name = ""
        self.id = None
        self.symbols: list[str] = None
        self.strategy_manager: StrategyManager = None
        self.order_manager: OrderManager = OrderManager(self.name)
        self.position_manager: PositionManager = PositionManager(self.name)
        self.active: bool = False
        self.initialized: bool = False

    def set_capital(self, initial_capital):
        self.capital = initial_capital
        self.position_manager.set_capital(initial_capital)

    def set_symbols(self, symbols: list):
        self.symbols = symbols

    def set_name(self, name):
        self.name = name

    def set_params(self, params: dict = None):
        if params is not None:
            for k, v in params.items():
                try:
                    self.__setattr__(k, v)
                except:
                    pass

    def on_init(self, strategy_manager):
        self.strategy_manager = strategy_manager
        self.position_manager.on_init(self.symbols)
        self.initialized = True

    def on_start(self):
        self.active = True

    def on_stop(self):
        self.active = False

    def on_tick(self, event: TickEvent):
        # update portfolio positions P&L
        self.position_manager.mark_to_market(event)

    def on_new_order(self, orderevent: OrderEvent):
        """New order comes in"""
        self.order_manager.on_new_order(orderevent)

    def on_order_status(self):
        for order in list(self.order_manager.standing_order_set):

            order_info = self.strategy_manager._broker.get_order(order.oid)
            order: OrderEvent
            # if order filled, put fillevent into event_engine,
            # remove from order dict and standing order set
            if order_info["status"] == "COMPLETE":
                # add to filled order
                fill_event = FillEvent(
                    sid=order.sid,
                    oid=order.oid,
                    sym=order.sym,
                    dir=order.direction,
                    base=order_info["base"],
                    counter=order_info["counter"],
                    fee_base=order_info["fee_base"],
                    create_ts=order_info["creation_timestamp"],
                    complete_ts=order_info["completed_timestamp"],
                )
                print(f"Order Filled: {fill_event}")
                self.strategy_manager._event_engine.put(fill_event)

    def on_fill(self, fillevent):
        # update positions
        self.order_manager.on_fill(fillevent)
        self.position_manager.on_fill(fillevent)

    def place_order(self, orderevent: OrderEvent):
        if self.active:
            self.strategy_manager.place_order(orderevent)

    def cancel_order(self, oid):

        for order in list(self.order_manager.standing_order_set):
            if order.oid == oid:
                self.strategy_manager._broker.cancel_order(order.luno_oid)
                self.order_manager.on_cancel(order)

    def cancel_all(self):

        for order in list(self.order_manager.standing_order_set):  # use a copy
            self.strategy_manager._broker.cancel_order(order.luno_oid)
            self.order_manager.on_cancel(order)

        print(f"Canceled all orders.")
