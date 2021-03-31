import os
import time
import sys, getopt
import datetime
import math
import threading
import logging
import socket

import requests

import ccxt

botTimeInterval = 40

import redis
import os
from os.path import join, dirname
from dotenv import load_dotenv

#dotenv_path = join('../.env')
# load_dotenv('.env')
# load_dotenv('/etc/rockx/.env')

if(os.path.exists("./etc/rockx/.env")):
    load_dotenv('./etc/rockx/.env')
    print("./etc/rockx/.env")
else:
    load_dotenv('.env')
    print(".env")

redis_host = os.environ.get("REDIS_HOST")
redis_port = os.environ.get("REDIS_PORT")
redis_password = os.environ.get("REDIS_PASSWORD")

ths_default_price = os.environ.get("THS_DEFAULT_PRICE")

exchangeBinance = ccxt.binance({
    'apiKey': '',
    'secret': '',
})
exchangeBitfinex = ccxt.bitfinex({
    'apiKey': '',
    'secret': '',
})
exchangeKraken = ccxt.kraken({
    'apiKey': '',
    'secret': '',
})
exchangePoloniex = ccxt.poloniex({
    'apiKey': '',
    'secret': '',
})
exchangeHuobi = ccxt.huobipro({
    'apiKey': '',
    'secret': '',
})
exchangeBitstamp = ccxt.bitstamp({
    'apiKey': '',
    'secret': '',
})
exchangeCoinbase = ccxt.coinbasepro({
    'apiKey': '',
    'secret': '',
})
exchangeOkex = ccxt.okex3({
    'apiKey': '',
    'secret': '',
})

trackedCoins = [
    "ATOM", "BTC", "ETH", "USDT"
]
baseCoins = [
    "USD", "BTC", "CNY", "USDT"
]
coinIndexList = {
    "ATOM": {
        "exchange": [
            ["binance", "USDT"],
            ["bitfinex", "USD"],
            # ["kraken", "USD"]
        ],
    },
    "BTC": {
        "exchange": [
            ["binance", "USDT"],
            ["bitfinex", "USD"],
            # ["kraken", "USD"]
        ],
    },
    "ETH": {
        "exchange": [
            ["binance", "USDT"],
            ["bitfinex", "USD"],
            # ["kraken", "USD"]
        ],
    },
    "USDT": {
        "exchange": [
            ["bitfinex", "USD"],
        ],
    }
}

r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)


def getExchangeAndPair(quotedCurrency, indexNum):
    count = 0
    selectedExchangePair = []

    for x in coinIndexList[quotedCurrency]["exchange"]:
        if(count < indexNum):
            count += 1
            selectedExchangePair.append([x[0], str(quotedCurrency)+"/"+str(x[1])])
        else:
            break

    return [selectedExchangePair, count]

def coin_THS(btc_price, usdt_price):
    url = 'http://api.rockminer.cn/open_api/contract/contract-unit-price'

    data = {'contract_id': 7}

    dataTHS = requests.post(url, data=data)
    dataTHS = dataTHS.json()

    print("dataTHS", dataTHS)

    if(len(dataTHS["retData"]) > 0):
        priceTHS = float(dataTHS["retData"])

        if(priceTHS.isdigit()):
            print("priceTHS", priceTHS)
        else:
            priceTHS = float(ths_default_price) # 33


        setPriceTHS(priceTHS, btc_price, usdt_price)

    else:
        priceTHS = float(ths_default_price) # 33

        setPriceTHS(priceTHS, btc_price, usdt_price)


def setPriceTHS(priceTHS, btc_price, usdt_price):
    print("priceTHS", priceTHS)

    priceBTC = float(btc_price)
    priceUSDT = float(usdt_price)

    r.set("ths" + ":" + "usd" + ":average_buy", priceTHS)
    r.set("ths" + ":" + "usd" + ":average_sell", priceTHS)
    r.set("ths" + ":" + "usd" + ":average_price", priceTHS)
    r.set("ths" + ":" + "btc" + ":average_buy", priceTHS / priceBTC)
    r.set("ths" + ":" + "btc" + ":average_sell", priceTHS / priceBTC)
    r.set("ths" + ":" + "btc" + ":average_price", priceTHS / priceBTC)
    r.set("ths" + ":" + "cny" + ":average_buy", priceTHS * 7)
    r.set("ths" + ":" + "cny" + ":average_sell", priceTHS * 7)
    r.set("ths" + ":" + "cny" + ":average_price", priceTHS * 7)
    r.set("ths" + ":" + "usdt" + ":average_buy", priceTHS / priceUSDT)
    r.set("ths" + ":" + "usdt" + ":average_sell", priceTHS / priceUSDT)
    r.set("ths" + ":" + "usdt" + ":average_price", priceTHS / priceUSDT)

