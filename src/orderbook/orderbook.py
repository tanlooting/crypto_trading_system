"""
Orderbook construction
rate limit: 50 session at one time.

Reference:
https://github.com/jacoduplessis/luno_streams/blob/master/luno_streams/updater.py
https://github.com/PacktPublishing/Learn-Algorithmic-Trading/blob/master/Chapter7/OrderBook.py
https://www.luno.com/en/developers/api#tag/Streaming-API
"""
from dotenv import dotenv_values
import websockets
import asyncio
import json
import time
from decimal import Decimal
from collections import defaultdict
import pandas as pd


class BackOffException(Exception):
    ...


class orderBook:
    def __init__(self, auth: dict, pair: str):

        self.pair = pair.upper()
        self.auth = {
            "api_key_id": auth_config["luno_key_id"],
            "api_key_secret": auth_config["luno_key_secret"],
        }
        self.ws = None
        self.sequence = None
        self.bids = {}
        self.asks = {}
        self.url = f"wss://ws.luno.com/api/1/stream/{self.pair}"
        self.time_last_connection_attempt = None
        self.bid_sorted = None
        self.ask_sorted = None
        self.vamp = None
        self.mid_price = None
        self.order_imbalance = None

    def check_backoff(self):
        """avoid rate limiting"""
        if self.time_last_connection_attempt is not None:
            delta = time.time() - self.time_last_connection_attempt
            if delta < 10:
                raise BackOffException()

    async def connect(self):
        if self.ws is not None:
            await self.ws.close()
        try:
            self.check_backoff()
        except BackOffException:
            await asyncio.sleep(10)
        self.time_last_connection_attempt = time.time()

        self.ws = await websockets.connect(self.url)
        await self.ws.send(json.dumps(self.auth))

        msg = await self.ws.recv()
        initial_msg_data = json.loads(msg)
        self.sequence = int(initial_msg_data["sequence"])

        ## CREATE BID ASK TREES HERE
        self.asks = {
            x["id"]: [Decimal(x["price"]), Decimal(x["volume"])]
            for x in initial_msg_data["asks"]
        }
        self.bids = {
            x["id"]: [Decimal(x["price"]), Decimal(x["volume"])]
            for x in initial_msg_data["bids"]
        }

        print("Orderbook received")

    async def run(self):
        """first msg is always a full order book"""
        await self.connect()
        async for msg in self.ws:
            if msg == '""':
                continue
            await self.handle_message(msg)
            #print(self.print_aggregated_lob())
            self.bid_sorted = self.consolidate(self.bids.values(), reverse=True)
            self.ask_sorted = self.consolidate(self.asks.values())
            
            # calculate prices
            self.calc_vamp(level = 10)
            self.calc_midprice()
            self.calc_order_imbalance(level = 10)

    async def handle_message(self, msg):
        """Call individual handlers depending on order type"""
        data = json.loads(msg)
        new_sequence = int(data["sequence"])
        if new_sequence != self.sequence + 1:
            return await self.connect()

        self.sequence = new_sequence
        self.process_message(data)

    def process_message(self, data):
        if data["delete_update"]:
            self.handle_delete(data)
        if data["create_update"]:
            self.handle_create(data)
        if data["trade_updates"]:
            self.handle_trade(data)

    def handle_create(self, data):
        print(f"CREATE {data['create_update']}")
        order = data["create_update"]
        price = Decimal(order["price"])
        volume = Decimal(order["volume"])
        key = order["order_id"]
        book = self.bids if order["type"] == "BID" else self.asks
        book[key] = [price, volume]

    def handle_delete(self, data):
        """delete_update only has an order id key, so still have to traverse entire dict on both side to find"""
        print(f"DELETE {data['delete_update']}")
        order_id = data["delete_update"]["order_id"]
        try:
            del self.bids[order_id]
        except KeyError:
            pass
        try:
            del self.asks[order_id]
        except KeyError:
            pass
        return

    def handle_trade(self, data):
        """
        list[dict]
        keys: ["base", "counter"," maker_order_id","taker_order_id","order_id"]
        """
        trades = []
        print(f"TRADES {data['trade_updates']}")
        for update in data["trade_updates"]:
            update["price"] = Decimal(update["counter"]) / Decimal(update["base"])
            maker_order_id = update["maker_order_id"]
            if maker_order_id in self.bids:
                self.update_existing_order(key="bids", update=update)
                trades.append({**update, "type": "sell"})
            elif maker_order_id in self.asks:
                self.update_existing_order(key="asks", update=update)
                trades.append({**update, "type": "buy"})
        return trades

    def update_existing_order(self, key, update):
        book = getattr(self, key)
        order_id = update["maker_order_id"]
        existing_order = book[order_id]
        existing_volume = existing_order[1]
        new_volume = existing_volume - Decimal(update["base"])
        if new_volume == Decimal("0"):
            del book[order_id]
        else:
            existing_order[1] -= Decimal(update["base"])

    def save_states(self):
        """save current orderbook"""
        ...
        
    @staticmethod
    def consolidate(orders, reverse=False):
            price_map = defaultdict(Decimal)
            for order in orders:
                price_map[order[0]] += order[1]
            rounded_list = map(
                lambda x: [round(x[0], ndigits=4), round(x[1], ndigits=4)],
                price_map.items(),
            )

            return sorted(rounded_list, key=lambda a: a[0], reverse=reverse)

    def print_aggregated_lob(self,levels = 10):
        
        return pd.DataFrame(
            {
                "bids": self.bid_sorted[:levels],
                "asks": self.ask_sorted[:levels],
            }
        )
    
    def calc_vamp(self, levels= 10):
        # BIDS
        bid_orders = self.bid_sorted[:levels]
        vwap_b = sum([order[0] * order[1] for order in bid_orders])/sum([order[1] for order in bid_orders])
            
        # ASKS
        ask_orders = self.ask_sorted[:levels]
        vwap_a = sum([order[0] * order[1] for order in ask_orders])/sum([order[1] for order in ask_orders])
           
        self.vamp = (vwap_b + vwap_a)/2
    
    def calc_midprice(self):
        self.mid_price = (self.bid_sorted[0][0] + self.ask_sorted[0][0])/2

        
    def calc_microprice(self):
        ...
    
    def calc_order_imbalance(self, levels = 10):
        """Order imbalance
        Q_b/ (Q_a + Q_b)
        1 -> more likely to buy
        0 -> more likely to sell

        Args:
            levels (int, optional): _description_. Defaults to 10.
        """
        bid_orders = self.bid_sorted[:levels]
        ask_orders = self.ask_sorted[:levels]
        q_b = sum([order[1] for order in bid_orders])
        q_a = sum([order[1] for order in ask_orders])
        self.order_imbalance = q_b/(q_a + q_b)


if __name__ == "__main__":

    auth_config = dotenv_values(".env")
    ob = orderBook(auth_config, "ETHMYR")
    asyncio.run(ob.run())
