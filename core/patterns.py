import pandas as pd
from typing import List, Dict, Any

class CandlestickPatterns:
    
    @staticmethod
    def detect_hammer(df: pd.DataFrame, idx: int = -1) -> bool:
        if len(df) < abs(idx): return False
        row = df.iloc[idx]
        body = abs(row['Close'] - row['Open'])
        lower_shadow = min(row['Open'], row['Close']) - row['Low']
        upper_shadow = row['High'] - max(row['Open'], row['Close'])
        return lower_shadow > body * 2 and upper_shadow < body * 0.5
        
    @staticmethod
    def detect_inverted_hammer(df: pd.DataFrame, idx: int = -1) -> bool:
        if len(df) < abs(idx): return False
        row = df.iloc[idx]
        body = abs(row['Close'] - row['Open'])
        lower_shadow = min(row['Open'], row['Close']) - row['Low']
        upper_shadow = row['High'] - max(row['Open'], row['Close'])
        return upper_shadow > body * 2 and lower_shadow < body * 0.5
        
    @staticmethod
    def detect_bullish_engulfing(df: pd.DataFrame, idx: int = -1) -> bool:
        if len(df) < abs(idx) + 1: return False
        current = df.iloc[idx]
        prev = df.iloc[idx - 1]
        
        prev_bearish = prev['Close'] < prev['Open']
        curr_bullish = current['Close'] > current['Open']
        engulfing = current['Open'] < prev['Close'] and current['Close'] > prev['Open']
        
        return prev_bearish and curr_bullish and engulfing
        
    @staticmethod
    def detect_bearish_engulfing(df: pd.DataFrame, idx: int = -1) -> bool:
        if len(df) < abs(idx) + 1: return False
        current = df.iloc[idx]
        prev = df.iloc[idx - 1]
        
        prev_bullish = prev['Close'] > prev['Open']
        curr_bearish = current['Close'] < current['Open']
        engulfing = current['Open'] > prev['Close'] and current['Close'] < prev['Open']
        
        return prev_bullish and curr_bearish and engulfing
        
    @staticmethod
    def detect_doji(df: pd.DataFrame, idx: int = -1) -> bool:
        if len(df) < abs(idx): return False
        row = df.iloc[idx]
        body = abs(row['Close'] - row['Open'])
        total_length = row['High'] - row['Low']
        if total_length == 0: return False
        return body / total_length < 0.1
        
    @staticmethod
    def detect_morning_star(df: pd.DataFrame, idx: int = -1) -> bool:
        if len(df) < abs(idx) + 2: return False
        first = df.iloc[idx - 2]
        second = df.iloc[idx - 1]
        third = df.iloc[idx]
        
        first_bearish = first['Close'] < first['Open']
        second_doji_or_small = abs(second['Close'] - second['Open']) / (second['High'] - second['Low'] + 1e-5) < 0.3
        third_bullish = third['Close'] > third['Open']
        gap_down = second['Open'] < first['Close']
        close_in_first = third['Close'] > (first['Open'] + first['Close']) / 2
        
        return first_bearish and second_doji_or_small and third_bullish and gap_down and close_in_first
        
    @staticmethod
    def detect_evening_star(df: pd.DataFrame, idx: int = -1) -> bool:
        if len(df) < abs(idx) + 2: return False
        first = df.iloc[idx - 2]
        second = df.iloc[idx - 1]
        third = df.iloc[idx]
        
        first_bullish = first['Close'] > first['Open']
        second_doji_or_small = abs(second['Close'] - second['Open']) / (second['High'] - second['Low'] + 1e-5) < 0.3
        third_bearish = third['Close'] < third['Open']
        gap_up = second['Open'] > first['Close']
        close_in_first = third['Close'] < (first['Open'] + first['Close']) / 2
        
        return first_bullish and second_doji_or_small and third_bearish and gap_up and close_in_first
        
    @staticmethod
    def detect_three_white_soldiers(df: pd.DataFrame, idx: int = -1) -> bool:
        if len(df) < abs(idx) + 2: return False
        c1 = df.iloc[idx - 2]
        c2 = df.iloc[idx - 1]
        c3 = df.iloc[idx]
        
        bull_c1 = c1['Close'] > c1['Open']
        bull_c2 = c2['Close'] > c2['Open']
        bull_c3 = c3['Close'] > c3['Open']
        
        higher_closes = c3['Close'] > c2['Close'] > c1['Close']
        opens_in_prev_body = (c1['Close'] > c2['Open'] > c1['Open']) and (c2['Close'] > c3['Open'] > c2['Open'])
        
        return bull_c1 and bull_c2 and bull_c3 and higher_closes and opens_in_prev_body
        
    @staticmethod
    def detect_three_black_crows(df: pd.DataFrame, idx: int = -1) -> bool:
        if len(df) < abs(idx) + 2: return False
        c1 = df.iloc[idx - 2]
        c2 = df.iloc[idx - 1]
        c3 = df.iloc[idx]
        
        bear_c1 = c1['Close'] < c1['Open']
        bear_c2 = c2['Close'] < c2['Open']
        bear_c3 = c3['Close'] < c3['Open']
        
        lower_closes = c3['Close'] < c2['Close'] < c1['Close']
        opens_in_prev_body = (c1['Close'] < c2['Open'] < c1['Open']) and (c2['Close'] < c3['Open'] < c2['Open'])
        
        return bear_c1 and bear_c2 and bear_c3 and lower_closes and opens_in_prev_body
        
    def analyze(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        patterns = []
        if len(df) < 3: return patterns
        
        if self.detect_hammer(df):
            patterns.append({'pattern': 'Çəkic (Hammer)', 'signal': 'BUY', 'strength': 0.6, 'description': 'Yüksəliş yönümlü Çəkic modeli aşkarlandı'})
        
        if self.detect_inverted_hammer(df):
            patterns.append({'pattern': 'Tərs Çəkic (Inverted Hammer)', 'signal': 'BUY', 'strength': 0.6, 'description': 'Yüksəliş yönümlü Tərs Çəkic modeli aşkarlandı'})
            
        if self.detect_bullish_engulfing(df):
            patterns.append({'pattern': 'Yüksəliş Udma (Bullish Engulfing)', 'signal': 'BUY', 'strength': 0.8, 'description': 'Yüksəliş Udma modeli aşkarlandı'})
            
        if self.detect_bearish_engulfing(df):
            patterns.append({'pattern': 'Düşüş Udma (Bearish Engulfing)', 'signal': 'SELL', 'strength': 0.8, 'description': 'Düşüş Udma modeli aşkarlandı'})
            
        if self.detect_doji(df):
            patterns.append({'pattern': 'Doci (Doji)', 'signal': 'NEUTRAL', 'strength': 0.4, 'description': 'Qərarsızlıq göstərən Doci şamı aşkarlandı'})
            
        if self.detect_morning_star(df):
            patterns.append({'pattern': 'Səhər Ulduzu (Morning Star)', 'signal': 'BUY', 'strength': 0.9, 'description': 'Güclü Yüksəliş göstərən Səhər Ulduzu aşkarlandı'})
            
        if self.detect_evening_star(df):
            patterns.append({'pattern': 'Axşam Ulduzu (Evening Star)', 'signal': 'SELL', 'strength': 0.9, 'description': 'Güclü Düşüş göstərən Axşam Ulduzu aşkarlandı'})
            
        if self.detect_three_white_soldiers(df):
            patterns.append({'pattern': 'Üç Ağ Əsgər (Three White Soldiers)', 'signal': 'BUY', 'strength': 0.85, 'description': 'Yüksəliş trendi göstərən Üç Ağ Əsgər aşkarlandı'})
            
        if self.detect_three_black_crows(df):
            patterns.append({'pattern': 'Üç Qara Qarğa (Three Black Crows)', 'signal': 'SELL', 'strength': 0.85, 'description': 'Düşüş trendi göstərən Üç Qara Qarğa aşkarlandı'})
            
        return patterns
