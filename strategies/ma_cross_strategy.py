"""
移动平均线交叉策略
"""
import backtrader as bt


class MACrossStrategy(bt.Strategy):
    """
    移动平均线交叉策略
    
    参数:
        fast_period: 快速移动平均线周期
        slow_period: 慢速移动平均线周期
    """
    
    params = (
        ('fast_period', 10),  # 快速移动平均线周期
        ('slow_period', 30),  # 慢速移动平均线周期
    )
    
    def __init__(self):
        """初始化策略"""
        # 计算移动平均线
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.params.fast_period)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.params.slow_period)
        
        # 交叉信号
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
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
            # 没有持仓，检查买入信号
            if self.crossover > 0:  # 金叉
                self.log(f'买入信号, 价格: {self.data.close[0]:.2f}')
                self.order = self.buy()
        
        else:
            # 有持仓，检查卖出信号
            if self.crossover < 0:  # 死叉
                self.log(f'卖出信号, 价格: {self.data.close[0]:.2f}')
                self.order = self.sell() 