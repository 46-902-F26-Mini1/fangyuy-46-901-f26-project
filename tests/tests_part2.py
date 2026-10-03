# Part 2 starter tests.
# Run:  python tests_part2.py

from main import (
    Order,
    OrderBook,
    Exchange,
    TradingBot,
    HardcodedBot,
    BUY,
    SELL,
)


def almostEqual(d1, d2, epsilon=10**-6):
    return abs(d2 - d1) < epsilon


def buyOrder(price, quantity, time, base="USD", quote="EUR"):
    return Order(base, quote, BUY, price, quantity, time)


def sellOrder(price, quantity, time, base="USD", quote="EUR"):
    return Order(base, quote, SELL, price, quantity, time)


def zeroPositions(**overrides):
    positions = {"USD": 0, "EUR": 0, "JPY": 0, "GBP": 0, "AUD": 0}
    positions.update(overrides)
    return positions


def positionsEqual(actual, expected):
    return actual.keys() == expected.keys() and all(
        almostEqual(actual[c], expected[c]) for c in expected
    )


### Exchange


def testSingleOrderRests():
    print("Testing a single order rests in its book...", end="")
    buy = buyOrder(0.85, 10, 0)
    exchange = Exchange()
    exchange.addTrader(HardcodedBot([[buy]]))
    exchange.performTradingRound()
    book = exchange.orderBooks[("USD", "EUR")]
    assert book.bids.size() == 1
    assert book.bids.peek() is buy
    assert book.asks.isEmpty()
    print("Passed!")


def testMatchingOrdersFill():
    print("Testing matching orders from two traders...", end="")
    buy = buyOrder(0.85, 5, 0)
    sell = sellOrder(0.85, 5, 0)
    buyer = HardcodedBot([[buy]])
    seller = HardcodedBot([[sell]])
    exchange = Exchange()
    exchange.addTrader(buyer)
    exchange.addTrader(seller)
    exchange.performTradingRound()
    # both orders are completely filled with nothing left over: the buyer gets
    # 5 USD for 5 * 0.85 = 4.25 EUR
    assert buy.quantity == 0 and sell.quantity == 0
    assert positionsEqual(buyer.positions, zeroPositions(USD=5, EUR=-4.25))
    assert positionsEqual(seller.positions, zeroPositions(USD=-5, EUR=4.25))
    print("Passed!")


def testPartialFillCompletesLater():
    print("Testing a partial fill completed in a later round...", end="")
    buy = buyOrder(0.85, 10, 0)
    sell1 = sellOrder(0.85, 5, 0)
    sell2 = sellOrder(0.85, 5, 1)
    buyer = HardcodedBot([[buy], []])
    seller = HardcodedBot([[sell1], [sell2]])
    exchange = Exchange()
    exchange.addTrader(buyer)
    exchange.addTrader(seller)
    exchange.performTradingRound()
    assert buy.quantity == 5  # still partially unfilled
    assert sell1.quantity == 0
    assert positionsEqual(buyer.positions, zeroPositions(USD=5, EUR=-4.25))
    assert positionsEqual(seller.positions, zeroPositions(USD=-5, EUR=4.25))

    # the buy is still in the book, so the next sell completes it
    exchange.performTradingRound()
    assert buy.quantity == 0
    assert sell2.quantity == 0
    assert positionsEqual(buyer.positions, zeroPositions(USD=10, EUR=-8.5))
    assert positionsEqual(seller.positions, zeroPositions(USD=-10, EUR=8.5))
    print("Passed!")


def testPriceMismatchMeansNoFills():
    print("Testing orders that don't cross...", end="")
    buy = buyOrder(0.85, 5, 0)
    sell = sellOrder(3, 5, 0)
    exchange = Exchange()
    exchange.addTrader(HardcodedBot([[buy]]))
    exchange.addTrader(HardcodedBot([[sell]]))
    exchange.performTradingRound()
    # both orders are still sitting in the book because nothing matches
    book = exchange.orderBooks[("USD", "EUR")]
    assert book.bids.size() == 1 and book.asks.size() == 1
    assert buy.quantity == 5 and sell.quantity == 5
    assert buy.fills == [] and sell.fills == []
    print("Passed!")


def testBetterPriceFirst():
    print("Testing the better price fills first...", end="")
    sell1 = sellOrder(0.85, 5, 0)
    sell2 = sellOrder(0.75, 5, 0)
    buy = buyOrder(0.85, 5, 1)
    seller = HardcodedBot([[sell1, sell2]])
    buyer = HardcodedBot([[], [buy]])
    exchange = Exchange()
    exchange.addTrader(seller)
    exchange.addTrader(buyer)
    exchange.performTradingRound()
    exchange.performTradingRound()
    # the buy matches the cheaper sell2, paying 5 * 0.75 = 3.75 EUR
    assert sell2.quantity == 0
    assert buy.quantity == 0
    assert sell1.quantity == 5
    assert positionsEqual(buyer.positions, zeroPositions(USD=5, EUR=-3.75))
    print("Passed!")


def testFirstComeFirstServed():
    print("Testing first come, first served at the same price...", end="")
    sell1 = sellOrder(0.85, 5, 0)
    sell2 = sellOrder(0.85, 5, 1)
    buy = buyOrder(0.85, 7, 1)
    exchange = Exchange()
    exchange.addTrader(HardcodedBot([[sell1], [sell2, buy]]))
    exchange.performTradingRound()
    exchange.performTradingRound()
    assert sell1.quantity == 0  # filled first
    assert sell2.quantity == 3  # and then partially filled
    assert buy.quantity == 0
    print("Passed!")


