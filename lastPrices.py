import ast
import json
import datetime
import time
import adx
from poloniex import Poloniex
from pymongo import MongoClient
from bson import ObjectId


polCon =  Poloniex("AQKCQME8-FA6XJ0XX-Z81BZC8N-ARJV85F9","b607e01152b255a4d1da89e01c5fd7cd6c8d5784db5c4c369875c1d48cea5b9cd1c26cffa5122bc43b293df12e04f2adeae10847190abaaf21963331838893e8")

client = MongoClient('mongodb://localhost:27017')

currHour = time.strftime("%Y/%m/%d %H")
currMin = time.strftime("%M")
db = client.ticker_db

polTickers = polCon.returnTicker()
tickPairKeys = polTickers.keys()

for keyPair in tickPairKeys:
    potentialTicks = db.potentials.find()
    for p in potentialTicks:
        if p['tick'] == keyPair:
            lastPrice = polTickers[keyPair]['last']
            if 'trigger' in p:
                if p['direction'] == 'buy':
                    print "Buy %s lastPrice: %f and trigger: %f" % (keyPair, float(lastPrice), p['trigger'])


