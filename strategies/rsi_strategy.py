"""
RSI策略
"""
import backtrader as bt


class RSIStrategy(bt.Strategy):
    """
    RSI策略
    
    参数:
        rsi_period: RSI计算周期
        oversold: 超卖阈值
        overbought: 超买阈值
    """
    
    params = (
        ('rsi_period', 14),    # RSI周期
        ('oversold', 30),      # 超卖阈值
        ('overbought', 70),    # 超买阈值
    )
    
    def __init__(self):
        """初始化策略"""
        # 计算RSI
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        
        # 记录交易
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
    def log(self, txt, dt=None):
        """记录日志"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行, 价格: {order.executed.price:.2f}, '
                        f'成本: {order.executed.value:.2f}, '
                        f'手续费: {order.executed.comm:.2f}')
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(f'卖出执行, 价格: {order.executed.price:.2f}, '
                        f'成本: {order.executed.value:.2f}, '
                        f'手续费: {order.executed.comm:.2f}')
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')
        
        self.order = None
    
    def notify_trade(self, trade):
        """交易完成通知"""
        if not trade.isclosed:
            return
        
        self.log(f'交易利润, 毛利润: {trade.pnl:.2f}, 净利润: {trade.pnlcomm:.2f}')
    
    def next(self):
        """策略逻辑"""
        # 检查是否有未完成的订单
        if self.order:
            return
        
        # 检查是否持仓
        if not self.position:
            # 没有持仓，检查买入信号（RSI超卖）
            if self.rsi[0] < self.params.oversold:
                self.log(f'RSI超卖买入信号, RSI: {self.rsi[0]:.2f}, 价格: {self.data.close[0]:.2f}')
                self.order = self.buy()
        
        else:
            # 有持仓，检查卖出信号（RSI超买）
            if self.rsi[0] > self.params.overbought:
                self.log(f'RSI超买卖出信号, RSI: {self.rsi[0]:.2f}, 价格: {self.data.close[0]:.2f}')
                self.order = self.sell() 