"""
数据下载工具
"""
import tushare as ts
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import time

from config.settings import TUSHARE_TOKEN, DATA_DIR, PERIOD_MAPPING, DATA_FILE_FORMAT, gm_token

# 新增掘金量化API导入
try:
    from gm.api import set_token, history
    gm_api_available = True
except ImportError:
    print("掘金量化API未安装")
    gm_api_available = False

class DataDownloader:
    """股票数据下载器"""
    
    def __init__(self):
        """初始化下载器"""
        if not TUSHARE_TOKEN:
            raise ValueError("请设置TUSHARE_TOKEN环境变量")
        
        ts.set_token(TUSHARE_TOKEN)
        self.pro = ts.pro_api()
        
        # 掘金token
        self.gm_token = gm_token
        if gm_api_available and self.gm_token:
            set_token(self.gm_token)
        
    def download_stock_data(
        self,
        symbol: str,
        period: str,
        start_date: str,
        end_date: str,
        save: bool = True
    ) -> pd.DataFrame:
        """
        下载股票数据
        
        Args:
            symbol: 股票代码
            period: 数据周期
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            save: 是否保存到本地
            
        Returns:
            DataFrame: 股票数据
        """
        print(f"正在下载 {symbol} 的 {period} 数据...")
        
        try:
            # 分钟级别优先用掘金量化API
            if period in ['1min', '5min', '10min', '15min', '30min', '60min'] and gm_api_available and self.gm_token:
                df = self._download_minute_data_gm(symbol, period, start_date, end_date)
            elif period in ['1min', '5min', '10min', '15min', '30min', '60min']:
                df = self._download_minute_data(symbol, period, start_date, end_date)
            else:
                df = self._download_daily_data(symbol, period, start_date, end_date)
            
            if df is None or df.empty:
                print(f"警告: {symbol} 在指定时间段内没有数据")
                return pd.DataFrame()
            
            # 数据清洗和格式化
            df = self._clean_data(df)
            
            # 保存数据
            if save:
                self._save_data(df, symbol, period, start_date, end_date)
            
            print(f"成功下载 {symbol} 数据，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            print(f"下载 {symbol} 数据失败: {str(e)}")
            return pd.DataFrame()
    
    def _download_minute_data(self, symbol: str, period: str, start_date: str, end_date: str) -> pd.DataFrame:
        """下载分钟级数据"""
        # 注意：分钟级数据需要特殊处理，这里简化处理
        # 实际使用时可能需要根据tushare的具体API调整
        try:
            # 使用pro_bar获取分钟数据
            df = self.pro.stk_mins(
                ts_code=symbol,
                freq=period,
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                fields='ts_code,trade_time,open,high,low,close,vol,amount'
            )
            return df
        except:
            # 如果分钟数据API不可用，返回空DataFrame
            print(f"分钟级数据API暂不可用，请使用日线数据")
            return pd.DataFrame()
    
    def _download_daily_data(self, symbol: str, period: str, start_date: str, end_date: str) -> pd.DataFrame:
        """下载日线及以上数据"""
        try:
            df = self.pro.daily(
                ts_code=symbol,
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
            )
            return df
        except Exception as e:
            print(f"下载日线数据失败: {str(e)}")
            return pd.DataFrame()
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗和格式化数据"""
        if df.empty:
            return df
        
        # 重命名列以符合backtrader要求
        column_mapping = {
            'trade_date': 'datetime',
            'trade_time': 'datetime',
            'vol': 'volume',
            'amount': 'amount'
        }
        df = df.rename(columns=column_mapping)
        
        # 处理日期时间
        if 'datetime' in df.columns:
            if 'trade_date' in df.columns:
                df['datetime'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            elif 'trade_time' in df.columns:
                df['datetime'] = pd.to_datetime(df['trade_time'])
        
        # 确保必要的列存在
        required_columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                if col == 'volume' and 'vol' in df.columns:
                    df['volume'] = df['vol']
                else:
                    print(f"警告: 缺少必要列 {col}")
        
        # 按日期排序
        df = df.sort_values('datetime').reset_index(drop=True)
        
        # 设置datetime为索引
        df.set_index('datetime', inplace=True)
        
        return df
    
    def _save_data(self, df: pd.DataFrame, symbol: str, period: str, start_date: str, end_date: str):
        """保存数据到本地"""
        if df.empty:
            return
        
        filename = DATA_FILE_FORMAT.format(
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        filepath = DATA_DIR / filename
        df.to_csv(filepath)
        print(f"数据已保存到: {filepath}")
    
    def batch_download(
        self,
        symbols: List[str],
        period: str,
        start_date: str,
        end_date: str
    ) -> dict:
        """
        批量下载多只股票数据
        
        Args:
            symbols: 股票代码列表
            period: 数据周期
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            dict: 每只股票的数据DataFrame
        """
        results = {}
        
        for i, symbol in enumerate(symbols, 1):
            print(f"进度: {i}/{len(symbols)} - {symbol}")
            
            df = self.download_stock_data(symbol, period, start_date, end_date)
            results[symbol] = df
            
            # 避免请求过于频繁
            if i < len(symbols):
                time.sleep(0.5)
        
        return results
    
    def load_local_data(self, symbol: str, period: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从本地加载数据"""
        filename = DATA_FILE_FORMAT.format(
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        filepath = DATA_DIR / filename
        
        if filepath.exists():
            df = pd.read_csv(filepath, index_col=0, parse_dates=True)
            print(f"从本地加载数据: {filepath}")
            return df
        else:
            print(f"本地数据文件不存在: {filepath}")
            return pd.DataFrame()

    def _download_minute_data_gm(self, symbol: str, period: str, start_date: str, end_date: str) -> pd.DataFrame:
        """用掘金量化API下载分钟级数据，bob作为datetime"""
        try:
            # symbol格式转换: 000001.SZ -> SZSE.000001
            if symbol.endswith('.SZ'):
                gm_symbol = f'SZSE.{symbol[:6]}'
            elif symbol.endswith('.SH'):
                gm_symbol = f'SHSE.{symbol[:6]}'
            else:
                gm_symbol = symbol
            # period格式转换: 5min -> 5m, 1min -> 1m, 60min -> 60m
            freq_map = {'1min': '1m', '5min': '5m', '10min': '10m', '15min': '15m', '30min': '30m', '60min': '60m'}
            gm_period = freq_map.get(period, period)
            # 掘金API要求时间格式: yyyy-mm-dd HH:MM:SS
            start_time = start_date + ' 09:00:00'
            end_time = end_date + ' 15:30:00'
            df = history(symbol=gm_symbol, frequency=gm_period, start_time=start_time, end_time=end_time,
                         fields='open,high,low,close,volume,bob', df=True)
            if 'bob' in df.columns:
                df['datetime'] = pd.to_datetime(df['bob'])
                df.drop(columns=['bob'], inplace=True)
            print(f"掘金API分钟数据获取成功: {df}")
            return df
        except Exception as e:
            print(f"掘金API分钟数据获取失败: {e}")
            return pd.DataFrame() 