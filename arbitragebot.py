from traders import *
from orders import *
import math



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
        if not negCycle:
           return []
        currentQuantity = ArbitrageBot.getInitialTradeQuantity(negCycle, orderBooks)
        tradeCycle = list(reversed(negCycle))
        newOrders = []

        for i in range(len(tradeCycle)-1):
            currentCurrency = tradeCycle[i]
            nextCurrency = tradeCycle[i + 1]
            if (currentCurrency, nextCurrency) in orderBooks:
                orderBook = orderBooks[(currentCurrency, nextCurrency)]

                marketOrder = orderBook.bids.peek()
                tradePrice = marketOrder.price

                newOrder = Order(
                    currentCurrency,     # base
                    nextCurrency,        # quote
                    SELL,
                    tradePrice,
                    currentQuantity,     # quantity is measured in base
                    tradingRound
                )

                newOrders.append(newOrder)

                currentQuantity *= tradePrice
            else:
                orderBook = orderBooks[(nextCurrency, currentCurrency)]
                marketOrder = orderBook.asks.peek()
                tradePrice = marketOrder.price
                baseQuantity = currentQuantity / tradePrice
                newOrder = Order(
                    nextCurrency,      
                    currentCurrency,  
                    BUY,
                    tradePrice,
                    baseQuantity,    
                    tradingRound
                )
                newOrders.append(newOrder)
                
                currentQuantity = baseQuantity
        return newOrders


        

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
        if not negCycle:
           return 0

        currentQuantity = float("inf")

        for i in range(len(negCycle)-1):
            currentCurrency = negCycle[i]
            nectCurrency = negCycle[i+1]
            if (currentCurrency, nectCurrency) in orderBooks:
               orderBook = orderBooks[(currentCurrency, nectCurrency)]

               marketOrder = orderBook.asks.peek()
               maxAvailable = marketOrder.quantity
               currentQuantity = min(currentQuantity, maxAvailable)

               currentQuantity *= marketOrder.price
            else:
                orderBook = orderBooks[(nectCurrency, currentCurrency)]
              
                marketOrder = orderBook.bids.peek()
                maxAvailable = marketOrder.quantity * marketOrder.price
                currentQuantity = min(currentQuantity, maxAvailable)
    
                currentQuantity /= marketOrder.price

        return currentQuantity


  
    def placeOrders(self, orderBooks, tradingRound):
        self.handleFilledOrders()

        negCycle = self.findNegativeCycle(orderBooks)
        newOrders = self.getOrdersFromCycle(negCycle, orderBooks, tradingRound)
        self.orders.extend(newOrders)

        return newOrders

    @staticmethod
    def buildExchangeGraph(orderBooks):
        currencies = set()
        edges = []

        for (base, quote), orderBook in orderBooks.items():
            currencies.add(base)
            currencies.add(quote)


            if not orderBook.asks.isEmpty():
                bestAsk = orderBook.asks.peek()
                rate = bestAsk.price
                weight = math.log(rate)

                edges.append(
                    (base, quote, weight)
                )

            # A BUY order follows:
            # quote -> base
            if not orderBook.bids.isEmpty():
                bestBid = orderBook.bids.peek()
                rate = 1 / bestBid.price
                weight = math.log(rate)

                edges.append(
                    (quote, base, weight)
                )

        return list(currencies), edges
        
    @staticmethod
    def findNegativeCycle(orderBooks):
        currencies, edges = ArbitrageBot.buildExchangeGraph(orderBooks)

        if len(currencies) == 0:
            return None

        # Set every distance to 0 so that negative cycles
        # anywhere in the graph can be detected.
        ## 以currency为终点的dis的最小值
        distance = {currency: 0 for currency in currencies}
        predecessor = {currency: None for currency in currencies}
        numberOfCurrencies = len(currencies)

        # Perform V - 1 rounds of relaxation.
        for _ in range(numberOfCurrencies - 1):
            changed = False

            for start, end, weight in edges:
                newDistance = distance[start] + weight

                if newDistance < distance[end]:
                    distance[end] = newDistance
                    predecessor[end] = start
                    changed = True

            # If nothing changed, all distances are already stable.
            if not changed:
                return None

        # One additional round:
        # if an edge can still be relaxed, a negative cycle exists.
        cycleVertex = None

        for start, end, weight in edges:
            newDistance = distance[start] + weight

            if newDistance < distance[end]:
                distance[end] = newDistance
                predecessor[end] = start
                cycleVertex = end

        # No edge changed during the extra round.
        if cycleVertex is None:
            return None

        # Following predecessors V times guarantees that we enter the cycle.
        for _ in range(numberOfCurrencies):
            cycleVertex = predecessor[cycleVertex]

        # Reconstruct the cycle by following predecessor links.
        negCycle = [cycleVertex]

        current = predecessor[cycleVertex]

        while current != cycleVertex:
            negCycle.append(current)
            current = predecessor[current]

        # Repeat the starting currency at the end.
        negCycle.append(cycleVertex)

        # Predecessors point backward, so reverse the result.
        negCycle.reverse()

        return negCycle
