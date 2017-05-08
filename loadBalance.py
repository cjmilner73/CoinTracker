import time
from poloniex import Poloniex
from pymongo import MongoClient
from myConnection import getConn

polCon =  getConn()

client = MongoClient('mongodb://localhost:27017')

currTime = time.strftime("%Y/%m/%d %H:%M:%S")

db = client.ticker_db

# Remove when happy
db.balances.remove({})

polBal = polCon.returnBalances()

polTickers = polCon.returnTicker()
tickPairKeys = polTickers.keys()

def loadTotalAltInBTC():
    total = 0

    myBalance = {}

    for balTicker, balValue  in polBal.iteritems():
        for tickerPair, price in polTickers.iteritems():
            btcKey = 'BTC_' + balTicker
            if tickerPair == btcKey:
                floatBalValue = float(balValue)
                myBalance[balTicker] = floatBalValue
                total += float(price['last']) * floatBalValue

        myBalance['timestamp'] = currTime
        myBalance['totalBTC'] = total

        db.balances.insert(myBalance)

def getTotalBTC():
    myBalance = {}
    for balTicker, balValue in polBal.iteritems():
        if balTicker == 'BTC':
            btcBalance = balValue
    return btcBalance
