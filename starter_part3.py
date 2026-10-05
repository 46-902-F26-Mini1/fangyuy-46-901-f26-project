class ArbitrageBot(TradingBot):
  """A trading bot that detects arbitrages by finding negative weight cycles in the exchange graph.

    Each round, the bot looks at the best order on each side of every order
    book. If those prices form an arbitrage, it trades one arbitrage cycle,
    taking as much as the best orders on the cycle allow, so every order it
    places fills straight away. Its profit for the round then ends up in a
    single currency, with every other currency back where it started. If there
    is no arbitrage, it places no orders.
    """

    @staticmethod
    def getOrdersFromCycle(negCycle, orderBooks, tradingRound):
        """Gets a list of orders to place to take advantage of the arbitrage formed by negCycle

        Args:
            negCycle: A list representing a cycle of currencies that create an
                arbitrage, or None if there is no arbitrage. The first and last
                elements of the list are the same. The list is ordered based on
                orders in the market, so orders placed will go in the reverse
                order.
            orderBooks: A dictionary mapping currency pairs to order books for
                the orders currently in the exchange
            tradingRound: An integer representing the current trading round.

        Returns:
            A list of orders to place that make money by taking advantage of the
            arbitrage in negCycle, or an empty list if negCycle is None.
        """
        pass

    @staticmethod
    def getInitialTradeQuantity(negCycle, orderBooks):
        """Gets the amount of the first currency to start trading so no orders go over the quantity available.

        To find the quantity we can trade, we start with the most of the first
        currency that the first order in the cycle can take. An order's quantity
        is in its base currency, so if the first currency is that order's quote,
        convert the order's quantity into the first currency. Then determine the
        quantity that would turn into for each currency around the cycle. If at
        any point, we'd need more than is available in the corresponding order,
        we just trade what's available in the order.

        Args:
            negCycle: A list of currencies that form a negative cycle in the
                exchange. Starts and ends with the same value.
            orderBooks: A dictionary mapping currency pairs to order books for
                the orders currently in the exchange

        Returns:
            The amount of the first currency to start trading so no orders go
            over the quantity available for that specific order.
        """
        pass

    def placeOrders(self, orderBooks, tradingRound):
        pass