import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

data = yf.download("AAPL", start="2022-01-01", end="2025-12-30", auto_adjust=True)

prices = data["Close"]

plt.plot(prices.index, prices.values)
plt.show()