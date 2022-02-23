import pandas as pd
import os
import pyupbit

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k    
    return target_price, float(df.iloc[1]['open'])

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)    
    ma15 = df['close'].rolling(window=15,min_periods=1).mean().iloc[-1]    
    return ma15

def get_ma10min(ticker,window):
    """10분봉 20이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=window)    
    ma10min = df['close'].rolling(window=window,min_periods=1).mean().iloc[-1]    
    return ma10min

def get_ma30min(ticker, window):
    """30분봉 20이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute30", count=window+10)    
    ma30min = df['close'].rolling(window=window).mean().iloc[-1]    
    return ma30min

def get_RSI(ticker, period = 14, column = 'close'):
    df = pyupbit.get_ohlcv(ticker, interval="minute10", count=100)
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

def get_target_ticker():
    tickerKRW = []
    targetTicker = []
    targetList = {}
    tickerKRW = pyupbit.get_tickers(fiat="KRW")

    for i in tickerKRW:

        targetPrice, openPrice = get_target_price(i,0.5)
        currentPrice = get_current_price(i)
        ma15 = get_ma15(i)
        targetList['종목'] = i
        targetList['시가'] = openPrice
        targetList['목표가'] = round(targetPrice,2)
        targetList['시가대비 변동율'] = round((targetPrice/openPrice*100-100),2)
        targetList['현재가'] = currentPrice
        targetList['15일 이평선값'] = ma15

        if targetPrice > currentPrice and  currentPrice > ma15:
            targetTicker.append(i)
            targetList['매수여부'] = "OK"        
        else:
            targetList['매수여부'] = "NO"

        if get_ma30min(i, 20) > get_ma30min(i, 60):
            targetTicker.append(i)
            targetList['골든크로스'] = "YES"
        else:
            targetList['골든크로스'] = "YES"
        
    
        df = pd.DataFrame([targetList])
        # .to_csv 
        # 최초 생성 이후 mode는 append
        if not os.path.exists('TargetList.csv'):
            df.to_csv('TargetList.csv', index=False, mode='w', encoding='utf-8-sig')
        else:
            df.to_csv('TargetList.csv', index=False, mode='a', encoding='utf-8-sig', header=False)
    return targetTicker

print(get_target_ticker())