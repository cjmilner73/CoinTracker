import time
import calendar
import adx
from poloniex import Poloniex
from pymongo import MongoClient
from myConnection import getConn

polCon =  getConn()

client = MongoClient('mongodb://localhost:27017')

currHour = time.strftime("%Y/%m/%d %H")
currMin = time.strftime("%M")

weekInSeconds = 604800
monthInSeconds = 2592000
twoMonthsInSeconds = 2592000*2
threeMonthsInSeconds = 2592000*3
fourHoursInSeconds = 14400
oneDayInSeconds = 86400
fiveMinsInSeconds = 900

startEpoch = oneDayInSeconds
tickPeriod = fiveMinsInSeconds

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
db.dipOrRise.remove({})
#db.potentials.remove({})
#db.trackers.remove({})

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

def getPeriodHigh(thisTick):
    periodHigh = db.tickChart.find({'tick': thisTick}).sort([("close", -1)]).limit(1)
    for i in periodHigh:
        periodHighVal = i['close']
    return periodHighVal

def getPeriodLow(thisTick):
    periodLow = db.tickChart.find({'tick': thisTick}).sort([("close", 1)]).limit(1)
    for i in periodLow:
        periodLowVal = i['close']
    return periodLowVal


lastADX=0
for thisTick in btcTickPairs:
    adx.initialize(s)
    for prices in db.tickChart.find({'tick': thisTick}):

        if high == low == close:
            print "%s high %s, low %s, close %s are the same, time , continue" % (thisTick, high, low, close)
            continue
        b.high = prices['high']
        b.low = prices['low']
        b.close = prices['close']
        b.open = prices['open']
        thisTime = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(prices['time']))
        thisEpochTime = prices['time']
        thisAdxVals = adx.handle_data(s,b)
        thisADX = thisAdxVals[0]
        thisPDI = thisAdxVals[1]
        thisMDI = thisAdxVals[2]
        db.adxResults.insert_one({'epochTime': thisEpochTime, 'time': thisTime, 'tick': thisTick, 'adx': thisADX, 'pdi': thisPDI, 'mdi': thisMDI, 'high': b.high, 'low': b.low, 'close': b.close, 'open': b.open})

# Finding the last time of all ADX entries, should be last 4 hour time
latestTime = db.adxResults.find().sort([("epochTime", -1)]).limit(1)

for i in latestTime:
    lastADX = i['epochTime']

# Now find all the TICKS that have an ADX over 50 with the time = the last time period (lastADX)
print "Checking ADX results for time: %s" % lastADX
latestADX = db.adxResults.find({'epochTime': lastADX, 'adx': {'$gt': 44}})

#  Now for each tick we find with ADX above 50, first check if it's already a potential
# TODO: This is inserting duplicate potentials!
found = False
for i in latestADX:
    potentialsDict = db.potentials.find()
    for p in potentialsDict:
        if (i['tick'] == p['tick']):
            found = True
# Check if potential already exists
    if found == False or ():
        if i['close'] >= getPeriodHigh(i['tick']) and i['pdi'] > i['mdi']:
            print "Setting up a Buy potential %s with ADX of %d" % (i['tick'], i['adx'])
            db.potentials.insert_one(i)
            db.potentials.update({'tick': i['tick']}, {"$set": {'direction': 'buy'}}, upsert=False)
            db.potentials.update({'tick': i['tick']}, {"$set": {'trigger': i['low']}}, upsert=False)
        if i['close'] <= getPeriodLow(i['tick']) and i['pdi'] < i['mdi']:
            print "Setting up a Sell potential  %s with ADX of %d" % (i['tick'], i['adx'])
            db.potentials.insert_one(i)
            db.potentials.update({'tick': i['tick']}, {"$set": {'direction': 'sell'}}, upsert=False)
            db.potentials.update({'tick': i['tick']}, {"$set": {'trigger': i['high']}}, upsert=False)
    else:
        if found == True:
            print "%s already in the potentials collection" % i['tick']
            found == False
        else:
            print "No High Found, ADX %s: %s: %s and High is %s" % (i['adx'], i['tick'], i['close'], getPeriodHigh(i['tick']))

# Now need to analyze next N periods for each potential, checking for dips or rises

# First, add potentials to trackers document

#tickExists = False
#for pot in db.potentials.find():
#    tickExist = False
#    for track in db.trackers.find():
#        if pot['tick'] == track['tick']:
#            tickExists = True
#            print "Tick %s found in potentials"
#    if (tickExists != True):
#        db.trackers.insert_one(pot)
    

# Now we have trackers, check for any that have expired, (5 x N periods old)
# Need to get potential Epoch time

# Get all periods after Epoch time, put them into tracking document

# if the count is > then remove from 'tracking' document


for pot in db.potentials.find():
    count = 0
    potEpochTime = pot['epochTime']
    thisTick = pot['tick']
    print "Checking adxResults for %s and after epochTime %s" % (thisTick, potEpochTime)
    for i in db.adxResults.find({'tick': thisTick, 'epochTime': {'$gt': potEpochTime}}):
        if i['tick'] == thisTick:
            count += 1
            if count >= 5:
                #db.tracking.remove({'tick': thisTick})
                db.potentials.delete_one({'tick': thisTick})
                count = 0
                db.dipOrRise.delete_many({})
                break
            else:
                db.dipOrRise.insert_one(i)

    # Now we have a the last N periods after the ADX period, let's work out if we have a dip or rise
    green, red = 0, 0
    for i in db.dipOrRise.find():
        if i['close'] > i['open']:
            print "Increasing GREEN by one for %s" % i['tick']
            print
            green += 1
        if i['close'] > i['open']:
            red += 1
            print "Increasing RED by one for %s" % i['tick']
            print

# if detected AND close price is < trigger, set trigger flag to true
    lastClosePrice = db.dipOrRise.find({'tick': pot['tick']}).sort([("epochTime", -1)]).limit(1)

    for i in lastClosePrice:
        closePrice = i['close']

    if red >= 3 and closePrice < pot['trigger'] and pot['direction'] == 'Buy':
        db.potentials.update({'tick': thisTick}, {"$set": {'triggerFlag': True}}, upsert=False)
	print "Setting BUY triggerFlag"
	print
    if green >= 3 and closePrice > pot['trigger'] and pot['direction'] == 'Sell':
        db.potentials.update({'tick': thisTick}, {"$set": {'triggerFlag': True}}, upsert=False)
	print "Setting SELL triggerFlag"
	print

# Now we should have the potentials collection updated with a triggerFlag and a trigger price, we're done herejjk




