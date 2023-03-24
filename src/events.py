from enum import Enum


class Exchange(Enum):
    LUNO = "luno"
    KRAKEN = "kraken"
    BINANCE = "binance"


class EventType(Enum):
    TICK = 0
    ORDER = 1
    FILL = 2
    CHECK_ORDER_STATUS = 3


class OrderType(Enum):
    MKT = 0
    LMT = 1


class OrderDir(Enum):
    """BID = BUY, ASK = SELL"""

    BID = "BID"
    ASK = "ASK"


class OrderStatus(Enum):
    """unused"""

    AWAITING = 0
    PENDING = 1
    COMPLETE = 2


class TickEvent:
    def __init__(
        self,
        sym: str,
        exchange: Exchange,
        code: str,  # sym.exc e.g. ETHMYR.luno
        timestamp,
        bid_p,
        ask_p,
        bid_v=None,
        ask_v=None,
    ):
        self.sym = sym
        self.exc = exchange
        self.code = code
        self.type = EventType.TICK
        self.timestamp = timestamp
        self.bid_p = bid_p
        self.ask_p = ask_p
        self.bid_v = bid_v
        self.ask_v = ask_v

    def __str__(self):
        return f"TICK {self.sym}.{self.exc.value} - date: {self.timestamp}, bid: {self.bid_p}, ask: {self.ask_p}"


class OrderEvent:
    def __init__(
        self,
        sid,
        sym,
        ordertype: OrderType,
        direction,
        base_volume: float,
        price: float,
        time_in_force="GTC",
        stop=None,
        post_only=True,
    ):
        self.oid = None  # generate client_oid
        self.sid = sid  # strategy id
        self.sym = sym
        self.type = EventType.ORDER
        self.ordertype = ordertype  # MKT or LMT or STP LMT
        self.direction = direction
        self.time_in_force = time_in_force  # GTC, IOC, FOK
        self.base_volume = base_volume  # volume
        self.counter_volume = None
        self.price = price
        self.stop = stop
        self.post_only = post_only
        self.order_time = None
        self.execution_price = None
        self.luno_oid = None  # luno oid

        if (self.ordertype == OrderType.MKT) & (self.direction == OrderDir.BID):
            self.counter_volume = self.base_volume * self.price

    def __str__(self):
        return f"ORDER {self.sym}.{self.sid} - ts: {self.order_time}, luno_oid: {self.luno_oid},client_oid: {self.oid}, type: {self.ordertype}, dir: {self.direction.value}, price: {self.price}, unit: {self.base_volume}"


class FillEvent:
    def __init__(
        self,
        sid: str,
        oid: str,
        sym: str,
        dir: OrderDir,
        base,
        counter,
        fee_base,
        create_ts,
        complete_ts,
    ):
        self.sid = sid
        self.oid = oid
        self.sym = sym
        self.type = EventType.FILL
        self.dir = dir
        self.base_volume = float(base)
        self.counter_volume = float(counter)
        self.fee_base = float(fee_base)
        self.create_ts = create_ts
        self.complete_ts = complete_ts
        self.exec_price = self.counter_volume / self.base_volume

    def __str__(self):
        return f"FILL {self.sym}.{self.sid} - ts: {self.complete_ts}, oid: {self.oid}, exec_price: {self.exec_price}, base_vol: {self.base_volume}, counter_vol: {self.counter_volume} "


class CheckOrderStatusEvent:
    def __init__(self):
        self.type = EventType.CHECK_ORDER_STATUS
