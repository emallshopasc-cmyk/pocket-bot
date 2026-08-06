"""Test skripti - core modulların yoxlanması."""
import sys
sys.path.insert(0, '.')

print("=" * 50)
print("  POCKET OPTION - MODUL TEST")
print("=" * 50)

# 1. Import test
try:
    from core.data_fetcher import DataFetcher
    from core.indicators import TechnicalIndicators
    from core.patterns import CandlestickPatterns
    from core.signal_engine import SignalEngine
    from core.chart_generator import ChartGenerator
    print("[OK] Butun core modullar import edildi")
except Exception as e:
    print(f"[XETA] Import: {e}")
    sys.exit(1)

# 2. Komponent yaratma testi
try:
    df = DataFetcher()
    ti = TechnicalIndicators()
    cp = CandlestickPatterns()
    se = SignalEngine(df, ti, cp)
    cg = ChartGenerator()
    print("[OK] Butun komponentler yaradildi")
except Exception as e:
    print(f"[XETA] Komponent: {e}")
    sys.exit(1)

# 3. Data fetch testi
print("\n[INFO] EUR/USD M5 datasi yuklenilir...")
try:
    data = df.fetch_data('EURUSD=X', 'M5')
    if data is not None and not data.empty:
        print(f"[OK] Data yuklendi: {len(data)} setir")
        print(f"     Son qiymet: {data.iloc[-1]['Close']:.5f}")
    else:
        print("[XEBERDARLIQ] Data bosh geldi (bazar bagli ola biler)")
except Exception as e:
    print(f"[XETA] Data fetch: {e}")

# 4. Signal scan testi
print("\n[INFO] M5 siqnallar skan edilir...")
try:
    signals = se.scan_all('M5')
    print(f"[OK] {len(signals)} siqnal tapildi")
    for s in signals:
        print(f"     -> {s['display_name']}: {s['direction']} ({s['confidence']}%)")
except Exception as e:
    print(f"[XETA] Skan: {e}")

# 5. Web app import testi
try:
    from web.app import create_app
    app = create_app(se)
    print("\n[OK] Web Dashboard import edildi")
except Exception as e:
    print(f"\n[XETA] Web: {e}")

# 6. Bot import testi
try:
    from bot.telegram_bot import TelegramBot
    from bot.formatters import SignalFormatter
    print("[OK] Telegram Bot import edildi")
except Exception as e:
    print(f"[XETA] Bot: {e}")

print("\n" + "=" * 50)
print("  TEST TAMAMLANDI")
print("=" * 50)
