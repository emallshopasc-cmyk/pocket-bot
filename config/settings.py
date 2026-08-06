import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TELEGRAM_BOT_TOKEN = '8941505352:AAHsWfhljzdi9hH-pdjzsfA86Ih1YzBEBLA'

CURRENCY_PAIRS = [
    'EURUSD_otc', 'GBPUSD_otc', 'USDJPY_otc', 'AUDUSD_otc', 
    'AUDCAD_otc', 'USDCAD_otc', 'EURGBP_otc', 'EURJPY_otc',
    'EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X'
]

PAIR_DISPLAY_NAMES = {
    'EURUSD_otc': 'EUR/USD OTC',
    'GBPUSD_otc': 'GBP/USD OTC',
    'USDJPY_otc': 'USD/JPY OTC',
    'AUDUSD_otc': 'AUD/USD OTC',
    'AUDCAD_otc': 'AUD/CAD OTC',
    'USDCAD_otc': 'USD/CAD OTC',
    'EURGBP_otc': 'EUR/GBP OTC',
    'EURJPY_otc': 'EUR/JPY OTC',
    'EURUSD=X': 'EUR/USD',
    'GBPUSD=X': 'GBP/USD',
    'USDJPY=X': 'USD/JPY',
    'AUDUSD=X': 'AUD/USD',
    'USDCHF=X': 'USD/CHF',
    'NZDUSD=X': 'NZD/USD',
    'EURGBP=X': 'EUR/GBP',
    'EURJPY=X': 'EUR/JPY'
}

TIMEFRAMES = {'M1': '1m', 'M5': '5m', 'M15': '15m'}
TIMEFRAME_PERIODS = {'M1': '1d', 'M5': '5d', 'M15': '15d'}

RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

BB_PERIOD = 20
BB_STD = 2

SMA_SHORT = 50
SMA_LONG = 200

EMA_SHORT = 9
EMA_LONG = 21

STOCH_K = 14
STOCH_D = 3
STOCH_OVERSOLD = 20
STOCH_OVERBOUGHT = 80

ATR_PERIOD = 14

SIGNAL_STRONG_THRESHOLD = 75
SIGNAL_MEDIUM_THRESHOLD = 50  # Tez-tez və sürətli 5-10s siqnallar üçün hədd

WEB_HOST = '0.0.0.0'
WEB_PORT = 5000

SCAN_INTERVAL_SECONDS = 2  # Hər 2 saniyədən bir ildırım skan!
TARGET_WIN_COUNT = 5        # 5 Qazanc Hədəfi!
DEFAULT_TRADE_DURATION = 30 # 30 Saniyəlik Turbo Opsionlar (S30)!

CHART_DIR = os.path.join(BASE_DIR, 'charts')

LOG_LEVEL = 'INFO'
DATA_CACHE_SECONDS = 1

# ============================================
# Pocket Option & Martingale Konfiqurasiyası
# ============================================
PO_SSID = '42["auth",{"session":"bkalk3kp4bgm91033ln96qeccv","isDemo":1,"uid":137750196,"platform":2}]'
PO_IS_DEMO = True

MARTINGALE_ENABLED = True
MARTINGALE_MAX_STEPS = 4
MARTINGALE_MULTIPLIER = 2.5
MARTINGALE_BASE_AMOUNT = 1.0

TIMEFRAME_SECONDS = {
    'S5': 5,
    'S10': 10,
    'M1': 60,
    'M5': 300,
    'M15': 900
}

# yfinance simvollarının Pocket Option aktiv adlarına uyğunlaşdırılması
PO_ASSET_MAPPING = {
    'EURUSD_otc': 'EURUSD_otc',
    'GBPUSD_otc': 'GBPUSD_otc',
    'USDJPY_otc': 'USDJPY_otc',
    'AUDUSD_otc': 'AUDUSD_otc',
    'AUDCAD_otc': 'AUDCAD_otc',
    'USDCAD_otc': 'USDCAD_otc',
    'EURGBP_otc': 'EURGBP_otc',
    'EURJPY_otc': 'EURJPY_otc',
    'EURUSD=X': 'EURUSD_otc',
    'GBPUSD=X': 'GBPUSD_otc',
    'USDJPY=X': 'USDJPY_otc',
    'AUDUSD=X': 'AUDUSD_otc'
}

