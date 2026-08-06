import sys
try:
    import websockets
    if not hasattr(websockets, 'asyncio'):
        import types
        _asyncio_mod = types.ModuleType('asyncio')
        _client_mod = types.ModuleType('client')
        _client_mod.connect = websockets.connect
        _asyncio_mod.client = _client_mod
        websockets.asyncio = _asyncio_mod
        sys.modules['websockets.asyncio'] = _asyncio_mod
        sys.modules['websockets.asyncio.client'] = _client_mod
except Exception:
    pass

from .data_fetcher import DataFetcher
from .indicators import TechnicalIndicators
from .patterns import CandlestickPatterns
from .signal_engine import SignalEngine
from .chart_generator import ChartGenerator
from .po_trader import PocketOptionTrader, MartingaleManager

__all__ = [
    'DataFetcher',
    'TechnicalIndicators',
    'CandlestickPatterns',
    'SignalEngine',
    'ChartGenerator',
    'PocketOptionTrader',
    'MartingaleManager'
]
