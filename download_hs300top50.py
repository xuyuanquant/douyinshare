import os
from utils.data_downloader import DataDownloader

# 掘金量化API
from gm.api import set_token, stk_get_index_constituents
from config.settings import gm_token

if not gm_token:
    raise ValueError("请在环境变量或.env中设置GM_TOKEN")
set_token(gm_token)

# 获取沪深300成分股（指数代码：SHSE.000300）
constituents = stk_get_index_constituents(index='SHSE.000300')
# 取前50只股票
stock_list = constituents['symbol'].tolist()[:50]

print(f"沪深300前50只股票: {stock_list}")

downloader = DataDownloader()

for symbol in stock_list:
    print(f"下载 {symbol} 的60分钟K线数据...")
    # symbol格式转换: SZSE.000001 -> 000001.SZ, SHSE.600000 -> 600000.SH
    if symbol.startswith('SZSE.'):
        ts_symbol = symbol[5:] + '.SZ'
    elif symbol.startswith('SHSE.'):
        ts_symbol = symbol[5:] + '.SH'
    else:
        ts_symbol = symbol
    downloader.download_stock_data(ts_symbol, '60min', '2023-01-01', '2023-12-31', save=True) 