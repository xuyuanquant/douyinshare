"""
股票回测研究项目主程序
"""
import typer
from typing import List, Optional
from pathlib import Path
import importlib.util
import sys

from utils.data_downloader import DataDownloader
from utils.backtest_engine import BacktestEngine
from strategies import MACrossStrategy, RSIStrategy, MABOXBreakStrategy
from config.settings import PERIOD_MAPPING

app = typer.Typer(help="股票回测研究工具")


@app.command()
def download(
    symbol: str = typer.Option(None, "--symbol", "-s", help="单只股票代码"),
    symbols: str = typer.Option(None, "--symbols", help="多只股票代码，用逗号分隔"),
    period: str = typer.Option("daily", "--period", "-p", help="数据周期"),
    start_date: str = typer.Option(..., "--start-date", help="开始日期 (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., "--end-date", help="结束日期 (YYYY-MM-DD)"),
    force: bool = typer.Option(False, "--force", "-f", help="强制重新下载")
):
    """下载股票历史数据"""
    
    # 验证周期参数
    if period not in PERIOD_MAPPING:
        typer.echo(f"错误: 不支持的周期 {period}")
        typer.echo(f"支持的周期: {', '.join(PERIOD_MAPPING.keys())}")
        raise typer.Exit(1)
    
    # 处理股票代码
    if symbol and symbols:
        typer.echo("错误: 不能同时指定 --symbol 和 --symbols")
        raise typer.Exit(1)
    
    if not symbol and not symbols:
        typer.echo("错误: 必须指定 --symbol 或 --symbols")
        raise typer.Exit(1)
    
    if symbol:
        stock_list = [symbol]
    else:
        stock_list = [s.strip() for s in symbols.split(",")]
    
    try:
        # 初始化下载器
        downloader = DataDownloader()
        
        if len(stock_list) == 1:
            # 单只股票下载
            df = downloader.download_stock_data(
                symbol=stock_list[0],
                period=period,
                start_date=start_date,
                end_date=end_date,
                save=True
            )
            
            if not df.empty:
                typer.echo(f"✅ 成功下载 {stock_list[0]} 数据，共 {len(df)} 条记录")
            else:
                typer.echo(f"❌ 下载 {stock_list[0]} 数据失败")
        else:
            # 批量下载
            results = downloader.batch_download(
                symbols=stock_list,
                period=period,
                start_date=start_date,
                end_date=end_date
            )
            
            success_count = sum(1 for df in results.values() if not df.empty)
            typer.echo(f"✅ 批量下载完成: {success_count}/{len(stock_list)} 只股票成功")
            
    except Exception as e:
        typer.echo(f"❌ 下载失败: {str(e)}")
        raise typer.Exit(1)


@app.command()
def backtest(
    symbol: str = typer.Option(..., "--symbol", "-s", help="股票代码"),
    period: str = typer.Option("daily", "--period", "-p", help="数据周期"),
    start_date: str = typer.Option(..., "--start-date", help="开始日期 (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., "--end-date", help="结束日期 (YYYY-MM-DD)"),
    strategy: str = typer.Option("ma_cross", "--strategy", help="策略名称或策略文件路径"),
    cash: float = typer.Option(1000000, "--cash", "-c", help="初始资金"),
    commission: float = typer.Option(0.001, "--commission", help="手续费率"),
    params: str = typer.Option(None, "--params", help="策略参数，格式: param1=value1,param2=value2")
):
    """运行回测"""
    
    # 验证周期参数
    if period not in PERIOD_MAPPING:
        typer.echo(f"错误: 不支持的周期 {period}")
        typer.echo(f"支持的周期: {', '.join(PERIOD_MAPPING.keys())}")
        raise typer.Exit(1)
    
    try:
        # 加载数据
        downloader = DataDownloader()
        df = downloader.load_local_data(symbol, period, start_date, end_date)
        
        if df.empty:
            typer.echo(f"❌ 未找到 {symbol} 的本地数据，请先下载数据")
            raise typer.Exit(1)
        
        typer.echo(f"📊 加载数据: {symbol}, 共 {len(df)} 条记录")
        
        # 加载策略
        strategy_class = load_strategy(strategy)
        if not strategy_class:
            typer.echo(f"❌ 无法加载策略: {strategy}")
            raise typer.Exit(1)
        
        # 解析策略参数
        strategy_params = {}
        if params:
            for param in params.split(","):
                if "=" in param:
                    key, value = param.split("=", 1)
                    strategy_params[key.strip()] = parse_param_value(value.strip())
        
        # 运行回测
        engine = BacktestEngine(cash=cash, commission=commission)
        results = engine.run_backtest(
            data=df,
            strategy_class=strategy_class,
            strategy_params=strategy_params,
            symbol=symbol
        )
        
        if results:
            engine.print_results()
            typer.echo("✅ 回测完成")
        else:
            typer.echo("❌ 回测失败")
            raise typer.Exit(1)
            
    except Exception as e:
        typer.echo(f"❌ 回测失败: {str(e)}")
        raise typer.Exit(1)


def load_strategy(strategy_name: str):
    """加载策略"""
    # 内置策略
    builtin_strategies = {
        "ma_cross": MACrossStrategy,
        "rsi": RSIStrategy,
        "ma_box_break": MABOXBreakStrategy
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
            
            # 查找策略类（假设策略类名以Strategy结尾）
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    hasattr(attr, '__bases__') and 
                    any('Strategy' in str(base) for base in attr.__bases__)):
                    return attr
            
            typer.echo(f"❌ 在文件 {strategy_path} 中未找到策略类")
            return None
            
        except Exception as e:
            typer.echo(f"❌ 加载策略文件失败: {str(e)}")
            return None
    
    typer.echo(f"❌ 未找到策略: {strategy_name}")
    return None


def parse_param_value(value: str):
    """解析参数值"""
    try:
        # 尝试转换为整数
        return int(value)
    except ValueError:
        try:
            # 尝试转换为浮点数
            return float(value)
        except ValueError:
            # 保持字符串
            return value


@app.command()
def list_strategies():
    """列出可用策略"""
    typer.echo("📋 可用策略:")
    typer.echo("  内置策略:")
    typer.echo("    - ma_cross: 移动平均线交叉策略")
    typer.echo("    - rsi: RSI策略")
    typer.echo("  自定义策略:")
    typer.echo("    - 指定 .py 文件路径")


@app.command()
def list_data():
    """列出已下载的数据"""
    from config.settings import DATA_DIR
    
    data_files = list(DATA_DIR.glob("*.csv"))
    
    if not data_files:
        typer.echo("📁 暂无已下载的数据")
        return
    
    typer.echo("📁 已下载的数据:")
    for file in sorted(data_files):
        typer.echo(f"  - {file.name}")


if __name__ == "__main__":
    app() 