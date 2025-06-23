import backtrader as bt

class MABOXBreakStrategy(bt.Strategy):
    params = (
        ('ma_fast', 5),
        ('ma_mid', 10),
        ('ma_slow', 60),
        ('box_period', 3),
        ('stake', 100),  # 最小交易单位
    )

    def __init__(self):
        self.ma5 = bt.indicators.SimpleMovingAverage(self.datas[0].close, period=self.p.ma_fast)
        self.ma10 = bt.indicators.SimpleMovingAverage(self.datas[0].close, period=self.p.ma_mid)
        self.ma60 = bt.indicators.SimpleMovingAverage(self.datas[0].close, period=self.p.ma_slow)
        self.ma60_slope = self.ma60 - self.ma60(-1)
        self.box_high = bt.indicators.Highest(self.datas[0].high, period=self.p.box_period)
        self.box_high.plotinfo.subplot = False
        self.box_low = bt.indicators.Lowest(self.datas[0].low, period=self.p.box_period)
        self.box_low.plotinfo.subplot = False
        self.buyprice = None
        self.in_box = False
        self.buy_signal_bar = None

    def next(self):
        pos = self.getposition().size
        price = self.datas[0].close[0]
        # 买入条件：股价上穿60均线且60均线向上
        if not pos:
            if (
                self.datas[0].close[-1] <= self.ma60[-1] and
                self.datas[0].close[0] > self.ma60[0] and
                self.ma60_slope[0] > 0
            ):
                # 记录箱体
                self.box_high_val = self.box_high[0]
                self.box_low_val = self.box_low[0]
                self.buy_signal_bar = len(self)
                # 计算可买股数（全仓，最小100股）
                cash = self.broker.get_cash()
                size = int(cash*0.95 // price // self.p.stake) * self.p.stake
                if size > 0:
                    print(f"买入: {size}股")
                    self.buy(size=size)
                    self.buyprice = price
                    self.in_box = True
                else:
                    print(f"资金不足，无法买入")
        # 卖出条件：5、10均线死叉
        else:
            if self.datas[0].close[0] < self.box_low_val or\
                self.datas[0].close[0] > self.box_high_val:
                self.in_box = False

            # 死叉
            if not self.in_box and self.ma5[0] < self.ma10[0]:
                self.close()
                self.buyprice = None
                self.in_box = False
                self.buy_signal_bar = None
            # 风控：买入后未突破箱体不止损
            elif self.buy_signal_bar is not None:
                # 若价格突破箱体则解除in_box
                if price > self.box_high_val or price < self.box_low_val:
                    self.in_box = False 

    def notify_order(self, order):
        print(f"订单状态: {order.getstatusname()}")