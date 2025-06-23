import os
import glob
import matplotlib.pyplot as plt
import backtrader as bt
import pandas as pd
from strategies.ma_box_break_strategy import MABOXBreakStrategy

DATA_DIR = 'data'  # 假设下载数据都在results目录
PERIOD = '60min'
START_DATE = '2023-01-01'
END_DATE = '2023-12-31'

# 获取所有已下载的沪深300前50只股票的60min数据文件
pattern = os.path.join(DATA_DIR, f'*_{PERIOD}.csv')
file_list = sorted(glob.glob(pattern))

if not file_list:
    print('未找到任何60min数据文件，请先下载数据！')
    exit(1)

for file in file_list:
    # 从文件名提取股票代码
    basename = os.path.basename(file)
    symbol = basename.split('_')[0]
    print(f'回测: {symbol}')
    # 读取数据
    df = pd.read_csv(file, parse_dates=['datetime'])
    df = df[(df['datetime'] >= START_DATE) & (df['datetime'] <= END_DATE)]
    df = df.sort_values('datetime')
    # 构造backtrader数据
    data = bt.feeds.PandasData(
        dataname=df,
        datetime='datetime',
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        openinterest=None,
        timeframe=bt.TimeFrame.Minutes,
        compression=60
    )
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MABOXBreakStrategy)
    cerebro.adddata(data, name=symbol)
    cerebro.broker.setcash(100000)
    print(f'初始资金: {cerebro.broker.getvalue():.2f}')
    result = cerebro.run()
    print(f'回测结束资金: {cerebro.broker.getvalue():.2f}')
    # 绘制净值曲线
    cerebro.plot(style='candlestick', volume=False, iplot=False) 