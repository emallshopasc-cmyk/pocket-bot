import pandas as pd
import numpy as np
import logging
from typing import Dict, Any
from config import settings

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Texniki indikatorların hesablanması.
    pandas_ta əvəzinə saf pandas/numpy ilə hesablanır.
    """

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = settings.RSI_PERIOD) -> pd.DataFrame:
        """RSI (Relative Strength Index) hesabla."""
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        # Exponential əvəzinə Wilder smoothing
        for i in range(period, len(avg_gain)):
            avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df

    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = settings.MACD_FAST,
                       slow: int = settings.MACD_SLOW,
                       signal: int = settings.MACD_SIGNAL) -> pd.DataFrame:
        """MACD (Moving Average Convergence Divergence) hesabla."""
        ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
        df['MACD'] = ema_fast - ema_slow
        df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        return df

    @staticmethod
    def calculate_bollinger(df: pd.DataFrame, period: int = settings.BB_PERIOD,
                            std: float = settings.BB_STD) -> pd.DataFrame:
        """Bollinger Bands hesabla."""
        df['BB_Middle'] = df['Close'].rolling(window=period).mean()
        rolling_std = df['Close'].rolling(window=period).std()
        df['BB_Upper'] = df['BB_Middle'] + (rolling_std * std)
        df['BB_Lower'] = df['BB_Middle'] - (rolling_std * std)
        return df

    @staticmethod
    def calculate_sma(df: pd.DataFrame, short: int = settings.SMA_SHORT,
                      long: int = settings.SMA_LONG) -> pd.DataFrame:
        """SMA (Simple Moving Average) hesabla."""
        df['SMA_Short'] = df['Close'].rolling(window=short).mean()
        df['SMA_Long'] = df['Close'].rolling(window=long).mean()
        return df

    @staticmethod
    def calculate_ema(df: pd.DataFrame, short: int = settings.EMA_SHORT,
                      long: int = settings.EMA_LONG) -> pd.DataFrame:
        """EMA (Exponential Moving Average) hesabla."""
        df['EMA_Short'] = df['Close'].ewm(span=short, adjust=False).mean()
        df['EMA_Long'] = df['Close'].ewm(span=long, adjust=False).mean()
        return df

    @staticmethod
    def calculate_stochastic(df: pd.DataFrame, k: int = settings.STOCH_K,
                              d: int = settings.STOCH_D) -> pd.DataFrame:
        """Stochastic Oscillator hesabla."""
        low_min = df['Low'].rolling(window=k).min()
        high_max = df['High'].rolling(window=k).max()
        df['Stoch_K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
        df['Stoch_D'] = df['Stoch_K'].rolling(window=d).mean()
        return df

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = settings.ATR_PERIOD) -> pd.DataFrame:
        """ATR (Average True Range) hesabla."""
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift()).abs()
        low_close = (df['Low'] - df['Close'].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = true_range.rolling(window=period).mean()
        return df

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Bütün indikatorları hesabla."""
        df = df.copy()
        try:
            df = self.calculate_rsi(df)
            df = self.calculate_macd(df)
            df = self.calculate_bollinger(df)
            df = self.calculate_sma(df)
            df = self.calculate_ema(df)
            df = self.calculate_stochastic(df)
            df = self.calculate_atr(df)
        except Exception as e:
            logger.error(f"İndikator hesablama xətası: {e}")
        return df

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        İndikatorları analiz edir və siqnallar qaytarır.
        Hər indikator üçün: value, signal (BUY/SELL/NEUTRAL), description (AZ)
        """
        if len(df) < 2:
            return {}

        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        results = {}

        # RSI
        if 'RSI' in df.columns and not pd.isna(last_row.get('RSI')):
            rsi = last_row['RSI']
            if rsi < settings.RSI_OVERSOLD:
                results['rsi'] = {'value': round(rsi, 2), 'signal': 'BUY',
                                  'description': 'Həddən artıq satılıb (Oversold)'}
            elif rsi > settings.RSI_OVERBOUGHT:
                results['rsi'] = {'value': round(rsi, 2), 'signal': 'SELL',
                                  'description': 'Həddən artıq alınıb (Overbought)'}
            else:
                results['rsi'] = {'value': round(rsi, 2), 'signal': 'NEUTRAL',
                                  'description': 'Neytral zona'}

        # MACD
        if all(col in df.columns for col in ['MACD', 'MACD_Signal']):
            macd_val = last_row['MACD']
            sig_val = last_row['MACD_Signal']
            prev_macd = prev_row['MACD']
            prev_sig = prev_row['MACD_Signal']

            if not (pd.isna(macd_val) or pd.isna(sig_val)):
                if macd_val > sig_val and prev_macd <= prev_sig:
                    results['macd'] = {'value': round(macd_val, 4), 'signal': 'BUY',
                                       'description': 'MACD siqnal xəttini yuxarı kəsdi'}
                elif macd_val < sig_val and prev_macd >= prev_sig:
                    results['macd'] = {'value': round(macd_val, 4), 'signal': 'SELL',
                                       'description': 'MACD siqnal xəttini aşağı kəsdi'}
                elif macd_val > sig_val:
                    results['macd'] = {'value': round(macd_val, 4), 'signal': 'BUY',
                                       'description': 'MACD yüksəliş trendindədir'}
                else:
                    results['macd'] = {'value': round(macd_val, 4), 'signal': 'SELL',
                                       'description': 'MACD düşüş trendindədir'}

        # Bollinger Bands
        if all(col in df.columns for col in ['BB_Lower', 'BB_Upper']):
            close = last_row['Close']
            lower = last_row['BB_Lower']
            upper = last_row['BB_Upper']

            if not (pd.isna(lower) or pd.isna(upper)):
                if close <= lower:
                    results['bollinger'] = {'value': round(close, 4), 'signal': 'BUY',
                                            'description': 'Qiymət alt Bollinger bandına toxundu'}
                elif close >= upper:
                    results['bollinger'] = {'value': round(close, 4), 'signal': 'SELL',
                                            'description': 'Qiymət üst Bollinger bandına toxundu'}
                else:
                    results['bollinger'] = {'value': round(close, 4), 'signal': 'NEUTRAL',
                                            'description': 'Qiymət Bollinger bandının daxilindədir'}

        # SMA Cross
        if all(col in df.columns for col in ['SMA_Short', 'SMA_Long']):
            sma_s = last_row['SMA_Short']
            sma_l = last_row['SMA_Long']

            if not (pd.isna(sma_s) or pd.isna(sma_l)):
                if sma_s > sma_l:
                    results['sma'] = {'value': f"{round(sma_s, 4)}/{round(sma_l, 4)}", 'signal': 'BUY',
                                      'description': 'Qızıl Kəsişmə (Golden Cross)'}
                else:
                    results['sma'] = {'value': f"{round(sma_s, 4)}/{round(sma_l, 4)}", 'signal': 'SELL',
                                      'description': 'Ölüm Kəsişməsi (Death Cross)'}

        # EMA Cross
        if all(col in df.columns for col in ['EMA_Short', 'EMA_Long']):
            ema_s = last_row['EMA_Short']
            ema_l = last_row['EMA_Long']
            prev_ema_s = prev_row['EMA_Short']
            prev_ema_l = prev_row['EMA_Long']

            if not (pd.isna(ema_s) or pd.isna(ema_l)):
                if ema_s > ema_l and prev_ema_s <= prev_ema_l:
                    results['ema'] = {'value': f"{round(ema_s, 4)}/{round(ema_l, 4)}", 'signal': 'BUY',
                                      'description': 'Qısa EMA uzun EMA-nı yuxarı kəsdi'}
                elif ema_s < ema_l and prev_ema_s >= prev_ema_l:
                    results['ema'] = {'value': f"{round(ema_s, 4)}/{round(ema_l, 4)}", 'signal': 'SELL',
                                      'description': 'Qısa EMA uzun EMA-nı aşağı kəsdi'}
                elif ema_s > ema_l:
                    results['ema'] = {'value': f"{round(ema_s, 4)}/{round(ema_l, 4)}", 'signal': 'BUY',
                                      'description': 'EMA yüksəliş trendini göstərir'}
                else:
                    results['ema'] = {'value': f"{round(ema_s, 4)}/{round(ema_l, 4)}", 'signal': 'SELL',
                                      'description': 'EMA düşüş trendini göstərir'}

        # Stochastic
        if all(col in df.columns for col in ['Stoch_K', 'Stoch_D']):
            k = last_row['Stoch_K']
            d = last_row['Stoch_D']

            if not (pd.isna(k) or pd.isna(d)):
                if k < settings.STOCH_OVERSOLD and k > d:
                    results['stochastic'] = {'value': round(k, 2), 'signal': 'BUY',
                                              'description': 'Stokastik həddən artıq satılıb və yüksəlir'}
                elif k > settings.STOCH_OVERBOUGHT and k < d:
                    results['stochastic'] = {'value': round(k, 2), 'signal': 'SELL',
                                              'description': 'Stokastik həddən artıq alınıb və düşür'}
                else:
                    results['stochastic'] = {'value': round(k, 2), 'signal': 'NEUTRAL',
                                              'description': 'Stokastik neytral zonadadır'}

        return results
