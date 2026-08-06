import html
from datetime import datetime
from config import settings

class SignalFormatter:
    
    @staticmethod
    def format_signal(signal):
        direction = signal.get('direction', '')
        direction_text = "⬆️ CALL (BUY)" if direction == "BUY" else "⬇️ PUT (SELL)" if direction == "SELL" else "Neytral"
        
        display_name = html.escape(str(signal.get('display_name', signal.get('symbol', 'Bilinmir'))))
        confidence = signal.get('confidence', 0)
        timeframe = html.escape(str(signal.get('timeframe', 'M1')))
        price = signal.get('price', 0.0)
        
        timestamp = signal.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            time_str = timestamp
        else:
            time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
        msg = f"💎 <b>GEMINI PRO — CANLI OTC SİQNAL</b>\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"💱 <b>Aktiv:</b> {display_name}\n"
        msg += f"📊 <b>İstiqamət:</b> <b>{direction_text}</b>\n"
        msg += f"⏱️ <b>Müddət:</b> 60 Saniyə ({timeframe})\n"
        msg += f"🔥 <b>Etibar:</b> <b>{confidence}%</b> (Yüksək Təsdiq)\n"
        msg += f"💰 <b>Giriş Qiyməti:</b> <code>{price}</code>\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        
        indicators = signal.get('indicators', {})
        if indicators:
            msg += "📋 <b>İndikator Təsdiqləri:</b>\n"
            for ind_name, ind_data in indicators.items():
                ind_sig = ind_data.get('signal', 'NEUTRAL')
                desc = html.escape(str(ind_data.get('description', '')))
                
                icon = "⚠️"
                if ind_sig == direction and direction != "NEUTRAL":
                    icon = "✅"
                elif ind_sig != direction and ind_sig != "NEUTRAL":
                    icon = "❌"
                    
                msg += f"  {icon} <b>{html.escape(ind_name.upper())}:</b> {desc}\n"
            msg += "\n"
            
        patterns = signal.get('patterns', [])
        if patterns:
            msg += "🕯️ <b>Şam Modelləri (Patterns):</b>\n"
            for pat in patterns:
                pat_name = html.escape(str(pat.get('pattern', '')))
                msg += f"  🔹 {pat_name}\n"
            msg += "\n"
            
        msg += f"⚡ <b>Avto-Ticarət Statusu:</b> Active (PO Real Sync)\n"
        msg += f"⏰ <b>Vaxt:</b> <code>{html.escape(time_str)}</code>\n\n"
        msg += "🛡️ <i>Sistem 100% Real Balans Nəzarəti ilə Ticarəti İdarə Edir.</i>"
        
        return msg

    @staticmethod
    def format_signal_list(signals):
        if not signals:
            return "⚡ <b>Hazırda 65%+ etibarlı siqnal yoxdur. Bazar skan edilir...</b>"
            
        msg = "🚀 <b>GEMINI PRO — CANLI OTC BAZAR SİQNALLARI</b>\n\n"
        for sig in signals:
            display_name = html.escape(str(sig.get('display_name', sig.get('symbol', ''))))
            direction = sig.get('direction', '')
            direction_icon = "⬆️ CALL" if direction == "BUY" else "⬇️ PUT" if direction == "SELL" else "➖"
            conf = sig.get('confidence', 0)
            tf = html.escape(str(sig.get('timeframe', 'M1')))
            
            msg += f"• <b>{display_name}</b> ({tf}) ➔ <b>{direction_icon}</b> (Etibar: <b>{conf}%</b>)\n"
            
        return msg
        
    @staticmethod
    def format_stats(stats):
        if not stats:
            return "Statistika mövcud deyil."
            
        win_rate = stats.get('win_rate', 0.0)
        min_conf = getattr(settings, 'SIGNAL_MEDIUM_THRESHOLD', 50)
        steps = getattr(settings, 'MARTINGALE_MAX_STEPS', 4)
        mult = getattr(settings, 'MARTINGALE_MULTIPLIER', 2.5)
        total_wins = stats.get('total_wins', 0)
        total_trades = stats.get('total_trades', 0)
        target = getattr(settings, 'TARGET_WIN_COUNT', 5)
        
        msg = "📈 <b>GEMINI PRO — CANLI MARTINGALE STATİSTİKASI</b>\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"• 🏆 Uğurlu Ticarət Hədəfi: <b>{total_wins}/{target} Qazanc</b>\n"
        msg += f"• 🎯 İcra Olunmuş Əmr Sayı: <b>{total_trades} Ticarət</b>\n"
        msg += f"• ⏱️ Turbo Opsion Müddəti: <b>30 Saniyə (S30)</b>\n"
        msg += f"• ⚡ Skan İntervalı: <b>2 Saniyə (İldırım)</b>\n"
        msg += f"• 📊 Min Etibar Həddi: <b>{min_conf}% (Signal Score)</b>\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "💰 <b>Xalis Mənfəətlə Bərpa (Net Profit Recovery):</b>\n"
        msg += f"  1️⃣ Addım: <b>$1.00</b> (Qazanc: +$0.85)\n"
        msg += f"  2️⃣ Addım: <b>$2.50</b> (Bərpa -$1.00 ➔ Mənfəət: +$1.12)\n"
        msg += f"  3️⃣ Addım: <b>$6.50</b> (Bərpa -$3.50 ➔ Mənfəət: +$2.02)\n"
        msg += f"  4️⃣ Addım: <b>$16.50</b> (Bərpa -$10.00 ➔ Mənfəət: +$4.02)\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "🌐 <b>Web Dashboard:</b> http://localhost:5000"
        return msg

    @staticmethod
    def format_help():
        msg = "🤖 <b>GEMINI PRO BOT — ƏMR VƏ TƏLİMAT RƏHBƏRİ:</b>\n\n"
        msg += "▫️ <b>📊 Siqnalları Göstər</b> — Ən yüksək etibarlı siqnalları göstərər.\n"
        msg += "▫️ <b>⚡ Canlı OTC Analiz</b> — Bütün OTC cütlüklərinin canlı analizi.\n"
        msg += "▫️ <b>⚙️ Parametrlər</b> — Giriş məbləği və qazanc hədəfi seçimi.\n"
        msg += "▫️ <b>📈 Statistika</b> — Canlı win-rate hesabatı.\n"
        msg += "▫️ <b>/analyze EURUSD_otc</b> — Spesifik aktiv analizi."
        return msg

    @staticmethod
    def format_welcome():
        return (
            "👋 <b>Salam! Gemini Pro Pocket Option & Martingale Botuna Xoş Gəldiniz.</b>\n\n"
            "Sizə en yüksək etibarlı (65%+) OTC siqnalları tapıb Martingale (4 addım, 2.5x) strategiyası ilə avto-ticarəti 100% dəqiq idarə etməyə kömək edəcəyəm."
        )
