from matplotlib.pyplot import axis
import pyupbit
import datetime
import time
import requests
import pandas as pd

def get_ma30min(ticker):
    """30분봉 20이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute30", count=100)    
    ma30min = df['close'].rolling(window=20,min_periods=1).mean()
    df['ma30min'] = ma30min
    df = df.loc['2022-02-22']

    return df['ma30min']

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
    
    #df = df.loc['2022-02-22']
    #buying = df['RSI'] <= 30
    ma30min5 = df['close'].rolling(window=5,min_periods=1).mean()
    df['ma30min5'] = ma30min5
    ma30min20 = df['close'].rolling(window=20,min_periods=1).mean()
    df['ma30min20'] = ma30min20
    
    df = df.loc['2022-02-22']
    df.to_csv("rsi.csv")
    print(df)
    return df['RSI']

df = get_RSI("KRW-HBAR", period = 14)
print(df)