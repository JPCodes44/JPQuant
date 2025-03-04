"""
Pandas_TA review
documentation
https://github.com/twopirllc/pandas-ta

"""

import talib as ta
import pandas_ta as pta
import pandas as pd


print("hi")

df = pd.read_csv("/Users/jpmak/Desktop/dev/Hyperliquid/MAN-1h-30wks_data.csv")

# SMA
df["sma_10"] = pta.sma(df["close"], length=10)

# EMA
df["ema_10"] = pta.sma(df["close"], length=10)

# RSI
df["rsi_14"] = pta.rsi(df["close"], length=10)

# MACD
df[["macd_line", "macd_signal", "macd_hist"]] = pta.macd(
    df["close"], fast=12, slow=26, signal=9
)

# stochastic oscillator
df[["stoch_k", "stoch_d"]] = pta.stoch(df["high"], df["low"], df["close"], k=14)

print(df)

# GET ALL OF THE INDICATORS HERE
# help(df.ta)
