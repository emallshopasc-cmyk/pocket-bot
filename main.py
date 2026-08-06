"""
Pocket Option Siqnal Sistemi və Martingale Avtotrader - Əsas Başlatma Faylı
==========================================================================
- Telegram Bot
- Web Dashboard
- Martingale İcra Mühərriki (4 addım, 2.5x çoxaldıcı)
- Pocket Option İnteqrasiyası (Demo/Real)
"""

import os
import sys
import io
import logging
import asyncio
import threading
import signal as sig
from datetime import datetime
import matplotlib
matplotlib.use('Agg')

# yfinance-in websockets==11.0.3 ilə uyğunluğu üçün shim
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

# Windows-da UTF-8 encoding problemininin həlli
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Layihə kök qovluğunu sys.path-ə əlavə et
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from config import settings
from core.data_fetcher import DataFetcher
from core.indicators import TechnicalIndicators
from core.patterns import CandlestickPatterns
from core.signal_engine import SignalEngine
from core.chart_generator import ChartGenerator
from core.po_trader import PocketOptionTrader

# ============================================
# Logging konfiqurasiyası
# ============================================
def setup_logging():
    """Logging sistemini qur."""
    log_dir = os.path.join(BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'pocket_{datetime.now().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        format='%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.getLogger('yfinance').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('engineio').setLevel(logging.WARNING)
    logging.getLogger('socketio').setLevel(logging.WARNING)

logger = logging.getLogger('pocket.main')

import random

shutdown_event = threading.Event()
active_bot_instance = None
last_traded_history = {}

def signal_handler(signum, frame):
    """Proqramı düzgün dayandırmaq üçün siqnal handler."""
    logger.info("⏹️  Dayandırma siqnalı alındı. Sistem söndürülür...")
    shutdown_event.set()

# ============================================
# Skan və Martingale Ticarət funksiyası
# ============================================
def run_scanner(signal_engine: SignalEngine, chart_generator: ChartGenerator, 
                po_trader: PocketOptionTrader, web_app=None):
    """
    Vaxtaşırı bazarı skan edən və siqnal olduqda Martingale ticarəti başladan funksiya.
    """
    logger.info("🔍 Bazar skaneri və Martingale icraçısı işə düşdü")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    po_trader.loop = loop
    
    # Pocket Option-a bağlan
    loop.run_until_complete(po_trader.connect())
    
    async def async_notify(text: str):
        """Telegram və Web-ə bildiriş göndər."""
        if active_bot_instance and hasattr(active_bot_instance, 'send_signal_to_all'):
            try:
                # MarkdownV2 safe text or raw
                await active_bot_instance.send_signal_to_all(text)
            except Exception as e:
                logger.error(f"Bot notify error: {e}")
        if web_app and hasattr(web_app, 'emit_new_signal'):
            try:
                web_app.emit_new_signal({'message': text, 'timestamp': datetime.now().isoformat()})
            except Exception as e:
                logger.error(f"Web notify error: {e}")

    while not shutdown_event.is_set():
        try:
            logger.info("📊 Bazar skan edilir...")
            
            for tf_key in ['M1', 'M5', 'M15']:
                signals = signal_engine.scan_all(tf_key)
                
                if signals:
                    # Ədalətli aktiv rotasiyası (Anti-monopolization & Asset rotation):
                    # Bənzər etibarlılıqda ən son ticarət olunmuş aktivi növbəyə salır, digərlərinə şans verir!
                    now_ts = datetime.now().timestamp()
                    for s in signals:
                        sym = s['symbol']
                        last_t = last_traded_history.get(sym, 0)
                        penalty = 3.5 if (now_ts - last_t) < 120 else 0.0
                        s['_score'] = s.get('confidence', 0) - penalty + random.uniform(0.01, 0.09)
                    
                    signals.sort(key=lambda x: x.get('_score', 0), reverse=True)
                    logger.info(f"✅ {tf_key} üçün {len(signals)} siqnal tapıldı (Seçilən Aktiv: {signals[0]['display_name']} - {signals[0]['confidence']}%)")
                    
                    for signal_data in signals[:1]:
                        last_traded_history[signal_data['symbol']] = now_ts
                        # Qrafik generasiya et
                        try:
                            df = signal_engine.data_fetcher.fetch_data(
                                signal_data['symbol'], tf_key
                            )
                            if df is not None and not df.empty:
                                chart_path = chart_generator.generate_chart(
                                    df, signal_data['symbol'], signal_data
                                )
                                signal_data['chart_path'] = chart_path
                        except Exception as e:
                            logger.error(f"Qrafik xətası: {e}")
                        
                        if web_app and hasattr(web_app, 'emit_new_signal'):
                            try:
                                web_app.emit_new_signal(signal_data)
                            except Exception as e:
                                logger.error(f"WebSocket göndərmə xətası: {e}")
                                
                        if settings.MARTINGALE_ENABLED and getattr(po_trader, 'is_auto_trading', False):
                            logger.info(f"⚡ Martingale Ticarəti İşə Düşür: {signal_data['display_name']} {signal_data['direction']} ({signal_data['confidence']}%)")
                            loop.run_until_complete(
                                po_trader.execute_trade_sequence(signal_data, callback_notify=async_notify)
                            )
                else:
                    logger.info(f"ℹ️  {tf_key} üçün siqnal tapılmadı")
            
            # Köhnə qrafikləri təmizlə
            try:
                chart_generator.cleanup_old_charts(max_age_hours=24)
            except Exception as e:
                logger.error(f"Qrafik təmizləmə xətası: {e}")
                
        except Exception as e:
            logger.error(f"❌ Skan xətası: {e}", exc_info=True)
        
        shutdown_event.wait(timeout=settings.SCAN_INTERVAL_SECONDS)
    
    logger.info("🔍 Bazar skaneri dayandırıldı")


# ============================================
# Web Dashboard işə salma
# ============================================
def run_web_dashboard(signal_engine: SignalEngine, po_trader: PocketOptionTrader):
    """Flask web dashboard-u işə sal."""
    try:
        from web.app import create_app
        
        app = create_app(signal_engine, po_trader)
        logger.info(f"🌐 Web Dashboard işə düşür: http://localhost:{settings.WEB_PORT}")
        
        if hasattr(app, 'socketio'):
            app.socketio.run(
                app,
                host=settings.WEB_HOST,
                port=settings.WEB_PORT,
                debug=False,
                use_reloader=False,
                log_output=False
            )
        else:
            app.run(
                host=settings.WEB_HOST,
                port=settings.WEB_PORT,
                debug=False,
                use_reloader=False
            )
        return app
    except Exception as e:
        logger.error(f"❌ Web Dashboard xətası: {e}", exc_info=True)
        return None


# ============================================
# Telegram Bot işə salma
# ============================================
def run_telegram_bot(signal_engine: SignalEngine, po_trader: PocketOptionTrader):
    """Telegram botu işə sal."""
    global active_bot_instance
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("⚠️  TELEGRAM_BOT_TOKEN təyin edilməyib. Bot işə düşməyəcək.")
        logger.warning("   @BotFather-dən token alın və config/settings.py-ə yazın.")
        return None
    
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        from bot.telegram_bot import TelegramBot
        
        bot = TelegramBot(signal_engine, settings.TELEGRAM_BOT_TOKEN)
        bot.po_trader = po_trader
        bot.setup()
        active_bot_instance = bot
        logger.info("🤖 Telegram Bot işə düşür...")
        bot.start()
        return bot
    except Exception as e:
        logger.error(f"❌ Telegram Bot xətası: {e}", exc_info=True)
        return None


def main():
    setup_logging()
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                        ║
    ║   🔮 POCKET OPTION SİQNAL VƏ MARTİNGALE BOTA         ║
    ║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━         ║
    ║   📊 Min. Etibar: 75%  |  🔄 Martingale: 4 Addım (2.5x)  ║
    ║   📈 Baza Məbləğ: $1   |  💰 $1 -> $2.5 -> $6.25 -> $15.6 ║
    ║                                                        ║
    ║   🌐 Dashboard: http://localhost:5000                   ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    logger.info("🚀 Sistem başladılır...")
    
    os.makedirs(settings.CHART_DIR, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)
    
    logger.info("⚙️  Core komponentlər yaradılır...")
    po_trader = PocketOptionTrader(None)
    data_fetcher = DataFetcher(po_trader)
    indicators = TechnicalIndicators()
    patterns = CandlestickPatterns()
    signal_engine = SignalEngine(data_fetcher, indicators, patterns)
    po_trader.signal_engine = signal_engine
    chart_generator = ChartGenerator()
    
    logger.info("✅ Core və Martingale komponentlər hazırdır")
    
    sig.signal(sig.SIGINT, signal_handler)
    sig.signal(sig.SIGTERM, signal_handler)
    
    scanner_thread = threading.Thread(
        target=run_scanner,
        args=(signal_engine, chart_generator, po_trader),
        daemon=True,
        name="BazarSkaneri"
    )
    scanner_thread.start()
    logger.info("🔍 Martingale Skaneri başladı")
    
    web_thread = threading.Thread(
        target=run_web_dashboard,
        args=(signal_engine, po_trader),
        daemon=True,
        name="WebDashboard"
    )
    web_thread.start()
    logger.info(f"🌐 Web Dashboard thread başladı: http://0.0.0.0:{settings.WEB_PORT}")

    if settings.TELEGRAM_BOT_TOKEN:
        logger.info("🤖 Telegram Bot əsas thread-də başladılır...")
        try:
            run_telegram_bot(signal_engine, po_trader)
        except (KeyboardInterrupt, SystemExit):
            logger.info("⏹️  Klaviatura ilə dayandırıldı")
        finally:
            shutdown_event.set()
            logger.info("👋 Sistem söndürüldü.")
    else:
        logger.warning("⚠️  Telegram Bot Token yoxdur. Web Dashboard əsas thread-də qalır.")
        try:
            shutdown_event.wait()
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            shutdown_event.set()


if __name__ == '__main__':
    main()
