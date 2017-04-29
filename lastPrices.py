import ast
import json
import datetime
import time
from poloniex import Poloniex
from pymongo import MongoClient
from myConnection import getConn

polCon =  getConn()

client = MongoClient('mongodb://localhost:27017')

currHour = time.strftime("%Y/%m/%d %H")
currMin = time.strftime("%M")
db = client.ticker_db

polTickers = polCon.returnTicker()
tickPairKeys = polTickers.keys()

for potentialTick in db.potentials.find():
    lastPrice = polTickers[potentialTick['tick']]
    if (potentialTick['triggerFlag'] and lastPrice >= potentialTick['trigger'] and potentialTick['direction'] == 'buy'):
        print "Buy %s lastPrice: %f and trigger: %f" % (potentialTick['tick'], float(lastPrice), potentialTick['trigger'])
    if (potentialTick['triggerFlag'] and lastPrice <= potentialTick['trigger'] and potentialTick['direction'] == 'sell'):
        print "Sell %s lastPrice: %f and trigger: %f" % (potentialTick['tick'], float(lastPrice), potentialTick['trigger'])

