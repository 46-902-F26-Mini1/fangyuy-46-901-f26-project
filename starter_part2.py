################################################################################
# Exchange
################################################################################
from orders import OrderBook, BUY, SELL

class Exchange:
    """A currency exchange"""

    def __init__(self):
        """Initializes a currency exchange

        Properties:
            orderBooks: A dictionary mapping currency pairs to order books
            tradingRound: An integer representing the current trading round
            traders: A list of trading bots that will place orders
        """
        self.orderBooks = {
            ('USD', 'EUR'): OrderBook(),
            ('USD', 'JPY'): OrderBook(),
            ('USD', 'GBP'): OrderBook(),
            ('USD', 'AUD'): OrderBook(),
            ('EUR', 'JPY'): OrderBook(),
            ('EUR', 'GBP'): OrderBook(),
            ('EUR', 'AUD'): OrderBook(),
            ('JPY', 'GBP'): OrderBook(),
            ('JPY', 'AUD'): OrderBook(),
            ('GBP', 'AUD'): OrderBook()
        }
        self.tradingRound = 0
        self.traders = []

    def addTrader(self, trader):
        """Adds a trader to the exchange. This trader should be at the end of the list.

        Args:
            trader: The trader to add
        """
        self.traders.append(trader)

    def performTradingRound(self):
        """Performs one trading round by gathering and processing orders from each trader.

        For now, loop through the traders in order and let them place orders.
        Later, we will randomize the order every round for fairness.
        """
        for trader in self.traders:
            newOrders = trader.placeOrders(self.orderBooks, self.tradingRound)

            for order in newOrders:
                pair = (order.base, order.quote)
                self.orderBooks[pair].processOrder(order)

        for trader in self.traders:
            trader.handleFilledOrders()

        self.tradingRound += 1
        
################################################################################
# Trading Bots
################################################################################

class TradingBot:
    """A trading bot. General trading bots do not place any orders.

    This class will be subclassed to implement different bot types.
    """

    def __init__(self):
        """Initializes a trading bot.

        Properties:
            positions: a dictionary mapping currencies to quantities held.
            orders: a list of outstanding orders that have been placed.
        """
        self.positions = {
            'USD': 0,
            'EUR': 0,
            'JPY': 0,
            'GBP': 0,
            'AUD': 0
        }
        self.orders = []
        self.processedFills = {}

    def placeOrders(self, orderBooks, tradingRound):
        """Returns a list of orders to place based on the current state of the exchange.

        Starts by calling handleFilledOrders to update positions based on any
        orders that have been filled (i.e. if other bots placed orders that
        caused this bot's pending orders to be partially or fully filled).
        Updates the self.orders list with new orders placed, and returns a list
        of the new orders so the exchange can process them.

        Args:
            orderBooks: A dictionary mapping currency pairs to order books
                containing all pending orders in the exchange.
            tradingRound: An integer representing the current trading round (how
                we represent time).

        Returns:
            A list of orders to place in the exchange. These orders are also
            added to the self.orders list so the bot can track the orders filled
            later.
        """
        self.handleFilledOrders()
        return []

    def handleFilledOrders(self):
        """Updates positions based on fills from the existing orders.

        If an order is fully filled, it is removed from the list of orders.

        Positions are updated based on quantity and price filled. For example,
        if an order was filled to buy 10 (quantity) USD (base)/JPY (quote) for 5
        (price): USD increases by 10, but JPY decreases by 10 * 5 = 50 because
        each unit of USD was purchased with 5 JPY.
        """
        remainingOrders = []

        for order in self.orders:
            start = self.processedFills.get(order, 0)

            for quantity, price in order.fills[start:]:
                if order.direction == BUY:
                    self.positions[order.base] += quantity
                    self.positions[order.quote] -= quantity * price

                elif order.direction == SELL:
                    self.positions[order.base] -= quantity
                    self.positions[order.quote] += quantity * price

            if order.quantity > 0:
                remainingOrders.append(order)
                self.processedFills[order] = len(order.fills)
            else:
                self.processedFills.pop(order, None)

        self.orders = remainingOrders

    def calculateUSDValue(self, orderBooks):
        """Gets the estimated value of the trading bot's portfolio in USD.

        Args:
            orderBooks: A dictionary mapping currency pairs to order books
                containing all pending orders in the exchange. These are used to
                estimate the fair value of USD in terms of the other currencies
                being traded.

        Returns:
            The estimated value of the bot's portfolio in USD, or None if any of
            the order books are empty (in which case an estimated value cannot
            be determined).
        """
        totalValue = 0

        for currency, quantity in self.positions.items():
            if quantity == 0:
                continue

            if currency == 'USD':
                totalValue += quantity
            else:
                book = orderBooks[('USD', currency)]
                rate = self.getConversionRateToUSD(book)

                if rate is None:
                    return None

                totalValue += quantity / rate

        return totalValue

    @staticmethod
    def getConversionRateToUSD(orderBook):
        """Gets an estimated conversion rate to USD based on a specific order book.

        The bid/ask spread is the difference between prices of the best
        unfulfilled bid (buy) offer and the best unfulfilled ask (sell) offer.
        Taking the mean of these order prices gives a good estimate of what the
        currency is actually worth (ie the fair value). This is how we estimate
        the values of each currency to calculate the USD value.

        Args:
            orderBook: The order book to generate the conversion rate for.
                The base is guaranteed to be USD.

        Returns:
            The average of the best bid and ask prices, or None if the order book is empty.
        """
        bidsEmpty = orderBook.bids.isEmpty()
        asksEmpty = orderBook.asks.isEmpty()

        if bidsEmpty and asksEmpty:
            return None

        if bidsEmpty:
            return orderBook.asks.peek().price

        if asksEmpty:
            return orderBook.bids.peek().price

        bidPrice = orderBook.bids.peek().price
        askPrice = orderBook.asks.peek().price

        return (bidPrice + askPrice) / 2


########################################
class HardcodedBot(TradingBot):
    """A hardcoded trading bot for testing purposes. Has a set list of orders to place at each round."""

    def __init__(self, ordersToPlace):
        """Initializes a hardcoded trading bot

        Args:
            ordersToPlace: A 2D list of orders. Index i is a list of the orders
                to place at trading round i.
        """
        super().__init__()
        self.ordersToPlace = ordersToPlace

    def placeOrders(self, orderBooks, tradingRound):
        self.handleFilledOrders()

        if tradingRound >= len(self.ordersToPlace):
            return []

        newOrders = self.ordersToPlace[tradingRound]

        self.orders.extend(newOrders)

        return newOrders
