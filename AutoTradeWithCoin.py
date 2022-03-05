from audioop import add
from mimetypes import init
from numpy import dtype
import schedule
import pyupbit
import datetime
import time
import requests
import pandas as pd
import os
from matplotlib import ticker


with open("upbit.txt") as f:
    lines = f.readlines()
    access = lines[0].strip()
    secret = lines[1].strip()
    myToken = lines[2].strip()

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )
    print(response)

def dbgout(message):
    """인자로 받은 문자열을 파이썬 셸과 슬랙으로 동시에 출력한다."""
    print(datetime.datetime.now().strftime('[%m/%d %H:%M:%S]'), message)
    strbuf = "`" + datetime.datetime.now().strftime('[%m/%d %H:%M:%S]') + "`" + message
    post_message(myToken,"#crypto", strbuf)

def get_koreaName(ticker):    
    url = "https://api.upbit.com/v1/market/all" 
    resp = requests.get(url) 
    data = resp.json() 

    for coin in data:
        if coin['market'] == ticker:
            return (coin['korean_name'])

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2, period=0.2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_lastday_close(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2, period=0.2)
    return df.iloc[0]['close']

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1, period=0.2)
    start_time = df.index[0]
    return start_time

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15, period=0.2)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15

def get_ma30min(ticker):
    """30분봉 20이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute30", count=20, period=0.2)    
    ma30min = df['close'].rolling(20).mean().iloc[-1]    
    return ma30min

def get_ma10min(ticker,window):
    """10분봉 20이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=window, period=0.2)    
    ma10min = df['close'].rolling(window=window).mean().iloc[-1]    
    return round(ma10min,1)

def get_ma5min(ticker,window):
    """5분봉 """
    df = pyupbit.get_ohlcv(ticker, interval="minute5", count=window, period=0.2)    
    ma5min = df['close'].rolling(window=window).mean().iloc[-1]    
    return round(ma5min,1)

def get_ma1min(ticker,window):
    """1분봉 """
    df = pyupbit.get_ohlcv(ticker, interval="minute1", count=window, period=0.2)    
    ma1min = df['close'].rolling(window=window).mean().iloc[-1]    
    return round(ma1min,1)

def get_soar(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="minute1", count=1, period=0.2)
    soar = df.iloc[0]['high'] / df.iloc[0]['open'] *100 -100
    return 5.0 > round(soar,2)

def get_balance(ticker):
    """잔고 조회"""
    coinlist=[]
    balances = upbit.get_balances()
    
    if ticker == 'ALL':
        for item in balances:
            if item['currency'] != 'KRW':
                coinlist.append("KRW-"+item['currency'])        
        return coinlist
    
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance']), float(b['locked'])
            else:
                return None, None
        
    return None, None

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def get_coin_info():
    pd.set_option('display.unicode.east_asian_width', True)
    pd.options.display.float_format = '{:,.1f}'.format
    balances = pd.DataFrame(upbit.get_balances())    
    balances = balances.drop([0])               # 첫번째 현금 보유 정보는 삭제함    

    balances = balances.astype({'balance':'float','locked':'float','avg_buy_price':'float'})
    
    mrkdwn_text = ""        
    
    for i in balances.index:
        coin = "KRW-" + balances.loc[i,'currency']
        korname = get_koreaName(coin)
        rates = round(get_current_price(coin) / balances.loc[i,'avg_buy_price']*100-100,1)
        min10_MA5 = get_ma10min(coin, 5)
        min10_MA20 = get_ma10min(coin, 20)
        min10_MA60 = get_ma10min(coin, 60)
        current_price = get_current_price(coin)
        last_price = get_lastday_close(coin)
        lastrate = round((current_price / last_price)*100 - 100, 2)
        if current_price > last_price:
            lastrates = "▲" + str(lastrate) + "%" # / " + str(current_price - last_price)
        else:
            lastrates = "▼" + str(lastrate) + "%" # / " + str(last_price - current_price)

        mrkdwn_text = mrkdwn_text + "\n" + "```" + korname + "(" + str(balances.loc[i,'currency']) +  ")" + "```" + "\n" + lastrates  +  "\n" + "현재가: " + str(int(current_price)) + "원" + "\n수익율: " + str(rates) + "%\n"

        if min10_MA5 > min10_MA20:
            mrkdwn_text = mrkdwn_text + "`10분봉 5이평선 단기상승`\n"
        else:
            mrkdwn_text = mrkdwn_text + "`10분봉 5이평선 단기하강`\n"
        
        if min10_MA5 > min10_MA60:
            mrkdwn_text = mrkdwn_text + "`10분봉 5이평선 중기상승`\n"
        else:
            mrkdwn_text = mrkdwn_text + "`10분봉 5이평선 중기하강`\n"

        time.sleep(1)
    dbgout(mrkdwn_text)
