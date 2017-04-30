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

polTicker = polCon.returnTicker()

tickPairKeys = polTicker.keys()

btcTickPairs = []
for tickPair in tickPairKeys:
    if tickPair.startswith("BTC"):
        btcTickPairs.append(tickPair)

closes = []
index = 0
for keyPair in btcTickPairs:
    polChart = polCon.returnChartData(keyPair, tickPeriod, startTimeEpoch, endTimeEpoch)
    for tickSticks in polChart['candleStick']:
        closes[index] = tickSticks['close']
        index += 1

    for i in closes:
        if i[2] > i[1]*1.3 > i[0]*1.3:
            print "Streaker!"

