import numpy as np
import pandas as pd
from forex_python.converter import CurrencyRates
from src.strategies.strategy_base import StrategyBase
from src.events import OrderEvent, OrderType, TickEvent, OrderDir, Exchange


def is_profitable(ratio: float, margin: float, fee: float = 0.005) -> bool:
    """Calculates whether current ratio is profitable"""
    profit = ratio - fee
    if profit > margin:
        return True
    return False


def is_buyable(ob: dict):
    """Check if it's tradable under current orderbook quality
    - check spread, check
    """
    # if spread is low < threshold
    units = ob["a"][0]  # check the orderbook info.
    return True, units


class latencyArbitrage(StrategyBase):
    def __init__(self):
        """ """
        super(latencyArbitrage, self).__init__()
        margin = 0.005
        self.lookback = 100  # lookback
        self.take_profit = None  #  take_profit
        self.stop_loss = None  # stop_loss
        self.time_limit = None  # time_limit
        self.margin = margin
        self.position = 0

        self.update_currency_ind = 0
        # self.c = CurrencyRates()
        # self.current_ccy = self.c.get_rate("USD", "MYR")
        self.current_ccy = 1
        self.dom_price = list()
        self.for_price = list()
        self.ratio = list()
        self.dom_current_price = 0
        self.for_current_price = 0
        self.current_ratio = 0
        self.dom_ts = 0
        self.for_ts = 0
        self.counter = 0
        self.spread_pct = 0

        # check how long these big jumps can sustain?
        # then we decide how much to take profit
        # stop loss will be based on time limit, or exit if <  or trailing stop
        # see orderbook size, we take the first layer?

        # match prices
        # take profit

    def on_tick(self, event: TickEvent):
        self.counter += 1
        print(event)
        if self.counter == 3:
            o = OrderEvent(
                sid=self.id,
                sym=event.sym,
                ordertype=OrderType.MKT,
                direction=OrderDir.BID,  # buy order
                unit=0.0001,
            )
            self.place_order(o)

        # if event.exc != Exchange.LUNO:
        #     wap = (event.bid_p * event.ask_v + event.ask_p * event.bid_v) / (
        #         event.ask_v + event.bid_v
        #     )
        #     wap *= self.current_ccy
        #     self.for_current_price = wap
        #     self.for_price.append(wap)
        #     self.for_ts = event.timestamp
        # else:
        #     # get currency and append to current_price
        #     spread = event.ask_p - event.bid_p
        #     self.dom_current_price = (event.ask_p + event.bid_p) / 2
        #     self.dom_ts = event.timestamp
        #     self.spread_pct = spread / self.dom_current_price

        # if self.counter >= 2:
        #     # up to 1 sec lag
        #     if (self.for_ts - self.dom_ts > 0) & ((self.for_ts - self.dom_ts) < 1000):
        #         ratio = self.for_current_price / self.dom_current_price
        #         self.ratio.append(ratio)
        #         print(
        #             f"ratio: {ratio}, timelag: {self.for_ts - self.dom_ts}, spread_pct: {self.spread_pct}"
        #         )
        #     if len(self.ratio) == self.lookback:
        #         self.ratio = self.ratio[1:]
        #         print(
        #             f"profitability: {ratio / np.mean(self.ratio) - 1 - 0.005 - self.spread_pct}, z-score: {(ratio - np.mean(self.ratio))/ np.std(self.ratio)}"
        #         )
        #     # o = OrderEvent(
        #     #     sid=self.id,
        #     #     sym=event.sym,
        #     #     ordertype=OrderType.MKT,
        #     #     direction=OrderDir.BID,  # buy order
        #     #     unit=0.0001,
        #     # )
        #     # self.place_order(o)
        # self.update_currency_ind += 1
        # # change to tick
        # if self.update_currency_ind == 200:
        #     self.update_currency_ind = 0
        #     self.current_ccy = self.c.get_rate("USD", "MYR")

        # # take profit is the historical mean
        # # when it returns to mean, then take profit
        # data_fast: float = 0
        # data_slow: float =0
        # latest_spread = data_fast / data_slow
        # self.tick += 1
        # self.ratio.append(latest_spread)
        # if self.tick > self.lookback:
        #     self.tick -= 1
        #     self.ratio = self.ratio[1:]  # drop first tick

        # hist_avg = np.mean(self.ratio)  # or median?
        # if is_profitable():
        #     if is_buyable[0]:
        #         units = is_buyable[1]

        #     # check account?
        #     # generate unique order ID
        #     # submit buy_order to order manager (keeps track of fill)
        #     # save trades
        #     # update position
        #     self.position = 1

    def get_orders(self):
        return self.order_manager.order_dict[self.id]
