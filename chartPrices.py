import collections
import ast
import json
import datetime
import time
import calendar
import adx
from poloniex import Poloniex
from pymongo import MongoClient
from create_new_document import insert_new_last 
#from create_new_document import insert_new_chart
from bson import ObjectId
from random import randint

polCon =  Poloniex("AQKCQME8-FA6XJ0XX-Z81BZC8N-ARJV85F9","b607e01152b255a4d1da89e01c5fd7cd6c8d5784db5c4c369875c1d48cea5b9cd1c26cffa5122bc43b293df12e04f2adeae10847190abaaf21963331838893e8")

client = MongoClient('mongodb://localhost:27017')

currHour = time.strftime("%Y/%m/%d %H")
currMin = time.strftime("%M")

monthInSeconds = 2592000
twoMonthsInSeconds = 2592000*2
threeMonthsInSeconds = 2592000*3
fourHours = 14400

startEpoch = threeMonthsInSeconds
tickPeriod = fourHours

days_to_subtract = 1
nowTimeEpoch = calendar.timegm(time.gmtime())
yesterdayTimeEpoch = nowTimeEpoch - startEpoch

db = client.ticker_db

polTicker = polCon.returnTicker()

tickPairKeys = polTicker.keys()

db.tickChart.remove({})
db.adxResults.remove({})

for keyPair in tickPairKeys:
    print "Loading " + keyPair
    polChart = polCon.returnChartData(keyPair,tickPeriod, yesterdayTimeEpoch, nowTimeEpoch)
    for tickSticks in polChart['candleStick']:
       high = tickSticks['high']
       low = tickSticks['low']
       epochTime = tickSticks['date']
       close = tickSticks['close']
       open = tickSticks['open']
       db.tickChart.insert_one({'tick': keyPair, 'high': high, 'low': low, 'time': epochTime, 'close': close, 'open': open})

class Student(object):
    ndx = "BTC"

    #container to count the number of event windows we have cycled through
    ticks = 0

    #Wilder uses a rolling window of 14 days for various smoothing within
    #the indicator calculation
    window_length = 14

    #a collection of data containers that will be used during steps of the calculation
    highs = []
    lows = []
    closes = []
    true_range_bucket = []
    pDM_bucket = []
    mDM_bucket = []
    dx_bucket = []

    #not sure why I had to define these here, but to print them later when debuggin
    #I found that I had to declare them here
    av_true_range = 0
    av_pDM = 0
    av_mDM = 0
    di_diff = 0
    di_sum = 0
    dx = 0


class Btc_usdt(object):
    high = 0
    low = 0 
    close = 0

s = Student();
b = Btc_usdt()

adx.initialize(s)

for thisTick in tickPairKeys:
    for prices in db.tickChart.find({'tick': thisTick}):
        b.high = prices['high']
        b.low = prices['low']
        b.close = prices['close']
        thisTime = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(prices['time']))
        thisAdxVals = adx.handle_data(s,b)
        thisADX = thisAdxVals[0]
        thisPDI = thisAdxVals[1]
        thisMDI = thisAdxVals[2]
        db.adxResults.insert_one({'time': thisTime, 'tick': thisTick, 'adx': thisADX, 'pdi': thisPDI, 'mdi': thisMDI})

# Adding comment for git test
