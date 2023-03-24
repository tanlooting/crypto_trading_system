from src.events import FillEvent, OrderEvent


class OrderManager:
    def __init__(self, name):
        self.name = name
        self.standing_order_set = set()
        self.canceled_order_set = set()

    def on_new_order(self, event: OrderEvent):
        self.standing_order_set.add(event)

    def on_order_status(self):
        ...

    def on_cancel(self, order: OrderEvent):
        self.standing_order_set.remove(order)
        self.canceled_order_set.add(order)

    def on_fill(self, fillevent: FillEvent):
        # once filled, remove from standing order set and order_dict
        for order in list(self.standing_order_set):
            if order.oid == fillevent.oid:
                self.standing_order_set.remove(order)

    def get_order(self, oid):
        return

    def get_standing_order(self):
        return self.standing_order_set
