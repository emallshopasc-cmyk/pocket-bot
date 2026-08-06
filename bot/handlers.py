import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, constants
from telegram.ext import ContextTypes
from .formatters import SignalFormatter
from config import settings

logger = logging.getLogger(__name__)

def get_main_keyboard():
    """Həmişə görünen böyük alt düymələr menyusu."""
    keyboard = [
        [KeyboardButton("📊 Siqnalları Göstər"), KeyboardButton("⚡ Canlı OTC Analiz")],
        [KeyboardButton("📈 Statistika"), KeyboardButton("⚙️ Parametrlər (Wizard)")],
        [KeyboardButton("🛑 Avto-Ticarəti Dayandır"), KeyboardButton("▶️ Avto-Ticarəti Başlat")],
        [KeyboardButton("ℹ️ Kömək & Rəhbər")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def safe_chat_action(update: Update):
    """Network xətalarında donmamaq üçün təhlükəsiz chat action."""
    try:
        if update.message:
            await update.message.reply_chat_action(constants.ChatAction.TYPING)
        elif update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_chat_action(constants.ChatAction.TYPING)
    except Exception:
        pass

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        if 'save_chat_id_func' in context.bot_data:
            context.bot_data['save_chat_id_func'](chat_id)

        keyboard = [
            [InlineKeyboardButton("💵 $1", callback_data='set_amt_1'), InlineKeyboardButton("💵 $2", callback_data='set_amt_2')],
            [InlineKeyboardButton("💵 $5", callback_data='set_amt_5'), InlineKeyboardButton("💵 $10", callback_data='set_amt_10')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        welcome_text = (
            f"👋 <b>Salam! Gemini Pro Pocket Option & Martingale Botuna Xoş Gəldiniz.</b>\n\n"
            f"⚙️ <b>Quraşdırma Wizard-ı (Addım 1/2):</b>\n"
            f"💰 Hər ticarətə daxil olmaq üçün <b>Baza Məbləği</b> seçin:"
        )
        try:
            await update.message.reply_text(welcome_text, parse_mode=constants.ParseMode.HTML, reply_markup=reply_markup)
            await update.message.reply_text("💡 Həmçinin aşağıdakı menyudan istifadə edə bilərsiniz:", reply_markup=get_main_keyboard())
        except Exception as e:
            logger.error(f"Error sending start msg: {e}")
    except Exception as e:
        logger.error(f"Error in start_handler: {e}")

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(SignalFormatter.format_help(), parse_mode=constants.ParseMode.HTML, reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Error in help_handler: {e}")

async def signals_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_chat_action(update)
    
    engine = context.bot_data.get('signal_engine')
    target = update.message or (update.callback_query and update.callback_query.message)
    
    if not target:
        return

    if not engine:
        msg = "Sistem hazırlaşır, zəhmət olmasa bir az gözləyin..."
        try:
            await target.reply_text(msg, reply_markup=get_main_keyboard())
        except Exception:
            pass
        return
        
    try:
        if hasattr(engine, 'scan_all_async'):
            signals = await engine.scan_all_async('M1')
        else:
            signals = engine.scan_all('M1')
            
        if signals:
            for sig in signals[:3]:
                msg = SignalFormatter.format_signal(sig)
                try:
                    await target.reply_text(msg, parse_mode=constants.ParseMode.HTML, reply_markup=get_main_keyboard())
                except Exception as e:
                    logger.error(f"Error sending signal msg: {e}")
        else:
            # Parallel olaraq bütün OTC cütlüklərinin analizini topla (< 0.1s!)
            otc_pairs = ['EURUSD_otc', 'GBPUSD_otc', 'AUDCAD_otc', 'USDJPY_otc', 'USDCAD_otc', 'EURGBP_otc', 'EURJPY_otc']
            
            async def get_sym_sig(sym):
                try:
                    return sym, await engine.generate_signal_async(sym, 'M1') if hasattr(engine, 'generate_signal_async') else engine.generate_signal(sym, 'M1')
                except Exception:
                    return sym, None
                    
            tasks = [get_sym_sig(sym) for sym in otc_pairs]
            results = await asyncio.gather(*tasks)
            
            otc_report = "⚡ <b>GEMINI PRO — CANLI OTC BAZAR HESABATI</b>\n"
            otc_report += "━━━━━━━━━━━━━━━━━━━━━━\n"
            
            for sym, sig in results:
                display = settings.PAIR_DISPLAY_NAMES.get(sym, sym)
                if sig and sig.get('direction') != 'NEUTRAL':
                    dir_icon = "⬆️ CALL (BUY)" if sig['direction'] == 'BUY' else "⬇️ PUT (SELL)"
                    otc_report += f"🔹 <b>{display}</b>: {dir_icon} | Etibar: <b>{sig['confidence']}%</b>\n"
                else:
                    otc_report += f"🔹 <b>{display}</b>: 🔄 Neytral Trend / Analiz Olunur...\n"
                    
            otc_report += "━━━━━━━━━━━━━━━━━━━━━━\n"
            otc_report += "🤖 <i>Sistem 65%+ ideal siqnal kəsişməsi olan kimi avtomatik ticarətə daxil olacaq.</i>"
            
            try:
                await target.reply_text(otc_report, parse_mode=constants.ParseMode.HTML, reply_markup=get_main_keyboard())
            except Exception as e:
                logger.error(f"Error sending OTC report: {e}")

    except Exception as e:
        logger.error(f"Error in signals_handler: {e}", exc_info=True)
        try:
            await target.reply_text("⚡ OTC Bazar Skan Edilir...", reply_markup=get_main_keyboard())
        except Exception:
            pass

async def analyze_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Zəhmət olmasa aktivin adını daxil edin. Nümunə: /analyze EURUSD_otc", parse_mode=constants.ParseMode.HTML, reply_markup=get_main_keyboard())
        return
        
    symbol = context.args[0].upper()
    await safe_chat_action(update)
    
    engine = context.bot_data.get('signal_engine')
    if not engine:
        await update.message.reply_text("Sistem xətası.", reply_markup=get_main_keyboard())
        return
        
    try:
        signal = engine.generate_signal(symbol, 'M1')
        if not signal:
            await update.message.reply_text(f"<b>{symbol}</b> üçün 65%+ etibarlı siqnal tapılmadı.", parse_mode=constants.ParseMode.HTML, reply_markup=get_main_keyboard())
            return
            
        msg = SignalFormatter.format_signal(signal)
        try:
            await update.message.reply_text(msg, parse_mode=constants.ParseMode.HTML, reply_markup=get_main_keyboard())
        except Exception as e:
            logger.error(f"Error sending analyze msg: {e}")
            
    except Exception as e:
        logger.error(f"Error in analyze_handler: {e}", exc_info=True)
        await update.message.reply_text("Analiz zamanı xəta baş verdi.", reply_markup=get_main_keyboard())

async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💵 $1", callback_data='set_amt_1'), InlineKeyboardButton("💵 $2", callback_data='set_amt_2')],
        [InlineKeyboardButton("💵 $5", callback_data='set_amt_5'), InlineKeyboardButton("💵 $10", callback_data='set_amt_10')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "💰 <b>Baza Giriş Məbləğini Seçin:</b>"
    
    try:
        if update.callback_query and update.callback_query.message:
            await update.callback_query.message.edit_text(msg, reply_markup=reply_markup, parse_mode=constants.ParseMode.HTML)
        elif update.message:
            await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode=constants.ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error in settings_handler: {e}")

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_chat_action(update)
    target = update.message or (update.callback_query and update.callback_query.message)
    if not target:
        return

    engine = context.bot_data.get('signal_engine')
    po_trader = context.bot_data.get('po_trader')
    
    if engine and hasattr(engine, 'get_stats'):
        stats = engine.get_stats()
        if po_trader:
            stats['total_wins'] = getattr(po_trader, 'total_wins', 0)
            stats['total_trades'] = len(getattr(po_trader, 'trade_history', []))
        msg = SignalFormatter.format_stats(stats)
    else:
        msg = "Statistika hazır deyil."
        
    try:
        await target.reply_text(msg, parse_mode=constants.ParseMode.HTML, reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Error in stats_handler: {e}")

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Düymələrə basıldıqda gələn mətnləri emal edir."""
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    po_trader = context.bot_data.get('po_trader')

    if text in ["📊 Siqnalları Göstər", "⚡ Canlı OTC Analiz"]:
        await signals_handler(update, context)
    elif text == "📈 Statistika":
        await stats_handler(update, context)
    elif text in ["⚙️ Parametrlər", "⚙️ Parametrlər (Wizard)"]:
        await settings_handler(update, context)
    elif text == "🛑 Avto-Ticarəti Dayandır":
        if po_trader:
            po_trader.is_auto_trading = False
        await update.message.reply_text("🛑 <b>Avto-ticarət UĞURLA DAYANDIRILDI!</b>\nBot artıq avtomatik əmr açmayacaq.", parse_mode=constants.ParseMode.HTML, reply_markup=get_main_keyboard())
    elif text == "▶️ Avto-Ticarəti Başlat":
        amt = getattr(settings, 'MARTINGALE_BASE_AMOUNT', 1.0)
        tgt = getattr(settings, 'TARGET_WIN_COUNT', 5)
        if po_trader:
            po_trader.is_auto_trading = True
            po_trader.total_wins = 0
            if hasattr(po_trader, 'martingale'):
                po_trader.martingale.base_amount = amt
                po_trader.martingale.current_step = 1
        await update.message.reply_text(f"▶️ <b>Avto-ticarət UĞURLA BAŞLADILDI!</b>\n💰 Baza Məbləğ: ${amt:.0f}\n🎯 Hədəf: {tgt} Qazanc", parse_mode=constants.ParseMode.HTML, reply_markup=get_main_keyboard())
    elif text in ["ℹ️ Kömək", "ℹ️ Kömək & Rəhbər"]:
        await help_handler(update, context)
    else:
        await update.message.reply_text("Zəhmət olmasa menyudakı düymələrdən birini seçin.", reply_markup=get_main_keyboard())

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    
    data = query.data
    
    # Addım 1: Baza məbləğ seçildi
    if data.startswith('set_amt_'):
        amt = float(data.split('_')[2])
        settings.MARTINGALE_BASE_AMOUNT = amt
        po_trader = context.bot_data.get('po_trader')
        if po_trader and hasattr(po_trader, 'martingale'):
            po_trader.martingale.base_amount = amt
            
        # Addım 2: Hədəf qazanc sayını soruş
        keyboard = [
            [InlineKeyboardButton("🏆 1 Dəfə Qazanc", callback_data='set_tgt_1')],
            [InlineKeyboardButton("🏆 3 Dəfə Qazanc", callback_data='set_tgt_3')],
            [InlineKeyboardButton("🏆 5 Dəfə Qazanc", callback_data='set_tgt_5')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = f"✅ Baza məbləğ <b>${amt:.0f}</b> seçildi.\n\n🎯 <b>Addım 2/2: Neçə Dəfə Qazanc Hədəflənsin?</b>"
        try:
            await query.message.edit_text(msg, reply_markup=reply_markup, parse_mode=constants.ParseMode.HTML)
        except Exception as e:
            logger.error(f"Error editing msg set_amt: {e}")

    # Addım 2: Qazanc hədəfi seçildi
    elif data.startswith('set_tgt_'):
        tgt = int(data.split('_')[2])
        settings.TARGET_WIN_COUNT = tgt
        po_trader = context.bot_data.get('po_trader')
        if po_trader:
            po_trader.total_wins = 0
            po_trader.is_auto_trading = True  # Avto-ticarəti rəsmən aktiv et!
            
        amt = getattr(settings, 'MARTINGALE_BASE_AMOUNT', 1.0)
        msg = (
            f"🎉 <b>PARAMETRLƏR MÜVƏFFƏQİYYƏTLƏ TƏSDİQLƏNDİ!</b>\n\n"
            f"💰 Baza Məbləğ: <b>${amt:.0f}</b>\n"
            f"🎯 Hədəf Qazanc Sayı: <b>{tgt} Dəfə</b>\n"
            f"🔄 Martingale Strategiyası: <b>4 Addım (2.5x - 6.5x - 16.5x)</b>\n"
            f"🛑 Hədəfə Çatdıqda: <b>Avtomatik Dayanacaq</b>\n\n"
            f"⚡ <b>Avto-Ticarət İndi Rəsmən Başladı!</b>"
        )
        try:
            await query.message.edit_text(msg, parse_mode=constants.ParseMode.HTML)
            await query.message.reply_text("🎛️ <b>İdarəetmə menyusu yeniləndi. Aşağıdakı düymələrlə idarə edə bilərsiniz:</b>", parse_mode=constants.ParseMode.HTML, reply_markup=get_main_keyboard())
        except Exception as e:
            logger.error(f"Error editing msg set_tgt: {e}")

    elif data == 'cmd_signals':
        await signals_handler(update, context)
    elif data == 'cmd_stats':
        await stats_handler(update, context)
    elif data == 'cmd_settings':
        await settings_handler(update, context)
    elif data == 'close':
        try:
            await query.message.delete()
        except Exception:
            pass

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Network / Bot exception: {context.error}")
