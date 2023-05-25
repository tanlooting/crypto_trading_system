""" TESTS
    1. at 5th tick we places a market order

    2. At 10th tick we place a far limit order BUY order

    3. At 12th tick we place another limit BUY order

    4. At 20th tick, cancel all orders (useful for MM/ time-based orders)
"""
import logging
import time
import numpy as np
from src.strategies.strategy_base import StrategyBase
from src.events import OrderEvent, OrderType, TickEvent, OrderDir, Exchange
from termcolor import cprint, colored

_logger = logging.getLogger("trading_system")


class naiveTest(StrategyBase):
    def __init__(self):
        """ """
        super(naiveTest, self).__init__()
        self.counter = 0
        self.spread_pct = 0
        self.prev_time = time.time()

    def on_tick(self, event: TickEvent):
        
        self.counter += 1
        mid_p = (event.ask_p + event.bid_p) / 2
        self.spread_pct = (event.ask_p - event.bid_p) / mid_p

        #print(f"{event}, spread_pct = {self.spread_pct *100}%, {self.counter}")

        super().on_tick(event)
        self.current_time = time.time()
        self.prev_time = self.current_time
        if self.counter == 5:

            # test placing a market order:
            o = OrderEvent(
                sid=self.id,
                sym=event.sym,
                ordertype=OrderType.MKT,
                direction=OrderDir.BID,  # buy order
                price=mid_p,
                base_volume=0.12,
            )

            self.place_order(o)
            
        # if (self.counter == 10) | (self.counter == 15):
        #     # test placing a limit order that is far away
        #     o = OrderEvent(
        #         sid=self.id,
        #         sym=event.sym,
        #         ordertype=OrderType.LMT,
        #         direction=OrderDir.BID,  # buy order
        #         price=round(mid_p - 15, 2),
        #         base_volume=0.1,
        #     )
        #     self.place_order(o)

        # if self.counter == 20:
        #     self.cancel_all()

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
