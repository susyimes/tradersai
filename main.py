import requests
import pandas as pd
import datetime
#这是BTC最近24小时数据与技术指标，帮忙分析一下走势，以及日内和中短期交易员策略建议
# 1. 获取 Kline 数据
url = "https://data-api.binance.vision/api/v3/klines"
params = {
    "symbol": "BTCUSDT",
    "interval": "1h",
    "limit": 48
}

response = requests.get(url, params=params)
if response.status_code == 200:
    klines = response.json()
else:
    print(f"获取数据失败: {response.status_code}")
    klines = []

# 2. 将数据转换为 DataFrame
columns = [
    'Open Time', 'Open', 'High', 'Low', 'Close', 'Volume',
    'Close Time', 'Quote Asset Volume', 'Number of Trades',
    'Taker Buy Base Asset Volume', 'Taker Buy Quote Asset Volume', 'Ignore'
]
data = pd.DataFrame(klines, columns=columns)

# 转换时间戳为日期格式
data['Open Time'] = pd.to_datetime(data['Open Time'], unit='ms')
data['Close Time'] = pd.to_datetime(data['Close Time'], unit='ms')
# 手动将时间从UTC转换为UTC+8
data['Open Time'] = data['Open Time'] + pd.Timedelta(hours=8)
# 转换相关价格和交易量数据为数值类型
for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
    data[col] = pd.to_numeric(data[col])

# 3. 计算技术指标

# --- 计算SMA和EMA ---
data['SMA20'] = data['Close'].rolling(window=20).mean()  # 20期简单移动平均
data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()  # 20期指数移动平均

# --- 计算布林带 ---
data['MiddleBand'] = data['Close'].rolling(window=20).mean()
data['StdDev'] = data['Close'].rolling(window=20).std()
data['UpperBand'] = data['MiddleBand'] + 2 * data['StdDev']
data['LowerBand'] = data['MiddleBand'] - 2 * data['StdDev']

# --- 计算随机指标 (Stochastic Oscillator) ---
low_min = data['Low'].rolling(window=14).min()
high_max = data['High'].rolling(window=14).max()
data['%K'] = (data['Close'] - low_min) / (high_max - low_min) * 100
data['%D'] = data['%K'].rolling(window=3).mean()

# --- 计算VWAP ---
data['TP'] = (data['High'] + data['Low'] + data['Close']) / 3
data['Cum_TP_Vol'] = (data['TP'] * data['Volume']).cumsum()
data['Cum_Vol'] = data['Volume'].cumsum()
data['VWAP'] = data['Cum_TP_Vol'] / data['Cum_Vol']

# --- 计算ATR（14期的移动平均） ---
data['High-Low'] = data['High'] - data['Low']
data['High-Close'] = abs(data['High'] - data['Close'].shift())
data['Low-Close'] = abs(data['Low'] - data['Close'].shift())
data['TR'] = data[['High-Low', 'High-Close', 'Low-Close']].max(axis=1)
data['ATR'] = data['TR'].rolling(window=14).mean()

# --- 计算RSI（14期） ---
delta = data['Close'].diff()
gain = delta.where(delta > 0, 0).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
data['RSI'] = 100 - (100 / (1 + rs))

# --- 计算MACD（默认参数12, 26, 9） ---
ema12 = data['Close'].ewm(span=12, adjust=False).mean()
ema26 = data['Close'].ewm(span=26, adjust=False).mean()
data['MACD'] = ema12 - ema26
data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

# 4. 打印整齐的表格 (选择部分指标)
header = (f"{'Open Time':20} {'Open':10} {'Volume':12} {'SMA20':10} {'EMA20':10} "
          f"{'UpperBand':10} {'LowerBand':10} {'%K':10} {'%D':10} {'VWAP':10} "
          f"{'ATR':10} {'RSI':10} {'MACD':10} {'MACD_Sig':10}")
print(header)
print("-" * len(header))

for index, row in data.tail(24).iterrows():
    open_time_str = row['Open Time'].strftime('%Y-%m-%d %H:%M')

    # 格式化数字，NaN值处理
    sma20_str = f"{row['SMA20']:.2f}" if pd.notna(row['SMA20']) else "N/A"
    ema20_str = f"{row['EMA20']:.2f}" if pd.notna(row['EMA20']) else "N/A"
    upper_band_str = f"{row['UpperBand']:.2f}" if pd.notna(row['UpperBand']) else "N/A"
    lower_band_str = f"{row['LowerBand']:.2f}" if pd.notna(row['LowerBand']) else "N/A"
    k_str = f"{row['%K']:.2f}" if pd.notna(row['%K']) else "N/A"
    d_str = f"{row['%D']:.2f}" if pd.notna(row['%D']) else "N/A"
    vwap_str = f"{row['VWAP']:.2f}" if pd.notna(row['VWAP']) else "N/A"
    atr_str = f"{row['ATR']:.2f}" if pd.notna(row['ATR']) else "N/A"
    rsi_str = f"{row['RSI']:.2f}" if pd.notna(row['RSI']) else "N/A"
    macd_str = f"{row['MACD']:.2f}" if pd.notna(row['MACD']) else "N/A"
    macd_signal_str = f"{row['MACD_Signal']:.2f}" if pd.notna(row['MACD_Signal']) else "N/A"

    print(f"{open_time_str:20} {row['Open']:10.2f} {row['Volume']:12.2f} {sma20_str:10} "
          f"{ema20_str:10} {k_str:10} {d_str:10} {upper_band_str:10} {lower_band_str:10}"
          f"{vwap_str:10} {atr_str:10} {rsi_str:10} {macd_str:10} {macd_signal_str:10}")
