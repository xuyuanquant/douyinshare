# 股票回测研究项目

一个基于Python的股票回测研究工具，支持数据下载、策略回测和结果分析。

## 功能特性

- 📊 下载股票历史K线数据（支持多种周期：5分钟、10分钟、30分钟、60分钟、日线等）
- 🔄 基于backtrader框架的策略回测
- 📈 回测结果可视化展示
- 🎯 支持多策略切换
- 💾 数据本地存储管理
- 🖥️ 命令行界面（基于Typer）

## 安装

1. 克隆项目
2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置Tushare API Token（在.env文件中）：
```
TUSHARE_TOKEN=your_tushare_token_here
```

## 使用方法

### 下载数据
```bash
# 下载单只股票数据
python main.py download --symbol 000001.SZ --period daily --start-date 2023-01-01 --end-date 2023-12-31

# 批量下载多只股票
python main.py download --symbols 000001.SZ,000002.SZ,600000.SH --period daily --start-date 2023-01-01 --end-date 2023-12-31
```

### 运行回测
```bash
# 使用默认策略回测
python main.py backtest --symbol 000001.SZ --period daily --start-date 2023-01-01 --end-date 2023-12-31

# 指定策略文件
python main.py backtest --symbol 000001.SZ --strategy strategies/ma_cross_strategy.py
```

## 项目结构

```
douyinshare/
├── main.py                 # 主程序入口
├── data/                   # 数据存储目录
├── strategies/             # 策略文件目录
├── utils/                  # 工具函数
├── config/                 # 配置文件
└── results/                # 回测结果
```

## 支持的周期

- 1min: 1分钟
- 5min: 5分钟
- 10min: 10分钟
- 15min: 15分钟
- 30min: 30分钟
- 60min: 60分钟
- daily: 日线
- weekly: 周线
- monthly: 月线 