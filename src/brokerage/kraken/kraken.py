from src.brokerage.kraken.TradeClient import TradeClient
from src.brokerage.kraken.ServiceClient import ServiceClient


class Kraken:
    def __init__(self, auth_config, mkt_event_engine, action_event_engine):
        self.trade_client = TradeClient(
            auth_config=auth_config,
            mkt_event_engine=mkt_event_engine,
            action_event_engine=action_event_engine,
        )
        self.service_client = ServiceClient()

    def get_service_client(self):
        return self.service_client

    def get_trade_client(self):
        return self.trade_client
