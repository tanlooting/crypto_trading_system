""" 
PURE MARKET MAKING 
@looting 

Reference:
https://docs.hummingbot.org/strategies/pure-market-making/#architecture
"""

import time
import logging

# from termcolor import cprint, colored
from src.strategies.strategy_base import StrategyBase
from src.events import (
    OrderEvent,
    OrderType,
    TickEvent,
    OrderDir,
    Exchange,
    FillEvent,
    EventType,
)

_logger = logging.getLogger("trading_system")

class marketMaking(StrategyBase):
    def __init__(self):
        """ """
        super(marketMaking, self).__init__()
        self.first_tick = True
        self.spread_pct = 0

        self.mid_price = list()
        self.bid_counter = 0  # no. of bids placed
        self.ask_counter = 0  # no. of asks placed

        self.bid_spread = 0  # distance away from mid price
        self.ask_spread = 0 
        self.min_spread = 0 # at what min spread should the bot automatically cancel orders

        self.order_refresh_time = 0  # seconds before cancelling all orders
        self.order_refresh_tolerance_pct  = 0 #
        
        self.order_levels = 1  # no. of orders at each side
        self.order_level_amount = 0 # volume increments for subsequent orders
        self.order_level_spread = 0 # price increments for subsequent orders

        self.inventory_skew_enabled = False
        self.inventory_target_base = 0  # target inventory
        self.inventory_range = 0  # tolerable range of inventory

        self.filled_order_delay = 0
        self.ping_pong_enabled = False
        # PARAMS (initialized from the start)
        self.min_tick_size = None
        self.base_init_inventory = None # base asset inventory level
        self.counter_inventory = None # counter asset inventory level
        self.target_ratio = 0
        self.current_ratio = 0

    def on_tick(self, event: TickEvent):
        super().on_tick(event)
        # get tick, this can be replaced with other microprice for better edge
        # quote based on micro-price
        mid_p = (event.ask_p + event.bid_p) / 2
        self.spread_pct = (event.ask_p - event.bid_p) / mid_p
        print(f"{event}, spread_pct = {self.spread_pct *100}%")
        
        # init anything that requires first tick.
        if self.first_tick:
            self.target_ratio = self.base_init_inventory * mid_p/self.counter_inventory
            self.current_ratio = self.target_ratio
            self.first_tick = False
        else:
            self.update_inventory(mid_p, event.sym)

        # LOGIC STARTS HERE
        
        # do not quote is regime unsuitable
        if not self.regime_suitable():
            self.cancel_all()
            return 

        # if order in place, and not stale. - not placing order
        # if no orders or haven't reached max - place order
        if not self.reached_max_orders("BIDS"):
            # place bid
            # calculate optimal bid. calculate size
            ...

        if not self.reached_max_orders("ASK"):
            # place asks
            ...

        # if order stale. - cancel order [DONE - see on_order_status]

        print(f"Current standing orders: {self.get_order_ids()}")
        print(f"Current cancelled orders: {self.get_cancelled_order_ids()}")
        print(
            f"Current cash: {self.position_manager.get_cash()},Total PnL: {self.position_manager.get_total_pnl()}, Positions: {self.position_manager.positions}"
        )
        

    def reached_max_orders(self, side):
        if side == "BID":
            if self.bid_counter == self.order_levels:
                return True
        elif side == "ASK":
            if self.ask_counter == self.order_levels:
                return True

    def regime_suitable(self):
        """Not implemented yet"""
        # if volatility spikes/breakout - not placing order. check if orders are in place, cancel them if necessary. set waiting time
        # condition to place order or not lies on volatility
        # precheck - market condition ok to market make?
        # news/ volatility spikes/ using lead-lag signal etc.
        return True

    def cal_optimal_bid_ask(self):
        """Not implemented yet"""
        ...

    def cal_top_bid_ask(self, event: TickEvent):
        """calculate L1 spreads"""
        min_tick = self.min_tick_size
        if (event.ask_p - event.bid_p) == min_tick:
            return event.bid_p, event.ask_p
        elif (event.ask_p - event.bid_p) == (2 * min_tick):
            # need to fix this
            return event.bid_p + min_tick, event.ask_p
        else:
            return event.bid_p + min_tick, event.ask_p - min_tick

    def cal_order_size(self):
        """Not implemented yet - calculate order size to place based on inventory"""
        ...

    def update_inventory(self, price, symbol):
        self.counter_inventory = self.position_manager.cash
        base_current_inventory = self.base_init_inventory + self.position_manager[symbol] * price
        self.current_ratio = base_current_inventory / self.counter_inventory

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

    def cancel_bids(self, orders: list):
        for order in orders:
            self.cancel_order(order)
            self.bid_counter -= 1

    def cancel_asks(self, orders: list):
        for order in orders:
            self.cancel_order(order)
            self.ask_counter -= 1

    def on_order_status(self):
        super().on_order_status()
        # if time since placement exceeds order refresh time, cancel order
        current_time = time.time_ns() / 1000
        for order in self.order_manager.standing_order_set:
            order: OrderEvent
            if current_time - order.order_time > self.order_refresh_time:
                self.cancel_order(order.oid)
                if order.direction == OrderDir.BID:
                    self.bid_counter -= 1
                elif order.direction == OrderDir.ASK:
                    self.ask_counter -= 1

    def kill_switch(self):
        """if pnl down significantly, or some shit happens. EXIT trading strategy."""
        self.active = False
        self.cancel_all()
        # save all files and exit program.

    def cancel_all(self):
        super().cancel_all()
        self.bid_counter = 0
        self.ask_counter = 0

    def on_fill(self, event: FillEvent):
        # check if filled - bid counter set to 0
        super().on_fill(event)
        if event.dir == OrderDir.BID:
            self.bid_counter -= 1
        else:
            self.ask_counter -= 1
