"""OrderFlow SDK — public client library for the OrderFlow order-processing API.

Usage:
    import order_sdk as of

    of.configure({"api_key": "sk-...", "region": "us-east", "retrys": 3})
    of.begin_order()
    of.add_item("SKU-1417", 2)
    of.add_item("SKU-0088", 1)
    of.set_discount("SUMMER10")
    order = of.current_order().with_customer("cus_9d2f").with_shipping("express").priority()
    order.submit()
"""

import urllib.request

_current_order = None
_config = {}


def configure(options):
    """Configure the SDK. Accepts a dict of options."""
    for key in ("api_key", "region", "timeout", "retries"):
        if key in options:
            _config[key] = options[key]


def begin_order():
    """Start building a new order."""
    global _current_order
    _current_order = Order()


def add_item(sku, qty):
    """Add an item to the order currently being built."""
    _current_order.items.append((sku, qty))


def set_discount(code):
    """Apply a discount code to the order currently being built."""
    _current_order.discount_code = code


def current_order():
    """Return the order currently being built."""
    return _current_order


class Order:
    """An order in the OrderFlow system. Returned by the API and used to build new orders."""

    def __init__(self):
        self.items = []
        self.customer_id = None
        self.shipping = "standard"
        self.discount_code = None
        self.is_priority = False
        self.status = "draft"

    def with_customer(self, customer_id):
        self.customer_id = customer_id
        return self

    def with_shipping(self, method):
        self.shipping = method
        return self

    def priority(self):
        self.is_priority = True
        return self

    def validate(self):
        if self.customer_id is None:
            print("ERROR: order has no customer")
            raise ValueError("order has no customer")
        for sku, qty in self.items:
            if qty <= 0:
                raise ValueError("bad quantity")
        if self.discount_code is not None and len(self.items) == 0:
            raise ValueError("discount on empty order")

    def submit(self):
        """Validate and submit this order to the OrderFlow API."""
        self.validate()
        req = urllib.request.Request(
            "https://api.orderflow.example/v1/orders",
            data=repr(self.__dict__).encode(),
            headers={"Authorization": "Bearer " + _config.get("api_key", "")},
        )
        urllib.request.urlopen(req, timeout=_config.get("timeout", 30))
        self.status = "submitted"


def load_order_template(path):
    """Load a reusable order template from a .ordertpl file.

    Format (one directive per line):
        # comment
        customer cus_9d2f
        item SKU-1417 2
        ship express
    """
    order = Order()
    for line in open(path):
        parts = line.strip().split()
        if not parts or parts[0].startswith("#"):
            continue
        if parts[0] == "item":
            order.items.append((parts[1], int(parts[2])))
        elif parts[0] == "customer":
            order.customer_id = parts[1]
        elif parts[0] == "ship":
            order.shipping = parts[1]
    return order
