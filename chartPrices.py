import time
import calendar
import adx
from poloniex import Poloniex
from pymongo import MongoClient

polCon = Poloniex("AQKCQME8-FA6XJ0XX-Z81BZC8N-ARJV85F9","b607e01152b255a4d1da89e01c5fd7cd6c8d5784db5c4c369875c1d48cea5b9cd1c26cffa5122bc43b293df12e04f2adeae10847190abaaf21963331838893e8")

client = MongoClient('mongodb://localhost:27017')

currHour = time.strftime("%Y/%m/%d %H")
currMin = time.strftime("%M")

weekInSeconds = 604800
monthInSeconds = 2592000
twoMonthsInSeconds = 2592000*2
threeMonthsInSeconds = 2592000*3
fourHoursInSeconds = 14400
oneDayInSeconds = 86400

startEpoch = weekInSeconds
tickPeriod = fourHoursInSeconds

nowTimeEpoch = calendar.timegm(time.gmtime())
# endTimeEpoch = calendar.timegm(time.gmtime()) - (5 * tickPeriod)
endTimeEpoch = nowTimeEpoch
startTimeEpoch = endTimeEpoch  - startEpoch

db = client.ticker_db

polTicker = polCon.returnTicker()

tickPairKeys = polTicker.keys()

btcTickPairs = []
for tickPair in tickPairKeys:
    if tickPair.startswith("BTC"):
        btcTickPairs.append(tickPair)

db.tickChart.remove({})
db.adxResults.remove({})
db.tickChartLastFive.remove({})
db.potentials.remove({})

#btcTickPairs = ["BTC_POT"]

for keyPair in btcTickPairs:
    polChart = polCon.returnChartData(keyPair, tickPeriod, startTimeEpoch, endTimeEpoch)
    for tickSticks in polChart['candleStick']:
        high = tickSticks['high']
        low = tickSticks['low']
        epochTime = tickSticks['date']
        close = tickSticks['close']
        open = tickSticks['open']
        db.tickChart.insert_one({'tick': keyPair, 'high': high, 'low': low, 'time': epochTime, 'close': close, 'open': open})

class Initial(object):
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


class TickObj(object):
    high = 0
    low = 0 
    close = 0

s = Initial()
b = TickObj()


for thisTick in btcTickPairs:
    adx.initialize(s)
    for prices in db.tickChart.find({'tick': thisTick}):

        b.high = prices['high']
        b.low = prices['low']
        b.close = prices['close']
        thisTime = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(prices['time']))
        thisEpochTime = prices['time']
        thisAdxVals = adx.handle_data(s,b)
        thisADX = thisAdxVals[0]
        thisPDI = thisAdxVals[1]
        thisMDI = thisAdxVals[2]
        
        db.adxResults.insert_one({'epochTime': thisEpochTime, 'time': thisTime, 'tick': thisTick, 'adx': thisADX, 'pdi': thisPDI, 'mdi': thisMDI, 'high': b.high, 'low': b.low, 'close': b.close})

# Check for ADX > 30 and set trigger

latestTime = db.adxResults.find().sort([("epochTime", -1)]).limit(1)
for i in latestTime:
    lastADX = i['epochTime']

latestADX =  db.adxResults.find({'epochTime': lastADX, 'adx': {'$gt': 50}})

# Load potentials (low, high, close already there as we are inserting whole docuent from adxResults to collection)
for i in latestADX:
    db.potentials.insert_one(i)
    if i['pdi'] > i['mdi']:
        print "Buy %s with ADX of %d" % (i['tick'], i['adx'])
        db.potentials.update({'tick': i['tick']}, {"$set": {'direction': 'buy'}}, upsert=False)
        db.potentials.update({'tick': i['tick']}, {"$set": {'trigger': i['low']}}, upsert=False)
    else:
        print "Sell %s with ADX of %d" % (i['tick'], i['adx'])
        db.potentials.update({'tick': i['tick']}, {"$set": {'direction': 'sell'}}, upsert=False)
        db.potentials.update({'tick': i['tick']}, {"$set": {'trigger': i['high']}}, upsert=False)

# Now need to analyze next N periods for each potential, checking for dips or rises

# First, add potentials to trackers document
trackingTicksDict = {}
for pot in db.potentials.find():
    trackingTicks = db.find.trackers()
    for i in trackingTicks:
        trackingTicksDict.append(i)
    if pot['tick'] not in trackingTicksDict:
        db.trackers.insert_one(pot)

# Now we have trackers, check for any that have expired, (5 x N periods old)
# Need to get potential Epoch time





# Get all periods after Epoch time, put them into tracking document

# if the count is > 5 then remove from 'tracking' document


checkForDipOrRiseDict = {}
for pot in db.potentials.find():
    count = 0
    potEpochTime = pot['epochTime']
    thisTick = pot['tick']
    trackingCur = db.adxResults.find({'tick': thisTick, 'epochTime': {'$gt': potEpochTime}})
    for i in trackingCur:
        if trackingCur['tick'] == thisTick:
            count += 1
            if count == 5:
                db.tracking.remove({'tick': thisTick})
            else:
                checkForDipOrRiseDict.append(i)

    # Now we have a the last N periods after the ADX period, let's work out if we have a dip or rise
    green, red = 0, 0
    for i in checkForDipOrRiseDict:
        if i['close'] > i['open']:
            green += 1
        if i['close'] > i['open']:
            red += 1

# if detected AND close price is < trigger, set trigger flag to true
    if (red >= 3 and checkForDipOrRiseDict['close'] < pot['trigger'] and pot['direction' == 'Buy']):
        db.potentials.update({'tick': thisTick}, {"$set": {'triggerFlag': True}}, upsert=False)
    if (green >= 3 and checkForDipOrRiseDict['close'] > pot['trigger'] and pot['direction' == 'Sell']):
        db.potentials.update({'tick': thisTick}, {"$set": {'triggerFlag': True}}, upsert=False)

# Now we should have the potentials collection updated with a triggerFlag and a trigger price, we're done herejjk