def testDifferentPairsNeverMatch():
    print("Testing different pairs never match...", end="")
    sell = sellOrder(0.85, 5, 0, "USD", "EUR")
    buy = buyOrder(0.85, 7, 1, "USD", "JPY")
    exchange = Exchange()
    exchange.addTrader(HardcodedBot([[sell], [buy]]))
    exchange.performTradingRound()
    exchange.performTradingRound()
    assert sell.quantity == 5 and buy.quantity == 7
    assert sell.fills == [] and buy.fills == []
    assert exchange.orderBooks[("USD", "EUR")].asks.peek() is sell
    assert exchange.orderBooks[("USD", "JPY")].bids.peek() is buy
    print("Passed!")


def testRoundCounterAdvances():
    print("Testing the round counter...", end="")
    exchange = Exchange()
    assert exchange.tradingRound == 0
    exchange.performTradingRound()  # a round with no traders still counts
    assert exchange.tradingRound == 1
    exchange.addTrader(TradingBot())
    exchange.performTradingRound()
    exchange.performTradingRound()
    assert exchange.tradingRound == 3
    print("Passed!")


### Positions


def testBuyFillUpdatesPositions():
    # buying 10 USD/JPY at 5: +10 USD, and 10 * 5 = 50 JPY paid for it
    print("Testing positions after a buy fill...", end="")
    bot = TradingBot()
    order = buyOrder(5, 10, 0, "USD", "JPY")
    order.quantity = 0
    order.fills = [(10, 5)]
    bot.orders = [order]
    bot.handleFilledOrders()
    assert positionsEqual(bot.positions, zeroPositions(USD=10, JPY=-50))
    print("Passed!")


def testSellFillUpdatesPositions():
    print("Testing positions after a sell fill...", end="")
    bot = TradingBot()
    order = sellOrder(5, 10, 0, "USD", "JPY")
    order.quantity = 0
    order.fills = [(10, 5)]
    bot.orders = [order]
    bot.handleFilledOrders()
    assert positionsEqual(bot.positions, zeroPositions(USD=-10, JPY=50))
    print("Passed!")


def testFilledOrderIsDropped():
    # a completely filled order is removed; a partially filled one stays
    print("Testing filled orders are dropped...", end="")
    bot = TradingBot()
    filled = sellOrder(1.00, 2, 0)
    filled.fills = [(2, 1.00)]
    filled.quantity = 0
    partial = sellOrder(1.00, 4, 1)
    partial.fills = [(3, 1.00)]
    partial.quantity = 1
    bot.orders = [filled, partial]
    bot.handleFilledOrders()
    assert bot.orders == [partial]
    assert positionsEqual(bot.positions, zeroPositions(USD=-5, EUR=5))
    print("Passed!")


### Conversion rate and USD value


def testConversionRateIsTheMidpoint():
    print("Testing the conversion rate...", end="")
    book = OrderBook()
    book.processOrder(buyOrder(0.80, 10, 0))
    book.processOrder(sellOrder(0.90, 10, 1))
    assert almostEqual(TradingBot.getConversionRateToUSD(book), 0.85)
    print("Passed!")


def testConversionRateOfAnEmptyBook():
    print("Testing the conversion rate of an empty book...", end="")
    assert TradingBot.getConversionRateToUSD(OrderBook()) == None
    print("Passed!")


def testUSDValueOfUSD():
    print("Testing the USD value of USD...", end="")
    bot = TradingBot()
    bot.positions["USD"] = 100
    assert almostEqual(bot.calculateUSDValue(Exchange().orderBooks), 100)
    print("Passed!")


def testUSDValueConvertsOtherCurrencies():
    # 50 EUR at 0.8 EUR per USD is worth 50 / 0.8 = 62.5 USD
    print("Testing the USD value of EUR...", end="")
    exchange = Exchange()
    exchange.orderBooks[("USD", "EUR")].processOrder(sellOrder(0.8, 10, 0))
    bot = TradingBot()
    bot.positions["EUR"] = 50
    bot.positions["USD"] = 100
    assert almostEqual(bot.calculateUSDValue(exchange.orderBooks), 162.5)
    print("Passed!")


def testUSDValueWithoutARate():
    print("Testing the USD value without a conversion rate...", end="")
    bot = TradingBot()
    bot.positions["EUR"] = 50
    assert bot.calculateUSDValue(Exchange().orderBooks) == None
    print("Passed!")


def testAll():
    testSingleOrderRests()
    testMatchingOrdersFill()
    testPartialFillCompletesLater()
    testPriceMismatchMeansNoFills()
    testBetterPriceFirst()
    testFirstComeFirstServed()
    testDifferentPairsNeverMatch()
    testRoundCounterAdvances()
    testBuyFillUpdatesPositions()
    testSellFillUpdatesPositions()
    testFilledOrderIsDropped()
    testConversionRateIsTheMidpoint()
    testConversionRateOfAnEmptyBook()
    testUSDValueOfUSD()
    testUSDValueConvertsOtherCurrencies()
    testUSDValueWithoutARate()
    print("All Part 2 starter tests passed!")


if __name__ == "__main__":
    testAll()