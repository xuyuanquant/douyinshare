"""
回测引擎
"""
import backtrader as bt
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import matplotlib.pyplot as plt

from config.settings import DEFAULT_CASH, DEFAULT_COMMISSION, DEFAULT_SLIPPAGE, RESULTS_DIR


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, cash: float = DEFAULT_CASH, commission: float = DEFAULT_COMMISSION):
        self.cash = cash
        self.commission = commission
        self.cerebro = None
        self.results = {}
        
    def run_backtest(self, data: pd.DataFrame, strategy_class: bt.Strategy, 
                    strategy_params: Dict[str, Any] = None, symbol: str = "UNKNOWN") -> Dict[str, Any]:
        """运行回测"""
        if data.empty:
            print("警告: 数据为空，无法进行回测")
            return {}
        
        # 创建Cerebro引擎
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(self.cash)
        self.cerebro.broker.setcommission(commission=self.commission)
        self.cerebro.broker.set_slippage_perc(DEFAULT_SLIPPAGE)
        
        # 创建数据源
        data_feed = self._create_data_feed(data)
        self.cerebro.adddata(data_feed)
        
        # 添加策略
        if strategy_params:
            self.cerebro.addstrategy(strategy_class, **strategy_params)
        else:
            self.cerebro.addstrategy(strategy_class)
        
        # 添加分析器
        self._add_analyzers()
        
        # 运行回测
        print(f"开始回测 {symbol}...")
        initial_value = self.cerebro.broker.getvalue()
        results = self.cerebro.run()
        self.cerebro.plot(style='candlestick')
        final_value = self.cerebro.broker.getvalue()
        
        # 收集结果
        self.results = self._collect_results(results, initial_value, final_value, symbol)
        return self.results
    
    def _create_data_feed(self, data: pd.DataFrame) -> bt.feeds.PandasData:
        """创建数据源"""
        # 确保数据格式正确
        column_mapping = {
            'Open': 'open', 'High': 'high', 'Low': 'low',
            'Close': 'close', 'Volume': 'volume'
        }
        data = data.rename(columns=column_mapping)
        
        # 确保所有必要列存在
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in data.columns:
                data[col] = data['close']
        
        return bt.feeds.PandasData(
            dataname=data,
            datetime=None,
            open='open', high='high', low='low', close='close', volume='volume',
            openinterest=-1
        )
    
    def _add_analyzers(self):
        """添加分析器"""
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    def _collect_results(self, results, initial_value: float, final_value: float, symbol: str) -> Dict[str, Any]:
        """收集回测结果"""
        if not results:
            return {}
        
        strategy = results[0]
        total_return = (final_value - initial_value) / initial_value * 100
        
        # 获取分析器结果
        sharpe_ratio = strategy.analyzers.sharpe.get_analysis()
        drawdown = strategy.analyzers.drawdown.get_analysis()
        trades = strategy.analyzers.trades.get_analysis()
        
        return {
            'symbol': symbol,
            'initial_value': initial_value,
            'final_value': final_value,
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio.get('sharperatio', 0),
            'max_drawdown': drawdown.get('max', {}).get('drawdown', 0),
            'total_trades': trades.get('total', {}).get('total', 0),
            'win_trades': trades.get('won', {}).get('total', 0),
            'loss_trades': trades.get('lost', {}).get('total', 0),
            'win_rate': trades.get('won', {}).get('total', 0) / max(trades.get('total', {}).get('total', 1), 1) * 100
        }
    
    def print_results(self):
        """打印回测结果"""
        if not self.results:
            print("没有可用的回测结果")
            return
        
        print("\n" + "="*50)
        print(f"回测结果 - {self.results['symbol']}")
        print("="*50)
        print(f"初始资金: {self.results['initial_value']:,.2f}")
        print(f"最终资金: {self.results['final_value']:,.2f}")
        print(f"总收益率: {self.results['total_return']:.2f}%")
        if self.results['sharpe_ratio'] is not None:
            print(f"夏普比率: {self.results['sharpe_ratio']:.3f}")
        print(f"最大回撤: {self.results['max_drawdown']:.2f}%")
        print(f"总交易次数: {self.results['total_trades']}")
        print(f"胜率: {self.results['win_rate']:.1f}%")
        print("="*50) 