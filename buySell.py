import time
from pymongo import MongoClient
from myConnection import getConn
from loadBalance import getTotalBTC

polCon = getConn()

client = MongoClient('mongodb://localhost:27017')

currHour = time.strftime("%Y/%m/%d %H")
currMin = time.strftime("%M")
db = client.ticker_db


# Step 1, decide on max BTC we are prepated to spend
# May depend on coin in question, if we already have that coin, how much BTC we have left, what else?
# For now, let's use 0.01 BTC (10 USD)
btcToSpend = 0.01

# Step 2, calculate if we have enough BTC
totalBTC = float(getTotalBTC())
print "-----------------------------"
print
print "Total BTC: %s" % totalBTC
print

# Step 3, calculate the amount of coin to buy corresponding to our BTC spend and buy
def buy(coin):
    myTickPrices = polCon.returnTicker()
    myCoinPair = 'BTC_' + coin
    coinPriceTick = myTickPrices[myCoinPair]
    coinPrice = coinPriceTick['last']
    noOfCoinsToBuy = round(btcToSpend / coinPrice)
    if ( noOfCoinsToBuy * coinPrice < totalBTC ):
        print "Buy %d of %s" % (noOfCoinsToBuy, myCoinPair)
        rate = 0
        # DO NOT USE THIS UNTIL SURE
        #polCon.buy(myCoinPair,rate,noOfCoinsToBuy)
    else:
        print "Not enough BTC, need %d, have only %d" % (noOfCoinsToBuy*coinPrice, totalBTC)

# Test buy of GNT

polTickers = polCon.returnTicker()
last = float(polTickers['BTC_GNT']['last'])
lowestAsk = float(polTickers['BTC_GNT']['lowestAsk'])
highestBid = float(polTickers['BTC_GNT']['highestBid'])


tickPair = 'BTC_GNO'
#lowestAsk = 0.0001334
btcAmount = 5

print "Checking for %s..." % tickPair
print

if  tickPair in polTickers:
    last = float(polTickers[tickPair]['last'])
    lowestAsk = float(polTickers[tickPair]['lowestAsk'])
    highestBid = float(polTickers[tickPair]['highestBid'])
    print "%s last: %.10f, lowestAsk: %.10f, highestBid: %.10f" % (tickPair, last, lowestAsk, highestBid)
    print
    print "Gonna try and buy %s at %.10f!" % (tickPair,lowestAsk)
    print
    amount = str(btcAmount/lowestAsk)
    lowestAskStr = str(lowestAsk)
    if totalBTC > btcAmount and lowestAsk < 0.15:
        polCon.buy(tickPair, lowestAskStr, amount)
        print "Just sent Buy request for %s at %s" % (tickPair, lowestAskStr)
        print
    else:
        print "Not enough BTC"
        print
else:
    print "Tick not available"
    print

