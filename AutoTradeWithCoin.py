import time
from matplotlib import ticker
import pyupbit
import datetime
import requests
import pandas as pd
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

with open("upbit.txt") as f:
    lines = f.readlines()
    access = lines[0].strip()
    secret = lines[1].strip()
    myToken = lines[2].strip()

client = WebClient(token=myToken)

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
    #print(df.tail())
    ma30min = df['close'].rolling(20).mean().iloc[-1]
    #print(ma30min)
    return ma30min

def get_ma10min(ticker,window):
    """10분봉 20이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=30)
    #print(df.tail())
    ma10min = df['close'].rolling(window).mean().iloc[-1]
    #print(ma30min)
    return ma30min

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
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def get_coin_info(ticker):
    pd.set_option('display.unicode.east_asian_width', True)
    pd.options.display.float_format = '{:,.1f}'.format
    Assets = pd.DataFrame(upbit.get_balances())
    Assets = Assets.drop([0])               # 첫번째 현금 보유 정보는 삭제함

    totalBalance = []           # 보유수량(잔고수량) = 잔고수량 + 미체결 잔고수량 계산하여 데이터 프레임에 추가
    currencyPrice = []          # 보유종목의 티커를 이용 현재가 조회
    coinRate = []               # 수익율=(현재가 / 매수가)*100 -100 수익율을 계산하여 데이터 프레임에 추가

    Assets = Assets.astype({'balance':'float','locked':'float','avg_buy_price':'float'})

    for i in Assets.index:
        totalBalance.append(Assets.loc[i,'balance'] + Assets.loc[i,'locked'])
        currencyPrice.append(get_current_price("KRW-" + Assets.loc[i,'currency']))    
        coinRate.append(currencyPrice[i-1] / Assets.loc[i,'avg_buy_price']*100-100)

    Assets.insert(3,"totalBalance",totalBalance, True)
    Assets.insert(4,"currency_price",currencyPrice, True)
    Assets.insert(5,"rates",coinRate, True)
    # 컬럼명을 한글로 대체
    Assets.columns=['코인','잔고수량', '미체결 잔고수량','수량','현재가','수익율','매수가','평균가', '통화단위']

    if ticker == 'ALL':
        mrkdwn_text = ""
        for i in Assets.index:    
            coinInfo = Assets.loc[i,['현재가', '수익율']]
            mrkdwn_text = mrkdwn_text + "`" + str(Assets.loc[i,'코인']) + "`" + "\n```" + coinInfo.to_string() + "```\n"

        try:
            response = client.chat_postMessage(channel='#crypto', text=mrkdwn_text)
            print(response.status_code)
        except SlackApiError as e:
            print('Error: {}'.format(e.response['error']))        
        return 0
    else:
        for i in Assets.index:
            if Assets.loc[i, '코인'] == ticker:            
                return round(Assets.loc[i, '수익율'],1)
    return 0

def get_movingaverage_trend(code, window):
    """인자로 받은 종목에 대한 이동평균가격을 반환한다."""
    try:
        #olhc = get
        time_now = datetime.now()
        str_today = time_now.strftime('%Y%m%d')
        ohlc = get_ma10min(code, 20)
        if str_today == str(ohlc.iloc[0].name):
            lastday = ohlc.iloc[1].name
        else:
            lastday = ohlc.iloc[0].name
        closes = ohlc['close'].sort_index()         
        ma = closes.rolling(window=window).mean()
        return ma.loc[lastday]
    except Exception as ex:
        #dbgout('get_movingavrg(' + str(window) + ') -> exception! ' + str(ex))
        return None    

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
# 시작 메세지 슬랙 전송
post_message(myToken,"#crypto", "autotrade start")
coins=get_balance("ALL")
coins.remove('KRW')

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-DOGE")
        end_time = start_time + datetime.timedelta(days=1)
        if now.minute % 30 == 0 and 0 <= now.second <= 5:
            get_coin_info('ALL')    
            time.sleep(5)                
        for coin in coins:
            if start_time < now < end_time - datetime.timedelta(seconds=10):    # 오늘 09:00 < 현재 < 익일 08:59:50            
                rates = get_coin_info(coin)
                target_price = get_target_price("KRW-" + coin, 0.5)            
                current_price = get_current_price("KRW-" + coin)
                ma15 = get_ma15("KRW-" + coin)
                ma30min = get_ma30min("KRW-" + coin)
                             
                if now.minute % 5 == 0 and 0 <= now.second <= 5:
                        if ma30min < current_price:
                            post_message(myToken,"#crypto", str(coin) + "\n▲" + str(rates) + "%\n" + str(current_price) + "원")
                        else:                            
                            post_message(myToken,"#crypto", str(coin) + "\n▼" + str(rates) + "%\n" + str(current_price) + "원")
                if target_price < current_price and ma15 < current_price:
                    krw = get_balance("KRW")
                    if krw > 5000:
                        buy_result = upbit.buy_market_order("KRW-" + coin, krw*0.9995)
                        post_message(myToken,"#crypto", coin + " buy : " +str(buy_result))
            else:
                coin = get_balance(coins[0])
                if coin > 0.00008:
                    sell_result = upbit.sell_market_order("KRW-" + coin, coin*0.9995)
                    post_message(myToken,"#crypto", coin + " buy : " +str(sell_result))
            time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken,"#crypto", e)
        time.sleep(1)
