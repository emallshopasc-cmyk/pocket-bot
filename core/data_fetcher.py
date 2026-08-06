import time
import logging
import asyncio
import pandas as pd
import yfinance as yf
from typing import Dict, Optional
from config import settings

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Bazar datalarını ultra-sürətli alma modulu.
    OTC cütlükləri üçün yalnız Pocket Option WebSocket və ya in-memory keşi istifadə edir.
    Heç vaxt OTC cütlüklər üçün yfinance bloklayıcı şəbəkə gözləməsi etmir!
    """

    def __init__(self, po_trader=None):
        self.po_trader = po_trader
        self._cache = {}

    async def fetch_data_async(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """
        Async olaraq şam datalarını ildırım sürətilə yükləyir (< 0.1s).
        """
        cache_key = f"{symbol}_{timeframe}"
        now = time.time()

        if cache_key in self._cache:
            cache_time, data = self._cache[cache_key]
            if now - cache_time < settings.DATA_CACHE_SECONDS:
                return data

        # 1. OTC cütdürsə — Yalnız Pocket Option in-memory keçini və ya fast websocket-i oxu
        if '_otc' in symbol.lower() or (self.po_trader and self.po_trader.is_connected):
            if self.po_trader and self.po_trader.client:
                asset = settings.PO_ASSET_MAPPING.get(symbol, symbol)
                seconds = settings.TIMEFRAME_SECONDS.get(timeframe, 60)

                # A. In-Memory Candles (0.001 saniyə)
                if hasattr(self.po_trader.client, 'candles') and asset in self.po_trader.client.candles:
                    df = self.po_trader.client.candles[asset]
                    if df is not None and not df.empty:
                        df_copy = df.copy()
                        df_copy.columns = [c.capitalize() for c in df_copy.columns]
                        self._cache[cache_key] = (now, df_copy)
                        return df_copy

                # B. Fast Async Fetch (Max 0.5s Timeout)
                try:
                    if hasattr(self.po_trader.client, 'get_candles_dataframe'):
                        df = await asyncio.wait_for(
                            self.po_trader.client.get_candles_dataframe(asset, seconds, count=60),
                            timeout=0.8
                        )
                        if df is not None and not df.empty:
                            df.columns = [c.capitalize() for c in df.columns]
                            self._cache[cache_key] = (now, df)
                            return df
                except Exception:
                    pass

            # OTC üçün yfinance-ə KEÇMƏ! Dərhal keçdəki məlumatı və ya None qaytar (0 gecikmə)
            return None

        # 2. Yalnız normal Forex cütlükləri üçün yfinance fallback (max 1 cəhd, fast timeout)
        return self.fetch_data(symbol, timeframe)

    def fetch_data(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Sync şam datalarını yükləyir."""
        if '_otc' in symbol.lower():
            return None  # OTC cütləri üçün yfinance-ə müraciət etmə!

        cache_key = f"{symbol}_{timeframe}"
        now = time.time()

        if cache_key in self._cache:
            cache_time, data = self._cache[cache_key]
            if now - cache_time < settings.DATA_CACHE_SECONDS:
                return data

        interval = settings.TIMEFRAMES.get(timeframe)
        period = settings.TIMEFRAME_PERIODS.get(timeframe)

        if interval and period:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval)
                if not df.empty:
                    self._cache[cache_key] = (now, df)
                    return df
            except Exception:
                pass

        return None

    def fetch_all_pairs(self, timeframe: str) -> Dict[str, pd.DataFrame]:
        """Bütün cütlüklər üçün datanı alır."""
        results = {}
        for symbol in settings.CURRENCY_PAIRS:
            df = self.fetch_data(symbol, timeframe)
            if df is not None and not df.empty:
                results[symbol] = df
        return results
