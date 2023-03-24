from src.events import FillEvent, EventType, OrderDir, TickEvent


class PositionManager:
    """keep tracks of initial capital, equity, assets"""

    def __init__(self, name):
        self.name = name
        self.initial_capital = 0
        self.cash = 0
        self.current_equity = 0  # equity
        self.positions = {}  # dict (symbols -> position)
        self.last_price = {}
        self.inst_meta = {}

    def set_name(self, name):
        self.name = name

    def set_inst_list(self, inst_list):
        """Not implemented: store important metadata of each instrument"""
        self.inst_list = inst_list

    def get_position_size(self):
        """Not implemented"""

    def get_total_pnl(self):
        # unrealized + realized
        return self.current_equity - self.initial_capital

    def on_init(self, symbols):
        """initialize all positions as 0, starting with 100% cash"""
        for sym in symbols:
            sym = sym.split(".")[0]
            self.positions[sym] = 0
            self.last_price[sym] = None

    def set_capital(self, initial_capital):
        self.initial_capital = initial_capital  # for individual strategy
        self.cash = initial_capital

    def on_fill(self, event: FillEvent):
        if event.dir == OrderDir.ASK:
            if event.base_volume > self.positions[event.sym]:
                print("trying to sell more than what you own. Check!")
            self.positions[event.sym] -= event.base_volume
            self.cash += event.counter_volume
        if event.dir == OrderDir.BID:
            self.positions[event.sym] += event.base_volume
            self.cash -= event.counter_volume

    def get_cash(self):
        return self.cash

    def mark_to_market(self, event: TickEvent):
        """update current price"""
        symbol = event.sym
        mid_price = (event.bid_p + event.ask_p) / 2
        if symbol in self.positions.keys():
            self.last_price[symbol] = mid_price
        self.current_equity = self.cash
        for symbol in self.positions.keys():
            self.current_equity += self.positions[symbol] * self.last_price[symbol]
