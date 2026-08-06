import os
import json
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from .handlers import (start_handler, help_handler, signals_handler, analyze_handler, 
                       settings_handler, stats_handler, text_message_handler, 
                       callback_handler, error_handler)
from .formatters import SignalFormatter
from telegram import constants

from config import settings

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, signal_engine, token):
        self.signal_engine = signal_engine
        self.token = token
        self.app = None
        self.data_dir = os.path.join(settings.BASE_DIR, "data")
        self.chat_ids_file = os.path.join(self.data_dir, "chat_ids.json")
        self.chat_ids = set()
        self._load_chat_ids()
        
    def _load_chat_ids(self):
        if os.path.exists(self.chat_ids_file):
            try:
                with open(self.chat_ids_file, 'r') as f:
                    data = json.load(f)
                    self.chat_ids = set(data.get('chat_ids', []))
            except Exception as e:
                logger.error(f"Error loading chat ids: {e}")
                
    def save_chat_id(self, chat_id):
        if chat_id not in self.chat_ids:
            self.chat_ids.add(chat_id)
            os.makedirs(self.data_dir, exist_ok=True)
            try:
                with open(self.chat_ids_file, 'w') as f:
                    json.dump({'chat_ids': list(self.chat_ids)}, f)
            except Exception as e:
                logger.error(f"Error saving chat ids: {e}")

    def setup(self):
        self.app = ApplicationBuilder().token(self.token).build()
        
        self.app.bot_data['signal_engine'] = self.signal_engine
        self.app.bot_data['po_trader'] = getattr(self, 'po_trader', None)
        self.app.bot_data['save_chat_id_func'] = self.save_chat_id
        
        self.app.add_handler(CommandHandler("start", start_handler))
        self.app.add_handler(CommandHandler("help", help_handler))
        self.app.add_handler(CommandHandler("signals", signals_handler))
        self.app.add_handler(CommandHandler("analyze", analyze_handler))
        self.app.add_handler(CommandHandler("settings", settings_handler))
        self.app.add_handler(CommandHandler("stats", stats_handler))
        
        # Persistent button text handler
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
        
        self.app.add_handler(CallbackQueryHandler(callback_handler))
        self.app.add_error_handler(error_handler)
        
    def start(self):
        logger.info("Bot starting...")
        self.app.run_polling()
        
    def stop(self):
        logger.info("Bot stopping...")
        if self.app:
            self.app.stop()
            
    async def send_signal(self, chat_id, signal):
        if not self.app or not self.app.bot:
            logger.error("Bot is not initialized.")
            return
            
        if isinstance(signal, str):
            msg = signal
            chart = None
        else:
            msg = SignalFormatter.format_signal(signal)
            chart = signal.get('chart_path')

        try:
            if chart and os.path.exists(chart):
                with open(chart, 'rb') as photo:
                    await self.app.bot.send_photo(chat_id=chat_id, photo=photo, caption=msg, parse_mode=constants.ParseMode.HTML)
            else:
                await self.app.bot.send_message(chat_id=chat_id, text=msg, parse_mode=constants.ParseMode.HTML)
        except Exception as e:
            logger.error(f"Failed to send signal to {chat_id}: {e}")
            
    async def send_signal_to_all(self, signal):
        for chat_id in self.chat_ids:
            await self.send_signal(chat_id, signal)