schedule.every(10).minutes.do(get_coin_info)

def get_RSI(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="minute5", count=100)
    df = pd.DataFrame(df)    
    
    delta = df['close'].diff(1)        
    delta = delta.dropna()   

    gain = delta.copy()    
    loss = delta.copy()
    gain[gain < 0] = 0    
    loss[loss > 0] = 0
    
    df['gain'] = gain
    df['loss'] = loss
    
    gainmean = gain.ewm(com=13, adjust=False).mean()
    lossmean = loss.abs().ewm(com=13, adjust=False).mean()
    RS = gainmean / lossmean

    RSI = 100.0 - (100.0 / (1.0 + RS))    
    
    df['RSI'] = RSI
    
    return df['RSI']

def buy_coin(ticker, balance, buy_message):    
    buy_result = upbit.buy_market_order(ticker, balance*0.995)        #0.9986 예약주문 거래수수료
    krw, krwLocked = get_balance("KRW")
       
    if buy_result != None:
        tradingNote['Date'] = datetime.datetime.now().strftime("%m/%d %H:%M:%S")
        tradingNote['Coin'] = ticker
        tradingNote['Qty'] = 10000 / pyupbit.get_current_price(ticker)
        tradingNote['Side'] = "buy"
        tradingNote['Price'] = pyupbit.get_current_price(ticker)
        tradingNote['Note'] = buy_message
        boughtCoins.append(ticker)
        dbgout("\n```매수체결 " + ticker + " : " + str(tradingNote['Price']) + "원에 " + str(buy_result['price']) + "원을 매수하다.```")
        df = pd.DataFrame([tradingNote])
        # .to_csv 
        # 최초 생성 이후 mode는 append
        if not os.path.exists('Transaction.csv'):
            df.to_csv('Transaction.csv', index=False, mode='w', encoding='utf-8-sig')
        else:
            df.to_csv('Transaction.csv', index=False, mode='a', encoding='utf-8-sig', header=False)
        return buy_result['executed_volume']
    else:
        dbgout("\n```주문가능한 금액(KRW)이 부족합니다.```")
        return 0


def sell_coin(ticker, sbalance, sell_message):
    
    sell_result = upbit.sell_market_order(ticker, sbalance)

    if ticker in boughtCoins and coinbalance < (5000 / pyupbit.get_current_price(ticker)):
        boughtCoins.remove(ticker)
        favoriteCoins.remove(ticker)
        
    if sell_result != None:
        tradingNote['Date'] = datetime.datetime.now().strftime("%m/%d %H:%M:%S")
        tradingNote['Coin'] = ticker
        tradingNote['Qty'] = sbalance
        tradingNote['Side'] = "sell"
        tradingNote['Price'] = pyupbit.get_current_price(ticker)                
        tradingNote['Note'] = sell_message

        dbgout("\n```매도체결 " + ticker + " : " + str(sell_result['volume']) + "```")

        df = pd.DataFrame([tradingNote])
        # .to_csv 
        # 최초 생성 이후 mode는 append
        if not os.path.exists('Transaction.csv'):
            df.to_csv('Transaction.csv', index=False, mode='w', encoding='utf-8-sig')
        else:
            df.to_csv('Transaction.csv', index=False, mode='a', encoding='utf-8-sig', header=False)
        return sell_result['executed_volume']
    else:
        dbgout(ticker + "주문가능한 금액(" + str(sbalance) + ")이 부족합니다.")
        return
         
def get_soaredCoin(ticker):
    #tickerList = pyupbit.get_tickers(fiat="KRW")

    maxCoin = {}
    maxSoar = None
    
    #for ticker in tickerList:        
    df = pyupbit.get_ohlcv(ticker, interval="minute5", count=5)     # to="20220227 09:30:00"
    df['soar'] = df['close'] / df['open'] *100 -100 
    soarValue = round(df['soar'].max(),1)
    maxCoin[ticker] = soarValue
    time.sleep(0.2)
    #df = pd.DataFrame(list(maxCoin.items()), columns=['ticker', 'soar'])
    df = pd.DataFrame.from_dict(maxCoin, orient='index').rename(columns={0:'soar'})
    df = df.sort_values('soar', ascending=False)
    #soarList = [item for item in df.head().index]
    return df['soar'].max()   #soarList

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
# 시작 메세지 슬랙 전송

dbgout("\nUpbit autotrade start")

