""" 
PURE MARKET MAKING 
@looting 

Reference:
https://docs.hummingbot.org/strategies/pure-market-making/#architecture
"""

from src.strategies.strategy_base import StrategyBase
from src.events import OrderEvent, OrderType, TickEvent, OrderDir, Exchange
from termcolor import cprint, colored


class marketMaking(StrategyBase):
    def __init__(self):
        """ """
        super(marketMaking, self).__init__()
        self.counter = 0
        self.spread_pct = 0

        self.mid_price = list()
        self.bid_counter = 0
        self.ask_counter = 0

        # connect to logs/ database service

    def on_tick(self, event: TickEvent):

        self.counter += 1
        mid_p = (event.ask_p + event.bid_p) / 2
        self.spread_pct = (event.ask_p - event.bid_p) / mid_p
        print(f"{event}, spread_pct = {self.spread_pct *100}%")
        super().on_tick(event)

        print(f"Current standing orders: {self.get_order_ids()}")
        print(f"Current cancelled orders: {self.get_cancelled_order_ids()}")
        print(
            f"Current cash: {self.position_manager.get_cash()},Total PnL: {self.position_manager.get_total_pnl()}, Positions: {self.position_manager.positions}"
        )

    def get_order_ids(self):
        order_ids = []
        for order in self.order_manager.standing_order_set:
            order_ids.append(order.luno_oid)
        return order_ids

    def get_cancelled_order_ids(self):
        order_ids = []
        for order in self.order_manager.canceled_order_set:
            order_ids.append(order.luno_oid)
        return order_ids

    def cancel_bids(self):
        ...
        self.bid_counter = 0

    def cancel_asks(self):
        ...
        self.ask_counter = 0

    def on_order_status(self):
        super().on_order_status()
        # do something more like check if time exceeds max age limit.
        # if yes, cancel orders

    def get_volatility():
        ...

    def kill_switch(self):
        """if pnl down significantly, or some shit happens. EXIT trading strategy."""
        self.active = False
        ...

    def cancel_all(self):
        super().cancel_all()
        self.bid_counter = 0
        self.ask_counter = 0