def startBot():
    try:

        # The decode_repsonses flag here directs the client to convert the responses from Redis into Python strings
        # using the default encoding utf-8.  This is client specific.

        print("---------")

        for i in trackedCoins:
            count = 0

            quotedCurrency = i.lower()
            pairTracked = getPrice(i, 5)
            for t in baseCoins:
                baseCurrency = t.lower()

                if(len(pairTracked[count]) >= 3):
                    print(quotedCurrency, baseCurrency, pairTracked[count])
                    if(pairTracked[count][0] > 0):
                        r.set(quotedCurrency + ":" + baseCurrency + ":average_buy", pairTracked[count][0])

                    if(pairTracked[count][1] > 0):
                        r.set(quotedCurrency + ":" + baseCurrency + ":average_sell", pairTracked[count][1])

                    if(pairTracked[count][2] > 0):
                        r.set(quotedCurrency + ":" + baseCurrency + ":average_price", pairTracked[count][2])

                count += 1

        btc_price = float(r.get("btc:usd:average_price"))
        usdt_price = float(r.get("usdt:usd:average_price"))

        coin_THS(btc_price, usdt_price)

    except Exception as e:
        print(e)

def getPrice(quotedCurrency, indexNum):
    quotedCurrency = quotedCurrency.upper()

    conversionRateUSD = 1
    conversionRateCNY = 1/7
    conversionRateBTC = 1
    conversionRateUSDT = 1

    orderBook_bitfinex_btc = exchangeBitfinex.fetchOrderBook("BTC/USD", 5)
    conversionRateBTC = orderBook_bitfinex_btc['bids'][0][0]

    orderBook_bitfinex_usdt = exchangeBitfinex.fetchOrderBook("USDT/USD", 5)
    conversionRateUSDT = orderBook_bitfinex_usdt['bids'][0][0]

    selectedExchangeResult = getExchangeAndPair(quotedCurrency, indexNum)
    selectedExchangePair = selectedExchangeResult[0]
    selectedExchangeCount = selectedExchangeResult[1]

    print(selectedExchangePair)

    defaultCurrencyPriceUSD = []
    defaultCurrencyPriceBTC = []
    defaultCurrencyPriceCNY = []
    defaultCurrencyPriceUSDT = []

    bid_total = 0
    ask_total = 0

    # if(currencyExist):
    for i in selectedExchangePair:
        if(i[0] == "binance"):
            orderBook_binance = exchangeBinance.fetchOrderBook(i[1], 5)
            bid_total += orderBook_binance['bids'][0][0]
            ask_total += orderBook_binance['asks'][0][0]
        elif(i[0] == "bitfinex"):
            orderBook_bitfinex = exchangeBitfinex.fetchOrderBook(i[1], 5)
            bid_total += orderBook_bitfinex['bids'][0][0]
            ask_total += orderBook_bitfinex['asks'][0][0]
        elif(i[0] == "kraken"):
            orderBook_kraken = exchangeKraken.fetchOrderBook(i[1], 5)
            bid_total += orderBook_kraken['bids'][0][0]
            ask_total += orderBook_kraken['asks'][0][0]

    bid_averaged = bid_total/selectedExchangeCount
    ask_averaged = ask_total/selectedExchangeCount

    bid_averaged_usd = bid_averaged / conversionRateUSD
    ask_averaged_usd = ask_averaged / conversionRateUSD

    averagePrice_total_usd = ((bid_averaged_usd + ask_averaged_usd)/2)

    defaultCurrencyPriceUSD.append(round(bid_averaged_usd,4))
    defaultCurrencyPriceUSD.append(round(ask_averaged_usd,4))
    defaultCurrencyPriceUSD.append(round(averagePrice_total_usd,4))

    bid_averaged_btc = bid_averaged / conversionRateBTC
    ask_averaged_btc = ask_averaged / conversionRateBTC

    averagePrice_total_btc = ((bid_averaged_btc + ask_averaged_btc)/2)

    defaultCurrencyPriceBTC.append(round(bid_averaged_btc,8))
    defaultCurrencyPriceBTC.append(round(ask_averaged_btc,8))
    defaultCurrencyPriceBTC.append(round(averagePrice_total_btc,8))

    bid_averaged_cny = bid_averaged / conversionRateCNY
    ask_averaged_cny = ask_averaged / conversionRateCNY

    averagePrice_total_cny = ((bid_averaged_cny + ask_averaged_cny)/2)

    defaultCurrencyPriceCNY.append(round(bid_averaged_cny,4))
    defaultCurrencyPriceCNY.append(round(ask_averaged_cny,4))
    defaultCurrencyPriceCNY.append(round(averagePrice_total_cny,4))

    bid_averaged_usdt = bid_averaged / conversionRateUSDT
    ask_averaged_usdt = ask_averaged / conversionRateUSDT

    averagePrice_total_usdt = ((bid_averaged_usdt + ask_averaged_usdt)/2)

    defaultCurrencyPriceUSDT.append(round(bid_averaged_usdt,4))
    defaultCurrencyPriceUSDT.append(round(ask_averaged_usdt,4))
    defaultCurrencyPriceUSDT.append(round(averagePrice_total_usdt,4))

    print("getPrice", defaultCurrencyPriceUSD, defaultCurrencyPriceBTC, defaultCurrencyPriceCNY, defaultCurrencyPriceUSDT)

    return [defaultCurrencyPriceUSD, defaultCurrencyPriceBTC, defaultCurrencyPriceCNY, defaultCurrencyPriceUSDT]




def setInterval(func, sec):
    def func_wrapper():
        setInterval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

setInterval(startBot,botTimeInterval)

# if __name__ == '__main__':
#     # app.run(debug=True)
#
#     main()