favoriteCoins = ['KRW-AERGO', 'KRW-CVC', 'KRW-POLY', 'KRW-WAVES', 'KRW-NEAR', 'KRW-NU']
initBoughtCoins = get_balance("ALL")
initBoughtCoins = list(set(initBoughtCoins))
favorites = "\n>보유코인\n```"
favoriteCoins_koreaName = []
for i in initBoughtCoins:
    favoriteCoins_koreaName.append(get_koreaName(i) + "(" + i + ")")
favoriteCoins_koreaName =sorted(favoriteCoins_koreaName)
favorites = favorites + '\n'.join(s for s in favoriteCoins_koreaName) +"```\n"
dbgout(favorites)

labels = ['currency', 'balance']
tradingNote = {}
overSold = []
overBought = []
addCoins = []
removeCoins = []

favoriteCoins = list(set(favoriteCoins))
favorites = "\n>관심코인\n```"
favoriteCoins_koreaName = []
for i in favoriteCoins:
    favoriteCoins_koreaName.append(get_koreaName(i) + "(" + i + ")")
favoriteCoins_koreaName =sorted(favoriteCoins_koreaName)
favorites = favorites + '\n'.join(s for s in favoriteCoins_koreaName) +"```\n"
dbgout(favorites)

while True:
    schedule.run_pending()
    time.sleep(1)
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-DOGE")
        end_time = start_time + datetime.timedelta(days=1)        
        
        boughtCoins = get_balance("ALL")        

        if len(initBoughtCoins) > len(boughtCoins):
            removeCoins = list(set(initBoughtCoins) - set(boughtCoins))
            favoriteCoins = list(set(favoriteCoins) - set(removeCoins))
            favoriteCoins = favoriteCoins + boughtCoins
        elif len(initBoughtCoins) < len(boughtCoins):
            addCoins = list(set(boughtCoins) - set(initBoughtCoins))
            favoriteCoins = favoriteCoins + boughtCoins
        else:
            favoriteCoins = favoriteCoins + boughtCoins

        initBoughtCoins = boughtCoins
        initBoughtCoins = list(set(initBoughtCoins))
        favoriteCoins = list(set(favoriteCoins))
       
        if len(addCoins) != 0:
            favoriteCoins = list(set(favoriteCoins))
            favorites = "\n>관심코인\n```"
            favoriteCoins_koreaName = []
            for i in favoriteCoins:
                favoriteCoins_koreaName.append(get_koreaName(i) + "(" + i + ")")
            favoriteCoins_koreaName =sorted(favoriteCoins_koreaName)
            favorites = favorites + '\n'.join(s for s in favoriteCoins_koreaName) +"```\n"

            favorites = favorites + ">매수코인\n```"
            for i in addCoins:
                favorites = favorites + get_koreaName(i) + "(" + i + ")" + "\n"
            favorites = favorites + "```"
            dbgout(favorites)
        elif len(removeCoins) !=0:
            favoriteCoins = list(set(favoriteCoins))
            favorites = "\n>관심코인\n```"
            favoriteCoins_koreaName = []
            for i in favoriteCoins:
                favoriteCoins_koreaName.append(get_koreaName(i) + "(" + i + ")")
            favoriteCoins_koreaName =sorted(favoriteCoins_koreaName)
            favorites = favorites + '\n'.join(s for s in favoriteCoins_koreaName) +"```\n"
            favorites = favorites + ">매도코인\n```"
            for i in removeCoins:
                favorites = favorites + get_koreaName(i) + "(" + i + ")" + "\n"
            favorites = favorites + "```"
            dbgout(favorites)
        addCoins.clear()
        removeCoins.clear()
        for coin in favoriteCoins:
                      
            # 오늘 09:00 < 현재 < 익일 08:59:50
            if start_time < now < end_time - datetime.timedelta(seconds=60):
                
                time.sleep(0.2)
                target_price = get_target_price(coin, 0.2)
                current_price = get_current_price(coin)
                
                RSI = get_RSI(coin)
                RSI_5Min = round(RSI.iloc[-1],1)

                if RSI_5Min < 35:
                    overSold.append(coin)
                    dbgout("\n```" + str(coin) + "코인이 과매도(" + str(RSI_5Min) + ") 구간으로 매수 타이밍이 되었습니다.```")
                elif RSI_5Min >= 80:
                    overBought.append(coin)
                    dbgout("\n```" + str(coin) + "코인이 과매수(" + str(RSI_5Min) + ") 구간으로 매도 타이밍이 되었습니다.```")
                    variance = get_soaredCoin(coin)
                    if variance > 5.0:
                        dbgout("\n```" + str(coin) + ": " + str(variance) + "% 상승구간```")
                elif RSI_5Min >= 75:
                    overBought.append(coin)
                    dbgout("\n```" + str(coin) + "코인이 과매수(" + str(RSI_5Min) + ") 구간으로 매도 타이밍이 되었습니다.```")
                    variance = get_soaredCoin(coin)
                    if variance > 5.0:
                        dbgout("\n```" + str(coin) + ": " + str(variance) + "% 상승구간```")
                elif 50 <= RSI_5Min < 65 and coin in overSold:
                    overSold.remove(coin)
                elif 40 <= RSI_5Min < 60 and coin in overBought:
                    overBought.remove(coin)

                coinbalance, coinLocked = get_balance(coin.split('-')[1])
               
                if coin in boughtCoins and coinbalance != None and coinLocked != None:
                    if 5000 > current_price * coinbalance and 5000 > current_price * coinLocked:
                        boughtCoins.remove(coin)               

                krw, krwLocked = get_balance("KRW")        # 매수 가능 보유자산 조회
                
                if krw > 5000:
                    min5_MA5 = get_ma5min(coin, 5)        
                    min5_MA10 = get_ma5min(coin, 10)            
                    min5_MA20 = get_ma5min(coin, 20)
                    
                    if current_price > target_price:
                        if current_price > min5_MA5 and min5_MA5 > min5_MA20 and min5_MA5 > min5_MA10:   # 현재 가격이 목표가와 5일 이평선 값보다 클때
                            buy_message = "Buy-1: " + str(coin) + " / " + str(current_price) + " > " + str(min5_MA5) + " and " + str(min5_MA5) + " > " + str(min5_MA20) + " and " + str(min5_MA5) + " > " + str(min5_MA10)
                            buy_coin(coin, krw, buy_message)

                        elif min5_MA5 > min5_MA20 and RSI_5Min <= 50:   # 현재 가격이 목표가와 5일 이평선 값보다 클때
                            buy_message = "Buy-2: " + str(coin) + " / " + str(min5_MA5) + " > " + str(min5_MA20) + " and " + str(RSI_5Min) + " <= 50 " 
                            buy_coin(coin, krw, buy_message)

                        elif current_price > min5_MA5 and coin in overSold:
                            buy_message = "Buy-3: " + str(current_price) + ">" + str(min5_MA5) + "coin in overSold"
                            buy_coin(coin, krw, buy_message)

                    elif coin in overSold and min5_MA5 > min5_MA20:
                        buy_message = "Buy-4: " + "coin in overSold"
                        buy_coin(coin, krw, buy_message)
                
                if coinbalance is not None and coin in boughtCoins:
                    currentPrice = pyupbit.get_current_price(coin)
                    if coinbalance > 5000 / currentPrice:
                        min5_MA5 = get_ma5min(coin, 5)
                        min5_MA10 = get_ma5min(coin, 10)
                        min5_MA20 = get_ma5min(coin, 20)                            
                        
                        if coin in overBought:
                            if RSI_5Min >= 75 and (coinbalance / 2) > (5000 / currentPrice):
                                sell_message = "Sell-1: " + str(RSI_5Min) + " >= 75 and" + str(coinbalance) + " / 2 > 5000 / " + str(currentPrice)
                                sell_coin(coin, coinbalance/2, sell_message)
                            elif RSI_5Min >= 80 and (coinbalance / 2) > (5000 / currentPrice):
                                sell_message = "Sell-2: " + str(RSI_5Min) + " >= 80 and" + str(coinbalance) + " / 2 > 5000 / " + str(currentPrice)
                                sell_coin(coin, coinbalance, sell_message)

                        elif min5_MA5 < min5_MA10 and current_price < min5_MA5 and coinbalance /2 > 5000 / currentPrice:
                            sell_message = "Sell-3: " + str(min5_MA5) + "<" + str(min5_MA10) + "and" + str(current_price) + "<" + str(min5_MA5) + "and" + str(coinbalance) + " / 2 > 5000 / " + str(currentPrice)
                            sell_coin(coin, coinbalance/2, sell_message)
                        
                        elif min5_MA5 < min5_MA20 and current_price < min5_MA5:                                
                            sell_message = "Sell-4: " + str(min5_MA5) + "<" + str(min5_MA20) + "and" + str(current_price) + "<" + str(min5_MA5)
                            sell_coin(coin, coinbalance, sell_message)                            
                
            time.sleep(1)        
    except Exception as e:
        print(e)        
        dbgout(e)
        time.sleep(1)
