import yfinance as yf
import pandas as pd

# 下载历史数据（假设为比特币的1小时数据）
data = yf.download('BTC-USD', period='1mo', interval='1h')

# 将时间戳直接转换为UTC+8（中国标准时间）
data.index = data.index.tz_convert('Asia/Shanghai')
data['Datetime'] = data.index
# 计算真实范围 (True Range, TR)
data['High-Low'] = data['High'] - data['Low']
data['High-Close'] = abs(data['High'] - data['Close'].shift())
data['Low-Close'] = abs(data['Low'] - data['Close'].shift())
data['TR'] = data[['High-Low', 'High-Close', 'Low-Close']].max(axis=1)

# 计算ATR（14期的移动平均）
data['ATR'] = data['TR'].rolling(window=14).mean()

# 计算RSI（14期）
delta = data['Close'].diff()  # 计算收盘价变化
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()  # 计算上涨幅度的平均值
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()  # 计算下跌幅度的平均值
rs = gain / loss  # 计算相对强度
data['RSI'] = 100 - (100 / (1 + rs))  # 计算RSI

# 计算MACD（默认12, 26, 9参数）
ema12 = data['Close'].ewm(span=12, adjust=False).mean()  # 计算12日EMA
ema26 = data['Close'].ewm(span=26, adjust=False).mean()  # 计算26日EMA
data['MACD'] = ema12 - ema26  # 计算MACD
data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()  # 计算MACD信号线

# 打印数据，确保输出时区为UTC+8，并展示RSI和MACD
print(data[['Datetime','Close', 'ATR', 'RSI', 'MACD', 'MACD_Signal']].tail(24).to_string(index=False))  # 输出最后24行数据
