import pandas as pd
from pandas import DataFrame
from pandas_ta.utils import get_offset, verify_series
from pandas_ta.utils import recent_maximum_index, recent_minimum_index
import matplotlib.pyplot as plt
import yfinance as yf
import numpy as np
import warnings
import datetime
#from mplfinance import candlestick2_ohlc
import matplotlib.ticker as ticker

plt.style.use('dark_background')
warnings.filterwarnings('ignore')

df = yf.download(tickers = '005930.KS', start = '2020-01-01', end = '2020-08-01')
df['Date'] = df.index

plt.grid(b=True, color='DarkTurquoise', alpha=0.3, linestyle=':', linewidth=2)
plt.legend( loc='upper left', fontsize = 13)
plt.xlabel('Date', fontsize = 17)
plt.ylabel('Close Price', fontsize = 17)
plt.title('Close Price', fontsize = 23, position = (0.5,1.05))
df.Close.plot(figsize = (18,8))
plt.show()

def SMA(data,period = 30, column = 'Close') :
    return data[column].rolling(window = period).mean()

def RSI(data, period = 14, column = 'Close') :
    delta = data[column].diff(1)
    delta = delta.dropna()
    
    up = delta.copy()
    down = delta.copy()
    up[up <0] =0
    down[down>0] = 0
    data['up'] = up
    data['down'] = down
    
    AVG_Gain = SMA(data, period, column = 'up')
    AVG_Loss = abs(SMA(data,period,column = 'down'))
    RS = AVG_Gain / AVG_Loss
    
    RSI = 100.0 - (100.0 / (1.0+RS))
    data['RSI'] = RSI
    
    return data

df = RSI(df, period = 14)

column_list = ['RSI']
df[column_list].plot(figsize = (18,8))
plt.title('RSI',position = (0.5,1.05),fontsize = 23)
plt.xlabel('Date', fontsize = 17)
plt.ylabel('RSI Values (0 - 100)', fontsize = 17)
plt.axhline(30, ls = '--', c='y', alpha = 0.9)
plt.grid(b=True, color='DarkTurquoise', alpha=0.3, linestyle=':', linewidth=2)
plt.legend( loc='upper left', fontsize = 13)
plt.axhline(70, ls = '--', c='y', alpha = 0.9)