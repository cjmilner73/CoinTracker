import time
import calendar
from pymongo import MongoClient
from myConnection import getConn

polCon = getConn()

client = MongoClient('mongodb://localhost:27017')

currHour = time.strftime("%Y/%m/%d %H")
currMin = time.strftime("%M")
db = client.ticker_db

# Check if 2 periods spike 30 percent over price average

weekInSeconds = 604800
monthInSeconds = 2592000
twoMonthsInSeconds = 2592000*2
threeMonthsInSeconds = 2592000*3
fourHoursInSeconds = 14400
oneDayInSeconds = 86400

tickPeriod = fourHoursInSeconds

nowTimeEpoch = calendar.timegm(time.gmtime())
# endTimeEpoch = calendar.timegm(time.gmtime()) - (5 * tickPeriod)
endTimeEpoch = nowTimeEpoch
startTimeEpoch = endTimeEpoch  - (3 * tickPeriod)

# Get last 3 periods

#polTicker = polCon.returnTicker()
#
#tickPairKeys = polTicker.keys()
#
#btcTickPairs = []
#for tickPair in tickPairKeys:
#    if tickPair.startswith("BTC"):
#        btcTickPairs.append(tickPair)
#
#for keyPair in btcTickPairs:
#    closes = []
#    index = 0
#    polChart = polCon.returnChartData(keyPair, tickPeriod, startTimeEpoch, endTimeEpoch)
#    for tickSticks in polChart['candleStick']:
#        closes[index] = tickSticks['close']
#        index += 1
#
#    for i in closes:
#        if i[2] > i[1]*1.3 > i[0]*1.3:
#            print "%s is streaking!" % keyPair

# TODO: Alternative code that doesn't require download, use existing collection

values = []
thisTick = "BTC_ETH"
lastThreeTicks = db.adxResults.find({'tick': thisTick}).sort([("epochTime", -1)]).limit(3)
for i in lastThreeTicks:
    values.append(i['close'])

values[0] = 51
values[1] = 50
values[2] = 49

for i in values:
    if values[1]/values[2] > 1.3 and values[0]/values[1] > 1.3:
        print "%s STREAKING" % (thisTick)

for i in values:
    if values[2]/values[1]  > 1.3 and values[1]/values[0] > 1.3:
        print "%s DUMPING" % (thisTick)
