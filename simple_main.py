"""
股票回测研究项目主程序 - 简化版本
"""
import argparse
import sys
from pathlib import Path
import importlib.util

# 尝试导入依赖，如果失败则给出提示
try:
    from utils.data_downloader import DataDownloader
    from utils.backtest_engine import BacktestEngine
    from strategies import MACrossStrategy, RSIStrategy
    from config.settings import PERIOD_MAPPING
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请先安装依赖包: pip install -r requirements.txt")
    sys.exit(1)


def download_data(args):
    """下载数据"""
    try:
        downloader = DataDownloader()
        
        if args.symbol:
            stock_list = [args.symbol]
        else:
            stock_list = [s.strip() for s in args.symbols.split(",")]
        
        if len(stock_list) == 1:
            df = downloader.download_stock_data(
                symbol=stock_list[0],
                period=args.period,
                start_date=args.start_date,
                end_date=args.end_date,
                save=True
            )
            
            if not df.empty:
                print(f"✅ 成功下载 {stock_list[0]} 数据，共 {len(df)} 条记录")
            else:
                print(f"❌ 下载 {stock_list[0]} 数据失败")
        else:
            results = downloader.batch_download(
                symbols=stock_list,
                period=args.period,
                start_date=args.start_date,
                end_date=args.end_date
            )
            
            success_count = sum(1 for df in results.values() if not df.empty)
            print(f"✅ 批量下载完成: {success_count}/{len(stock_list)} 只股票成功")
            
    except Exception as e:
        print(f"❌ 下载失败: {str(e)}")
        sys.exit(1)


def run_backtest(args):
    """运行回测"""
    try:
        # 加载数据
        downloader = DataDownloader()
        df = downloader.load_local_data(args.symbol, args.period, args.start_date, args.end_date)
        
        if df.empty:
            print(f"❌ 未找到 {args.symbol} 的本地数据，请先下载数据")
            sys.exit(1)
        
        print(f"📊 加载数据: {args.symbol}, 共 {len(df)} 条记录")
        
        # 加载策略
        strategy_class = load_strategy(args.strategy)
        if not strategy_class:
            print(f"❌ 无法加载策略: {args.strategy}")
            sys.exit(1)
        
        # 解析策略参数
        strategy_params = {}
        if args.params:
            for param in args.params.split(","):
                if "=" in param:
                    key, value = param.split("=", 1)
                    strategy_params[key.strip()] = parse_param_value(value.strip())
        
        # 运行回测
        engine = BacktestEngine(cash=args.cash, commission=args.commission)
        results = engine.run_backtest(
            data=df,
            strategy_class=strategy_class,
            strategy_params=strategy_params,
            symbol=args.symbol
        )
        
        if results:
            engine.print_results()
            print("✅ 回测完成")
        else:
            print("❌ 回测失败")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 回测失败: {str(e)}")
        sys.exit(1)


def load_strategy(strategy_name):
    """加载策略"""
    # 内置策略
    builtin_strategies = {
        "ma_cross": MACrossStrategy,
        "rsi": RSIStrategy
    }
    
    if strategy_name in builtin_strategies:
        return builtin_strategies[strategy_name]
    
    # 从文件加载策略
    strategy_path = Path(strategy_name)
    if strategy_path.exists() and strategy_path.suffix == ".py":
        try:
            spec = importlib.util.spec_from_file_location("strategy", strategy_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找策略类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    hasattr(attr, '__bases__') and 
                    any('Strategy' in str(base) for base in attr.__bases__)):
                    return attr
            
            print(f"❌ 在文件 {strategy_path} 中未找到策略类")
            return None
            
        except Exception as e:
            print(f"❌ 加载策略文件失败: {str(e)}")
            return None
    
    print(f"❌ 未找到策略: {strategy_name}")
    return None


def parse_param_value(value):
    """解析参数值"""
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def list_strategies():
    """列出可用策略"""
    print("📋 可用策略:")
    print("  内置策略:")
    print("    - ma_cross: 移动平均线交叉策略")
    print("    - rsi: RSI策略")
    print("  自定义策略:")
    print("    - 指定 .py 文件路径")


def list_data():
    """列出已下载的数据"""
    from config.settings import DATA_DIR
    
    data_files = list(DATA_DIR.glob("*.csv"))
    
    if not data_files:
        print("📁 暂无已下载的数据")
        return
    
    print("📁 已下载的数据:")
    for file in sorted(data_files):
        print(f"  - {file.name}")


def main():
    parser = argparse.ArgumentParser(description="股票回测研究工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 下载命令
    download_parser = subparsers.add_parser('download', help='下载股票历史数据')
    download_parser.add_argument('--symbol', '-s', help='单只股票代码')
    download_parser.add_argument('--symbols', help='多只股票代码，用逗号分隔')
    download_parser.add_argument('--period', '-p', default='daily', help='数据周期')
    download_parser.add_argument('--start-date', required=True, help='开始日期 (YYYY-MM-DD)')
    download_parser.add_argument('--end-date', required=True, help='结束日期 (YYYY-MM-DD)')
    
    # 回测命令
    backtest_parser = subparsers.add_parser('backtest', help='运行回测')
    backtest_parser.add_argument('--symbol', '-s', required=True, help='股票代码')
    backtest_parser.add_argument('--period', '-p', default='daily', help='数据周期')
    backtest_parser.add_argument('--start-date', required=True, help='开始日期 (YYYY-MM-DD)')
    backtest_parser.add_argument('--end-date', required=True, help='结束日期 (YYYY-MM-DD)')
    backtest_parser.add_argument('--strategy', default='ma_cross', help='策略名称或策略文件路径')
    backtest_parser.add_argument('--cash', '-c', type=float, default=1000000, help='初始资金')
    backtest_parser.add_argument('--commission', type=float, default=0.001, help='手续费率')
    backtest_parser.add_argument('--params', help='策略参数，格式: param1=value1,param2=value2')
    
    # 其他命令
    subparsers.add_parser('list-strategies', help='列出可用策略')
    subparsers.add_parser('list-data', help='列出已下载的数据')
    
    args = parser.parse_args()
    
    if args.command == 'download':
        download_data(args)
    elif args.command == 'backtest':
        run_backtest(args)
    elif args.command == 'list-strategies':
        list_strategies()
    elif args.command == 'list-data':
        list_data()
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 