import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from config import settings
from .data_fetcher import DataFetcher
from .indicators import TechnicalIndicators
from .patterns import CandlestickPatterns

logger = logging.getLogger(__name__)

class SignalEngine:
    def __init__(self, data_fetcher: DataFetcher, indicators: TechnicalIndicators, patterns: CandlestickPatterns):
        self.data_fetcher = data_fetcher
        self.indicators = indicators
        self.patterns = patterns
        self._history = []
        self._stats = {'win_count': 0, 'loss_count': 0, 'win_rate': 0.0}

    def _process_df_to_signal(self, df, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        if df is None or df.empty or len(df) < 5:
            return None

        df = self.indicators.calculate_all(df)
        ind_analysis = self.indicators.analyze(df)
        pat_analysis = self.patterns.analyze(df)

        buy_count = sum(1 for val in ind_analysis.values() if val['signal'] == 'BUY')
        sell_count = sum(1 for val in ind_analysis.values() if val['signal'] == 'SELL')
        total_ind = len(ind_analysis) if len(ind_analysis) > 0 else 1

        direction = 'NEUTRAL'
        confidence = 0.0

        if buy_count > sell_count:
            direction = 'BUY'
            confidence = (buy_count / total_ind) * 100
        elif sell_count > buy_count:
            direction = 'SELL'
            confidence = (sell_count / total_ind) * 100

        # Pattern bonus
        if direction != 'NEUTRAL':
            for pat in pat_analysis:
                if pat['signal'] == direction:
                    confidence += pat['strength'] * 10

        confidence = min(100.0, confidence)

        if confidence >= settings.SIGNAL_MEDIUM_THRESHOLD and direction != 'NEUTRAL':
            price = df.iloc[-1]['Close']
            signal = {
                'symbol': symbol,
                'display_name': settings.PAIR_DISPLAY_NAMES.get(symbol, symbol),
                'direction': direction,
                'confidence': round(confidence, 2),
                'timeframe': timeframe,
                'price': float(price),
                'indicators': ind_analysis,
                'patterns': pat_analysis,
                'timestamp': datetime.now(),
                'chart_path': None
            }
            self._add_to_history(signal)
            return signal

        return None

    def generate_signal(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        df = self.data_fetcher.fetch_data(symbol, timeframe)
        return self._process_df_to_signal(df, symbol, timeframe)

    async def generate_signal_async(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        df = await self.data_fetcher.fetch_data_async(symbol, timeframe)
        return self._process_df_to_signal(df, symbol, timeframe)

    def scan_all(self, timeframe: str = 'M5') -> List[Dict[str, Any]]:
        signals = []
        for symbol in settings.CURRENCY_PAIRS:
            sig = self.generate_signal(symbol, timeframe)
            if sig:
                signals.append(sig)
        return signals

    async def scan_all_async(self, timeframe: str = 'M5') -> List[Dict[str, Any]]:
        signals = []
        for symbol in settings.CURRENCY_PAIRS:
            sig = await self.generate_signal_async(symbol, timeframe)
            if sig:
                signals.append(sig)
        return signals

    def scan_all_timeframes(self) -> Dict[str, List[Dict[str, Any]]]:
        results = {}
        for tf in settings.TIMEFRAMES.keys():
            results[tf] = self.scan_all(tf)
        return results

    def _add_to_history(self, signal: Dict[str, Any]):
        self._history.insert(0, signal)
        if len(self._history) > 100:
            self._history.pop()

    def get_history(self) -> List[Dict[str, Any]]:
        return self._history

    def get_stats(self) -> Dict[str, Any]:
        total = self._stats['win_count'] + self._stats['loss_count']
        if total > 0:
            self._stats['win_rate'] = round((self._stats['win_count'] / total) * 100, 2)
        return self._stats
