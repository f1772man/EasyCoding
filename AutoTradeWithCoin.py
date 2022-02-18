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

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_lastday_close(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    return df.iloc[0]['close']

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15

def get_ma30min(ticker):
    """30분봉 20이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute30", count=30)    
    ma30min = df['close'].rolling(20).mean().iloc[-1]    
    return ma30min

def get_ma10min(ticker,window):
    """10분봉 20이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=10)    
    
    ma10min = df['close'].rolling(window=window).mean()#.iloc[-1]
    
    df['10min5MA'] = ma10min
    
    ma10min = ma10min.iloc[-1]
    return ma10min

def get_balance(ticker):
    """잔고 조회"""
    coins=[]
    balances = upbit.get_balances()
    
    if ticker == 'ALL':
        for item in balances:
            coins.append(item['currency'])
        return coins
    
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
        mrkdwn_text = now.strftime('>%H:%M:%S %p')
        
        for i in balances.index:
            rates = get_coin_info(balances.loc[i,'코인'])
            min10_MA5 = get_ma10min("KRW-" + balances.loc[i,'코인'], 5)
            min10_MA20 = get_ma10min("KRW-" + balances.loc[i,'코인'], 20)
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
        mrkdwn_text = mrkdwn_text + now.strftime('>%H:%M:%S %p')
        post_message(myToken,"#crypto", mrkdwn_text)
    else:
        for i in balances.index:
            if balances.loc[i, '코인'] == ticker:
                return round(balances.loc[i, '수익율'],1)
    

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
# 시작 메세지 슬랙 전송
post_message(myToken, "#crypto", ' ')
startTime = datetime.datetime.now().strftime('\n>%m-%d %H:%M:%S%p')
post_message(myToken,"#crypto", startTime + "\n>Upbit autotrade start" )
coins=get_balance("ALL")
coins.remove('KRW')

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-DOGE")
        end_time = start_time + datetime.timedelta(days=1)        
        
        for coin in coins:
            if start_time < now < end_time - datetime.timedelta(seconds=10):    # 오늘 09:00 < 현재 < 익일 08:59:50                            
                target_price = get_target_price('KRW-' + coin, 0.5)
                current_price = get_current_price('KRW-' + coin)
                ma15 = get_ma15('KRW-' + coin)
                if now.minute % 10 == 0 and 0 <= now.second <= 5:            
                    get_coin_info('ALL') 
                    time.sleep(5)
                
                if target_price < current_price and ma15 < current_price:
                    krw = get_balance("KRW")
                    #post_message(myToken,"#crypto", coin + " 매수신호 ")
                    if krw > 5000:
                        buy_result = upbit.buy_market_order('KRW-' + coin, krw*0.9995)
                        post_message(myToken,"#crypto", coin + "buy : " +str(buy_result))
            else:
                coin = get_balance(coins[0])
                if coin > 0.00008:
                    sell_result = upbit.sell_market_order('KRW-' + coin, coin*0.9995)
                    post_message(myToken,"#crypto", coin + "buy : " +str(sell_result))
            time.sleep(1)        
    except Exception as e:
        print(e)
        post_message(myToken,"#crypto", e + "while")
        time.sleep(1)
