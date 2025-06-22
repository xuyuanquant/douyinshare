"""
使用示例
"""
import pandas as pd
from utils.data_downloader import DataDownloader
from utils.backtest_engine import BacktestEngine
from strategies import MACrossStrategy, RSIStrategy


def example_download_and_backtest():
    """示例：下载数据并运行回测"""
    
    print("=== 股票回测研究项目示例 ===\n")
    
    # 1. 下载数据（需要先设置TUSHARE_TOKEN）
    try:
        downloader = DataDownloader()
        
        # 下载平安银行2023年的日线数据
        print("1. 下载数据...")
        df = downloader.download_stock_data(
            symbol="000001.SZ",
            period="daily",
            start_date="2023-01-01",
            end_date="2023-12-31",
            save=True
        )
        
        if df.empty:
            print("❌ 数据下载失败，请检查TUSHARE_TOKEN设置")
            return
        
        print(f"✅ 数据下载成功，共 {len(df)} 条记录\n")
        
        # 2. 运行移动平均线策略回测
        print("2. 运行移动平均线交叉策略回测...")
        engine = BacktestEngine(cash=1000000, commission=0.001)
        
        results = engine.run_backtest(
            data=df,
            strategy_class=MACrossStrategy,
            strategy_params={'fast_period': 5, 'slow_period': 20},
            symbol="000001.SZ"
        )
        
        if results:
            engine.print_results()
        
        # 3. 运行RSI策略回测
        print("\n3. 运行RSI策略回测...")
        results = engine.run_backtest(
            data=df,
            strategy_class=RSIStrategy,
            strategy_params={'rsi_period': 14, 'oversold': 30, 'overbought': 70},
            symbol="000001.SZ"
        )
        
        if results:
            engine.print_results()
            
    except Exception as e:
        print(f"❌ 示例运行失败: {str(e)}")
        print("请确保已设置TUSHARE_TOKEN环境变量")


def example_custom_strategy():
    """示例：创建自定义策略"""
    
    print("\n=== 自定义策略示例 ===\n")
    
    # 这里展示如何创建一个简单的双均线策略
    strategy_code = '''
import backtrader as bt

class CustomStrategy(bt.Strategy):
    params = (
        ('ma1', 5),
        ('ma2', 10),
    )
    
    def __init__(self):
        self.ma1 = bt.indicators.SMA(self.data.close, period=self.params.ma1)
        self.ma2 = bt.indicators.SMA(self.data.close, period=self.params.ma2)
        self.crossover = bt.indicators.CrossOver(self.ma1, self.ma2)
    
    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        else:
            if self.crossover < 0:
                self.sell()
'''
    
    print("自定义策略代码示例:")
    print(strategy_code)
    print("使用方法:")
    print("1. 将策略代码保存为 .py 文件")
    print("2. 运行: python main.py backtest --symbol 000001.SZ --strategy your_strategy.py")


if __name__ == "__main__":
    example_download_and_backtest()
    example_custom_strategy() 