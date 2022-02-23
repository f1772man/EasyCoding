from numpy import dtype
import pyupbit
import datetime
import time
import requests
import pandas as pd
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
    strbuf = datetime.datetime.now().strftime("[%m/%d %H:%M:%S] ") + message
    post_message(myToken,"#crypto", strbuf)

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    #target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    target_price = df.iloc[0][3] + (df.iloc[0][1] - df.iloc[0][2]) * k
    return target_price

def get_lastday_close(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    return df.iloc[0][3]

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)    
    ma15 = df['close'].rolling(window=15,min_periods=1).mean().iloc[-1]    
    return ma15

def get_ma30min(ticker):
    """30분봉 20이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute30", count=20)    
    ma30min = df['close'].rolling(window=20,min_periods=1).mean().iloc[-1]    
    return ma30min

def get_ma10min(ticker,window):
    """10분봉 20이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=window)    
    ma10min = df['close'].rolling(window=window,min_periods=1).mean().iloc[-1]    
    return ma10min

def get_balance(ticker):
    """잔고 조회"""
    coinlist=[]
    balances = upbit.get_balances()
    
    if ticker == 'ALL':
        for item in balances:            
            if item['currency'] != 'KRW':
                coinlist.append(item['currency'])            
        return coinlist
    
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def get_coin_info(ticker):
    pd.set_option('display.unicode.east_asian_width', True)
    pd.options.display.float_format = '{:,.1f}'.format
    balances = pd.DataFrame(upbit.get_balances())
    balances = balances.drop([0])               # 첫번째 현금 보유 정보는 삭제함

    totalBalance = []           # 보유수량(잔고수량) = 잔고수량 + 미체결 잔고수량 계산하여 데이터 프레임에 추가
    currencyPrice = []          # 보유종목의 티커를 이용 현재가 조회
    coinRate = []               # 수익율=(현재가 / 매수가)*100 -100 수익율을 계산하여 데이터 프레임에 추가

    balances = balances.astype({'balance':'float','locked':'float','avg_buy_price':'float'})

    for i in balances.index:
        totalBalance.append(balances.loc[i,'balance'] + balances.loc[i,'locked'])
        currencyPrice.append(get_current_price("KRW-" + balances.loc[i,'currency']))    
        coinRate.append(currencyPrice[i-1] / balances.loc[i,'avg_buy_price']*100-100)

    balances.insert(3,"totalBalance",totalBalance, True)
    balances.insert(4,"currency_price",currencyPrice, True)
    balances.insert(5,"rates",coinRate, True)
        
    # 컬럼명을 한글로 대체
    balances.columns=['코인','잔고수량', '미체결 잔고수량','수량','현재가','수익율','매수가','평균가', '통화단위']

    if ticker == 'ALL':
        mrkdwn_text = ""        
        
        for i in balances.index:
            rates = round(balances.loc[i, "수익율"],1)
            min10_MA5 = get_ma10min("KRW-" + balances.loc[i,'코인'], 5)
            min10_MA20 = get_ma10min("KRW-" + balances.loc[i,'코인'], 20)
            print(min10_MA20)
            current_price = get_current_price("KRW-" + balances.loc[i,'코인'])
            last_price = get_lastday_close("KRW-" + balances.loc[i,'코인'])
            lastrate = round((current_price / last_price)*100 - 100, 2)
            if current_price > last_price:
                lastrates = str(lastrate) + "% ▲" + str(current_price - last_price)
            else:
                lastrates = str(lastrate) + "% ▼" + str(last_price - current_price)
            if min10_MA5 < current_price and min10_MA5 > min10_MA20:
                mrkdwn_text = mrkdwn_text + "\n`" + str(balances.loc[i,'코인']) + "`\n```" + str(int(current_price)) + " (" + str(rates) + "%)\n" + lastrates  +  "\n" +   "상승```\n"
            else:
                mrkdwn_text = mrkdwn_text + "\n`" + str(balances.loc[i,'코인']) + "`\n```" + str(int(current_price)) + " (" + str(rates) + "%)\n" + lastrates  +  "\n" +   "하강```\n"
            time.sleep(1)
        dbgout(mrkdwn_text)
    else:
        for i in balances.index:
            if balances.loc[i, '코인'] == ticker:
                return round(balances.loc[i, '수익율'],1)
    
def get_RSI(ticker, period = 14, column = 'close'):
    df = pyupbit.get_ohlcv(ticker, interval="minute30", count=100)
    df = pd.DataFrame(df)
    df.to_csv("rsi.csv")
    
    delta = df[column].diff(1)    
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

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
# 시작 메세지 슬랙 전송

dbgout("\nUpbit autotrade start")
#coins=get_balance("ALL")
coins = ['DOGE','FLOW','MLK','HBAR','NU','CVC','AERGO','STRK']

bought_list = []
RSI_list = []

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-DOGE")
        end_time = start_time + datetime.timedelta(days=1)        
        
        for coin in coins:
            if start_time < now < end_time - datetime.timedelta(seconds=60):    # 오늘 09:00 < 현재 < 익일 08:59:50                            
                target_price = get_target_price("KRW-" +  coin, 0.2)
                current_price = get_current_price("KRW-" + coin)
                ma15 = get_ma15("KRW-" + coin)                
                min10_MA20 = get_ma10min("KRW-" + coin, 20)
                min10_MA60 = get_ma10min("KRW-" + coin, 60)
                rsi = get_RSI("KRW-" + coin, period = 14)               
                min30rsi = rsi.iloc[-1]
                if min30rsi <= 30:
                    RSI_list.append(coin)
                if target_price < current_price and ma15 < current_price:
                    krw = get_balance("KRW")
                    if krw > 5000 and coin not in bought_list:                  # 해당 종목을 구매했으면 재구매하지않는다.
                        buy_result = upbit.buy_market_order("KRW-" + coin, 10000)                        
                        bought_list.append(coin)
                        dbgout(coin + " buy")
                elif min10_MA20 > min10_MA60 and coin in RSI_list:          # 골든크로스 20이평선이 60이평선을 뚫는 조건을 만족하고 30분봉 RSI 값이 30 밑으로 떨어질때
                    krw = get_balance("KRW")
                    if krw > 5000 and coin not in bought_list:                  # 해당 종목을 구매했으면 재구매하지않는다.
                        buy_result = upbit.buy_market_order("KRW-" + coin, 10000)                        
                        bought_list.append(coin)
                        dbgout(coin + " buy")
            else:                
                coinbalance = get_balance(coin)
                if coinbalance > 0.00008:
                    sell_result = upbit.sell_market_order("KRW-" + coin, coinbalance)      
                    dbgout(coin + " sell")
            time.sleep(1)
        if now.minute % 10 == 0 and 0 <= now.second <= 5:
            get_coin_info('ALL')            
            time.sleep(5)            
    except Exception as e:
        print(e)        
        dbgout(e)
        time.sleep(1)