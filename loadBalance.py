import json
import datetime
import time
import calendar
import adx
from poloniex import Poloniex
from pymongo import MongoClient
from bson import ObjectId

polCon =  Poloniex("AQKCQME8-FA6XJ0XX-Z81BZC8N-ARJV85F9","b607e01152b255a4d1da89e01c5fd7cd6c8d5784db5c4c369875c1d48cea5b9cd1c26cffa5122bc43b293df12e04f2adeae10847190abaaf21963331838893e8")

client = MongoClient('mongodb://localhost:27017')

currTime = time.strftime("%Y/%m/%d %H:%M:%S")

db = client.ticker_db

polBal = polCon.returnBalances()


polTickers = polCon.returnTicker()
tickPairKeys = polTickers.keys()

total = 0

myBalance = {}

for balTicker, balValue  in polBal.iteritems():
   for tickerPair, price in polTickers.iteritems():
      btcKey = 'BTC_' + balTicker
      #if (tickerPair == btcKey) or (balTicker == 'USDT'):
      if (tickerPair == btcKey):
          floatBalValue = float(balValue)
          if ( floatBalValue != 0):
               myBalance[btcKey] = floatBalValue
               total += float(price['last']) * floatBalValue

myBalance['timestamp'] = currTime
myBalance['totalBTC'] = total
print total
print polTickers['USDT_BTC']['last']
print float(polBal['USDT'])
myBalance['totalUSD'] = float(polBal['USDT']) + (total * float(polTickers['USDT_BTC']['last']))

db.balances.insert(myBalance)
print myBalance['totalUSD']
