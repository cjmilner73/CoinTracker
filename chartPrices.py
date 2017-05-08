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
        thisTime = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(prices['time']))
        thisEpochTime = prices['time']
        thisAdxVals = adx.handle_data(s,b)
        thisADX = thisAdxVals[0]
        thisPDI = thisAdxVals[1]
        thisMDI = thisAdxVals[2]
        db.adxResults.insert_one({'epochTime': thisEpochTime, 'time': thisTime, 'tick': thisTick, 'adx': thisADX, 'pdi': thisPDI, 'mdi': thisMDI, 'high': b.high, 'low': b.low, 'close': b.close})

# Finding the last time of all ADX entries, should be last 4 hour time
latestTime = db.adxResults.find().sort([("epochTime", -1)]).limit(1)

for i in latestTime:
    lastADX = i['epochTime']

# Now find all the TICKS that have an ADX over 50 with the time = the last time period (lastADX)
latestADX = db.adxResults.find({'epochTime': lastADX, 'adx': {'$gt': 44}})

#  Now for each tick we find with ADX above 50, first check if it's already a potential
# TODO: This is inserting duplicate potentials!
newTicks = {}
found = False
for i in latestADX:
    potentialsDict = db.potentials.find()
    for p in potentialsDict:
        print "p['tick'] = %s" % p['tick']
        print "i['tick'] = %s" % i['tick']
        if (i['tick'] == p['tick']):
            print "FOUND A DUPLICATE"
            found = True
# TODO: This statement must always be resulting in True...
    if found == False:
        print "Type potentialsDict: %s" % type(potentialsDict)
        print "%s not found, trying to insert..." % (i['tick'])
        db.potentials.insert_one(i)
        if i['pdi'] > i['mdi']:
            print "Setting up a Buy potential %s with ADX of %d" % (i['tick'], i['adx'])
            db.potentials.update({'tick': i['tick']}, {"$set": {'direction': 'buy'}}, upsert=False)
            db.potentials.update({'tick': i['tick']}, {"$set": {'trigger': i['low']}}, upsert=False)
        else:
            print "Setting up a Sell potential  %s with ADX of %d" % (i['tick'], i['adx'])
            db.potentials.update({'tick': i['tick']}, {"$set": {'direction': 'sell'}}, upsert=False)
            db.potentials.update({'tick': i['tick']}, {"$set": {'trigger': i['high']}}, upsert=False)
    else:
	print "%s already in the potentials collection" % i['tick']
        found == False

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

# if the count is > 5 then remove from 'tracking' document


for pot in db.potentials.find():
    count = 0
    potEpochTime = pot['epochTime']
    thisTick = pot['tick']
    for i in db.adxResults.find({'tick': thisTick, 'epochTime': {'$gt': potEpochTime}}):
        if i['tick'] == thisTick:
            count += 1
            if count == 5:
                #db.tracking.remove({'tick': thisTick})
                db.potential.remove({'tick': thisTick})
                count = 0
            else:
                db.dipOrRise.insert_one(i)

    # Now we have a the last N periods after the ADX period, let's work out if we have a dip or rise
    green, red = 0, 0
    for i in db.dipOrRise.find():
        if i['close'] > i['open']:
            print "Increasing GREEN by one"
            print
            green += 1
        if i['close'] > i['open']:
            red += 1
            print "Increasing RED by one"
            print

# if detected AND close price is < trigger, set trigger flag to true
    lastClosePrice = db.find.dipOrRise({'tick': pot['tick']}).sort([("epochTime", -1)]).limit(1)
    for i in lastClosePrice:
        closePrice = lastClosePrice['close']

    if red >= 3 and closePrice < pot['trigger'] and pot['direction' == 'Buy']:
        db.potentials.update({'tick': thisTick}, {"$set": {'triggerFlag': True}}, upsert=False)
	print "Setting BUY triggerFlag"
	print
    if green >= 3 and closePrice > pot['trigger'] and pot['direction' == 'Sell']:
        db.potentials.update({'tick': thisTick}, {"$set": {'triggerFlag': True}}, upsert=False)
	print "Setting SELL triggerFlag"
	print

# Now we should have the potentials collection updated with a triggerFlag and a trigger price, we're done herejjk




