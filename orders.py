from fc_utils import PQ

################################################################################
# Order
################################################################################

BUY = 'Buy'
SELL = 'Sell'

class Order:
    """An order to buy/sell a currency pair"""

    def __init__(self, base, quote, direction, price, quantity, time):
        """
        Initializes an order

        Args:
            base: The base currency
            quote: The quote currency
            direction: The direction (BUY or SELL)
            price: The price (amount of quote currency) for 1 unit of base currency
            quantity: The amount of the base currency to buy/sell
            time: The time the order was made

        Other Properties:
            fills: A list of (quantity, price) tuples representing amount 
                filled and the price it was filled at. This is a list
                because an order can be filled by multiple different orders
                at different prices, so we need to track all of them.
        """
        self.base = base
        self.quote = quote
        self.direction = direction
        self.price = price
        self.quantity = quantity
        self.time = time
        self.fills = []
    
    def __repr__(self):
        return f"Order(base: {self.base}, quote: {self.quote}, direction: {self.direction}, price: {self.price}, quantity: {self.quantity}, time: {self.time})"

    def almostEqual(x, y):
        return abs(x - y) <= 0.01
        
    def __eq__(self, other):
        return (
            isinstance(other, Order)
            and self.base == other.base
            and self.quote == other.quote
            and self.direction == other.direction
            and self.almostEqual(self.price, other.price)
            and self.almostEqual(self.quantity, other.quantity)
            and self.time == other.time
        )

    def __hash__(self):
        return hash((self.base, self.quote, self.direction, self.time))

################################################################################
# OrderBook
################################################################################

class OrderBook:
    """An order book for one currency pair"""

    def __init__(self):
        """
        Initializes an order book for a single currency pair.
        
        Stores both buy and sell orders that are pending fulfillment for the 
        currency pair. Stored to allow fast matching, prioritizing who is
        fulfilling the order. i.e.
        - Sellers will match with the buyer willing to pay the highest price
        - Buyers will match with sellers who want the lowest price
        - When tied, the earlier order is prioritized

        Properties:
            bids: The BUY orders that have yet to be fulfilled
            asks: The SELL orders that have yet to be fulfilled
        """
        self.bids = PQ(key=lambda order: (-order.price, order.time))
        self.asks = PQ(key=lambda order: (order.price, order.time))
    
    def __repr__(self):
        return f"OrderBook(bids: {self.bids}, asks: {self.asks})"

    def processOrder(self, order):
        """
        Updates the order book based on the order given.

        If the order can be fulfilled, it is fulfilled starting with the best
        offer currently available. The order given can be fully, partially,
        or not fulfilled. If not completely fulfilled, it is added to orders
        pending fulfillment. 
        
        Any orders filled (completely or partially) will have their quantity
        updated. They will also have a tuple (quantity, price) added to their
        list of fills.

        Args:
            order: The new order to fill.
        """
        ## BUY
        if order.direction == BUY:
            while (not self.asks.isEmpty()
                    and order.price >= self.asks.peek().price 
                    and order.quantity > 0):
                
                beforeOrder = self.asks.pop()

                self._fillOrders(order, beforeOrder)

                if beforeOrder.quantity > 0:
                    self.asks.push(beforeOrder)
            if order.quantity > 0:
                self.bids.push(order)

        ## SELL
        elif order.direction == SELL:
            while (not self.bids.isEmpty()
                and order.price <= self.bids.peek().price
                and order.quantity > 0):

                beforeOrder = self.bids.pop()

                self._fillOrders(order, beforeOrder)

                if beforeOrder.quantity > 0:
                    self.bids.push(beforeOrder)

            if order.quantity > 0:
                self.asks.push(order)

    def _fillOrders(self, order, beforeOrder):
        """Match quantities and record the fill for both orders."""
        dealPrice = beforeOrder.price
        dealQuantity = min(beforeOrder.quantity, order.quantity)

        beforeOrder.fills.append((dealQuantity, dealPrice))
        order.fills.append((dealQuantity, dealPrice))

        beforeOrder.quantity -= dealQuantity
        order.quantity -= dealQuantity
