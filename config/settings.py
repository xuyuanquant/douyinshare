"""
项目配置文件
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 数据目录
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"
STRATEGIES_DIR = BASE_DIR / "strategies"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)
STRATEGIES_DIR.mkdir(exist_ok=True)

# Tushare配置
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "")

# 掘金量化配置
gm_token = os.getenv("GM_TOKEN", "")

# 数据周期映射
PERIOD_MAPPING = {
    "1min": "1min",
    "5min": "5min", 
    "10min": "10min",
    "15min": "15min",
    "30min": "30min",
    "60min": "60min",
    "daily": "D",
    "weekly": "W",
    "monthly": "M"
}

# 回测默认参数
DEFAULT_CASH = 1000000  # 默认初始资金
DEFAULT_COMMISSION = 0.001  # 默认手续费率
DEFAULT_SLIPPAGE = 0.001  # 默认滑点

# 数据文件格式
DATA_FILE_FORMAT = "{symbol}_{period}_{start_date}_{end_date}.csv" 