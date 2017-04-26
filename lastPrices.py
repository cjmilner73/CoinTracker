import ast
import json
import datetime
import time
import adx
from poloniex import Poloniex
from pymongo import MongoClient
from create_new_document import insert_new_doc 
from bson import ObjectId


polCon =  Poloniex("AQKCQME8-FA6XJ0XX-Z81BZC8N-ARJV85F9","b607e01152b255a4d1da89e01c5fd7cd6c8d5784db5c4c369875c1d48cea5b9cd1c26cffa5122bc43b293df12e04f2adeae10847190abaaf21963331838893e8")

client = MongoClient('mongodb://localhost:27017')

currHour = time.strftime("%Y/%m/%d %H")
currMin = time.strftime("%M")
db = client.ticker_db

polTickers = polCon.returnTicker()
print polTickers
tickPairKeys = polTickers.keys()

def getLatestHourFromDB():
    lastDoc = db.tickPrice.find({}).sort([('_id', -1)]).limit(1)
    lastH = 'Dummy'
    for n in lastDoc:
	lastH =  n['timestamp_minute']
    return lastH

lastHour = getLatestHourFromDB()

if lastHour != currHour:
    for keyPair in tickPairKeys:
        insert_new_doc(keyPair,currHour)


for keyPair in tickPairKeys:
    lastPrice = polTickers[keyPair]['last']
    lowestAsk = polTickers[keyPair]['lowestAsk']
    highestBid = polTickers[keyPair]['highestBid']
    setLast = {}
    setLow = {}
    setHigh = {}
    setLast['last.' + currMin] = lastPrice
    setLow['low.' + currMin] = lowestAsk
    setHigh['high.' + currMin] = highestBid
    db.tickPrice.update({'timestamp_minute': currHour, 'tick': keyPair }, {'$set': setLast }, upsert=False)
    db.tickPrice.update({'timestamp_minute': currHour, 'tick': keyPair }, {'$set': setLow }, upsert=False)
    db.tickPrice.update({'timestamp_minute': currHour, 'tick': keyPair }, {'$set': setHigh }, upsert=False)
    print "Updated minute " + currMin + " for hour " + currHour + " and " + keyPair + " with last: " + lastPrice
    print "Updated minute " + currMin + " for hour " + currHour + " and " + keyPair + " with low: " + highestBid
    print "Updated minute " + currMin + " for hour " + currHour + " and " + keyPair + " with high: " + lowestAsk

#price = db.tickPrice.find_one( {'_id': ObjectId('58fe2cc4df58732f15428c99')} )

