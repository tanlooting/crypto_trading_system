import json

import time
import json
import requests
import urllib
from typing import Awaitable, Any
import asyncio

# import websocket
from forex_python.converter import CurrencyRates
from luno_python.client import Client

# class sinegy_data:
#     """ Working but to check with Sinegy:
#     - Ticker does not come with server timestamp
#     - orderbook server timestamp returns 0
#     """
#     def __init__(self, pair:str, key_id:str, key_secret:str):
#         self.key_id = key_id
#         self.key_secret = key_secret
#         self.pair = pair

#     async def connect(self):
#         pass

#     async def get_bid_ask(self, outpath: str) -> Awaitable[dict]:
#         headers = {
#             'api-key': self.key_id
#         }

#         url = 'https://api.sinegy.com/api/v1/market/spot/orderbook'
#         path = {
#             'currencyPair': self.pair,
#         }
#         url += '?' + urllib.parse.urlencode(path)
#         ob = requests.request(method = 'GET', url = url, headers = headers, data = None).json()
#         await asyncio.sleep(0.5)
#         ts = round(time.time()* 1000) #ts = ob['data'][1]
#         ask = min(ob['data'][2])
#         bid = max(ob['data'][5])

#         query = {"ts": ts,
#                  "ask": ask,
#                  "bid": bid,
#                  "mid": (ask + bid) / 2,
#                  "spread": ask - bid
#                  }
#         print(f"Sinegy:{query}")

#         with open(outpath,"a") as f:
#             json.dump(query,f)
#             f.write("\n")
#         return await query


class luno_data:
    def __init__(self, pair: str, key_id: str, key_secret: str):
        self.key_id = key_id
        self.key_secret = key_secret
        self.pair = pair

    async def connect(self):
        if (self.key_secret == None) | (self.key_id == None):
            raise AttributeError("API key not provided")

        self.client = Client(api_key_id=self.key_id, api_key_secret=self.key_secret)
        print("connected to Luno...")

    async def get_bid_ask(self, outpath=None, save_file=False):
        x = await self.client.get_ticker(self.pair)
        asyncio.sleep(0.5)
        query = {
            "ts": x["timestamp"],
            "ask": x["ask"],
            "bid": x["bid"],
            "mid": (float(x["ask"]) + float(x["bid"])) / 2,
            "spread": float(x["ask"]) - float(x["bid"]),
        }
        print(f"Luno:{query}")
        if save_file:
            with open(outpath, "a") as f:
                json.dump(query, f)
                f.write("\n")
        return await query

    async def __repr__(self):
        return repr(self.pair)


# class binance_data:
#     def __init__(self, pair:str, socket:str, conv_rate: float) -> None:
#         self.pair = pair
#         self.socket = socket
#         self.conv_rate = conv_rate

#     async def connect(self):
#         print('connecting to Binance...')
#         return websocket.create_connection(self.socket)

#     async def get_bid_ask(self, con: object, outpath: str) -> Awaitable[dict]:
#         """ Connect and stream data
#         """
#         x = json.loads(con.recv())
#         ask_myr = float(x['a'])* self.conv_rate
#         bid_myr = float(x['b'])* self.conv_rate
#         query = {'ts': x['E'],
#             'ask': ask_myr,
#             'bid': bid_myr ,
#             'mid': (ask_myr + bid_myr) / 2,
#             'spread': (ask_myr - bid_myr)
#            }
#         print(f"Binance: {query}")

#         with open(outpath,"a") as f:
#             json.dump(query,f)
#             f.write("\n")
#         return await query
