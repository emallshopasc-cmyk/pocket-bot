import os
import time
import logging
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import mplfinance as mpf
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional
from config import settings

logger = logging.getLogger(__name__)

class ChartGenerator:
    def __init__(self):
        if not os.path.exists(settings.CHART_DIR):
            os.makedirs(settings.CHART_DIR, exist_ok=True)
            
    def generate_chart(self, df: pd.DataFrame, symbol: str, signal_info: Dict[str, Any]) -> Optional[str]:
        try:
            plt.style.use('dark_background')
            
            # Son 100 şamı göstərək
            plot_df = df.tail(100).copy()
            
            mc = mpf.make_marketcolors(
                up='lime', down='red', 
                edge='inherit', wick='inherit',
                volume='in', ohlc='i'
            )
            s = mpf.make_mpf_style(
                marketcolors=mc, 
                facecolor='#1a1a2e',
                edgecolor='white',
                figcolor='#1a1a2e',
                gridstyle='--',
                gridcolor='gray'
            )
            
            addplots = []
            
            # Bollinger Bands
            if all(col in plot_df.columns for col in ['BB_Upper', 'BB_Middle', 'BB_Lower']):
                addplots.append(mpf.make_addplot(plot_df['BB_Upper'], color='cyan', alpha=0.6))
                addplots.append(mpf.make_addplot(plot_df['BB_Middle'], color='gray', alpha=0.6, linestyle='--'))
                addplots.append(mpf.make_addplot(plot_df['BB_Lower'], color='cyan', alpha=0.6))
                
            # RSI
            if 'RSI' in plot_df.columns:
                addplots.append(mpf.make_addplot(plot_df['RSI'], panel=1, color='magenta', ylabel='RSI'))
                
            # MACD
            if all(col in plot_df.columns for col in ['MACD', 'MACD_Signal', 'MACD_Hist']):
                addplots.append(mpf.make_addplot(plot_df['MACD'], panel=2, color='blue', ylabel='MACD'))
                addplots.append(mpf.make_addplot(plot_df['MACD_Signal'], panel=2, color='orange'))
                colors = ['green' if val > 0 else 'red' for val in plot_df['MACD_Hist']]
                addplots.append(mpf.make_addplot(plot_df['MACD_Hist'], type='bar', panel=2, color=colors))
            
            filename = f"chart_{symbol.replace('=', '_')}_{signal_info.get('timeframe', 'TF')}_{int(time.time())}.png"
            filepath = os.path.join(settings.CHART_DIR, filename)
            
            title = f"{settings.PAIR_DISPLAY_NAMES.get(symbol, symbol)} - {signal_info.get('timeframe', '')} - Siqnal: {signal_info.get('direction', '')}"
            
            # Siqnal oxu
            direction = signal_info.get('direction')
            markers = []
            if direction == 'BUY':
                marker_data = [plot_df['Low'].iloc[i] * 0.999 if i == len(plot_df)-1 else float('nan') for i in range(len(plot_df))]
                addplots.append(mpf.make_addplot(marker_data, type='scatter', markersize=200, marker='^', color='lime'))
            elif direction == 'SELL':
                marker_data = [plot_df['High'].iloc[i] * 1.001 if i == len(plot_df)-1 else float('nan') for i in range(len(plot_df))]
                addplots.append(mpf.make_addplot(marker_data, type='scatter', markersize=200, marker='v', color='red'))
            
            # Panel sayını dinamik təyin et
            has_rsi = 'RSI' in plot_df.columns and not plot_df['RSI'].isna().all()
            has_macd = all(col in plot_df.columns for col in ['MACD', 'MACD_Signal', 'MACD_Hist']) and not plot_df['MACD'].isna().all()
            
            plot_kwargs = dict(
                type='candle',
                style=s,
                title=title,
                figsize=(12, 8),
                savefig=dict(fname=filepath, dpi=150, bbox_inches='tight')
            )
            
            if addplots:
                plot_kwargs['addplot'] = addplots
            
            if has_rsi and has_macd:
                plot_kwargs['panel_ratios'] = (3, 1, 1)
            elif has_rsi or has_macd:
                plot_kwargs['panel_ratios'] = (3, 1)
            
            mpf.plot(plot_df, **plot_kwargs)
            
            return filepath
            
        except Exception as e:
            logger.error(f"Qrafik yaradılarkən xəta: {str(e)}")
            return None
            
    def cleanup_old_charts(self, max_age_hours: int = 24):
        try:
            now = time.time()
            for filename in os.listdir(settings.CHART_DIR):
                filepath = os.path.join(settings.CHART_DIR, filename)
                if os.path.isfile(filepath):
                    if now - os.path.getmtime(filepath) > max_age_hours * 3600:
                        os.remove(filepath)
                        logger.debug(f"Köhnə qrafik silindi: {filename}")
        except Exception as e:
            logger.error(f"Köhnə qrafiklər silinərkən xəta: {str(e)}")
