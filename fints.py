import finterstellar as fs
import pyupbit

df = pyupbit.get_ohlcv("KRW-DOGE", interval="day", count=100)
#fs.draw_chart(df, right="DOGE")
print(fs.rsi(df, w=14))
