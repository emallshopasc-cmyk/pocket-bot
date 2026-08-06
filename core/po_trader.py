"""
Pocket Option Ticarət İcrası və Martingale Strategiya İdarəetməsi Modulu
========================================================================
- Pocket Option WebSocket API ilə inteqrasiya
- Martingale strategiyası (4 addım, 2.5x çoxaldıcı)
- Real və ya Demo hesab dəstəyi
- Reallığa tam uyğun Balans Yoxlaması ilə 100% Dəqiq Qazanc/İtki Təyini
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from config import settings

logger = logging.getLogger(__name__)

try:
    from pocketoptionapi_async import AsyncPocketOptionClient, OrderDirection
    PO_API_AVAILABLE = True
except Exception as e:
    PO_API_AVAILABLE = False
    OrderDirection = None
    logger.error(f"❌ PocketOption API Yüklənmə Xətası: {e}", exc_info=True)


class MartingaleManager:
    """
    Martingale risk idarəetmə sinfi.
    Calculates amounts:
      Step 1: $1.0
      Step 2: $2.5
      Step 3: $6.25
      Step 4: $15.63
    """

    def __init__(self, base_amount: float = settings.MARTINGALE_BASE_AMOUNT,
                 multiplier: float = settings.MARTINGALE_MULTIPLIER,
                 max_steps: int = settings.MARTINGALE_MAX_STEPS):
        self.base_amount = base_amount
        self.multiplier = multiplier
        self.max_steps = max_steps
        self.current_step = 1

    def get_current_amount(self) -> float:
        """Hazırkı cəhd üçün tam mənfəətli Martingale məbləğini hesablayır."""
        current_base = getattr(settings, 'MARTINGALE_BASE_AMOUNT', self.base_amount)
        # Tam bərpa və mənfəət vuruqları: 1.0x -> 2.5x -> 6.5x -> 16.5x
        multipliers = [1.0, 2.5, 6.5, 16.5]
        if self.current_step <= len(multipliers):
            mult = multipliers[self.current_step - 1]
        else:
            mult = multipliers[-1] * (2.5 ** (self.current_step - len(multipliers)))
        return round(current_base * mult, 2)

    def on_win(self):
        """Uğurlu ticarətdən sonra addımı sıfırlayır."""
        logger.info(f"✅ Trade UĞURLU oldu (Addım {self.current_step}). Martingale sıfırlanır.")
        self.current_step = 1

    def on_loss(self) -> bool:
        """
        Uğursuz ticarətdən sonra addımı artırır.
        Növbəti cəhdin mümkün olub-olmadığını qaytarır.
        """
        logger.warning(f"❌ Trade UĞURSUZ oldu (Addım {self.current_step}).")
        if self.current_step < self.max_steps:
            self.current_step += 1
            logger.info(f"🔄 Martingale növbəti addıma keçir: Addım {self.current_step} (${self.get_current_amount()})")
            return True
        else:
            logger.error(f"🛑 Maksimum Martingale addımına ({self.max_steps}) çatıldı. Sıfırlanır.")
            self.current_step = 1
            return False


class PocketOptionTrader:
    """
    Pocket Option ticarət bota inteqrasiya sinfi.
    """

    def __init__(self, signal_engine=None):
        self.signal_engine = signal_engine
        self.ssid = settings.PO_SSID
        self.is_demo = settings.PO_IS_DEMO
        self.client = None
        self.martingale = MartingaleManager()
        self.is_connected = False
        self.trade_history = []
        self.total_wins = 0
        self.is_auto_trading = False  # İstifadəçi düyməyə basana qədər Avto-ticarət DEAKTİVDİR!
        self.loop = None

    async def connect(self) -> bool:
        """Pocket Option-a qoşulur."""
        if not self.ssid:
            logger.warning("⚠️  PO_SSID konfiqurasiya edilməyib.")
            return False

        if not PO_API_AVAILABLE:
            logger.warning("⚠️  PocketOption API kitabxanası yoxdur.")
            return False

        try:
            logger.info(f"🔌 Pocket Option-a qoşulunur... (Hesab: {'DEMO' if self.is_demo else 'REAL'})")
            self.client = AsyncPocketOptionClient(self.ssid, is_demo=self.is_demo)
            connected = await self.client.connect()
            self.is_connected = connected
            if connected:
                logger.info("✅ Pocket Option-a uğurla qoşuldu!")
                balance = await self.client.get_balance()
                logger.info(f"💰 Balans: {balance.balance} {balance.currency}")
            else:
                logger.error("❌ Pocket Option-a qoşulmaq mümkün olmadı. SSID-ni yoxlayın.")
            return connected
        except Exception as e:
            logger.error(f"❌ PO Qoşulma xətası: {e}")
            self.is_connected = False
            return False

    async def execute_trade_sequence(self, signal: Dict[str, Any], callback_notify=None):
        """
        Martingale strategiyası ilə siqnal üzrə ticarət ardıcıllığını icra edir (max 4 cəhd).
        """
        if not self.is_auto_trading:
            logger.info("ℹ️ Avto-ticarət söndürülüb (is_auto_trading=False). Əmr açılmır.")
            return

        target_wins = getattr(settings, 'TARGET_WIN_COUNT', 5)
        if self.total_wins >= target_wins:
            self.is_auto_trading = False
            logger.info(f"🏆 Hədəfə çatıldı ({self.total_wins}/{target_wins}). Avto-ticarət dayandırıldı.")
            if callback_notify:
                await callback_notify(f"🎉 <b>TƏBRİKLƏR! HƏDƏFƏ ÇATILDI!</b> 🏆\n"
                                      f"Sizin təyin etdiyiniz <b>{target_wins} Qazanc</b> tamamlandı!\n"
                                      f"🛑 Avto-ticarət avtomatik olaraq DAYANDIRILDI.")
            return

        symbol = signal['symbol']
        timeframe = signal['timeframe']
        direction = signal['direction']
        display_name = signal['display_name']

        po_asset = settings.PO_ASSET_MAPPING.get(symbol, symbol.replace('=X', ''))
        action = 'call' if direction == 'BUY' else 'put'
        duration = getattr(settings, 'DEFAULT_TRADE_DURATION', 30)

        logger.info(f"🚀 Turbo Ticarət ardıcıllığı başlayır: {display_name} | {direction} | TF: {duration}s")

        step = 1
        sequence_won = False
        retry_count = 0

        while step <= settings.MARTINGALE_MAX_STEPS:
            amount = self.martingale.get_current_amount()
            trade_info = {
                'symbol': symbol,
                'display_name': display_name,
                'direction': direction,
                'action': action,
                'amount': amount,
                'step': step,
                'max_steps': settings.MARTINGALE_MAX_STEPS,
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat(),
                'status': 'EXECUTING'
            }

            logger.info(f"🎯 Addım {step}/{settings.MARTINGALE_MAX_STEPS}: {display_name} - {action.upper()} ${amount}")

            # Əmri icra et və Pocket Option hesabında real balans dəyişikliyini gözlə
            trade_result = await self._place_single_trade(po_asset, action, amount, duration, signal)

            if trade_result['outcome'] == 'RETRY':
                retry_count += 1
                logger.warning(f"⚠️ Bağlantı xətasına görə Addım {step} təkrarlanacaq (Cəhd {retry_count}/3).")
                if retry_count >= 3:
                    self.is_auto_trading = False
                    logger.error("🛑 3 cəhddən sonra Pocket Option-a bağlanmaq mümkün olmadı. Avto-ticarət dayandırıldı.")
                    if callback_notify:
                        await callback_notify("🛑 <b>Pocket Option bağlantısı kəsildi.</b>\n"
                                              "Avto-ticarət təhlükəsizlik üçün DAYANDIRILDI.\n"
                                              "Yenidən başlatmaq üçün <b>▶️ Avto-Ticarəti Başlat</b> düyməsinə klikləyin.")
                    break
                await asyncio.sleep(3)
                continue

            retry_count = 0  # Uğurlu cəhddən sonra sıfırla

            if callback_notify:
                await callback_notify(f"⚡ <b>TURBO TİCARƏT İCRA EDİLİR</b> (Addım {step}/{settings.MARTINGALE_MAX_STEPS})\n"
                                      f"💱 <b>Aktiv:</b> {display_name}\n"
                                      f"📊 <b>Yön:</b> {'⬆️ CALL (BUY)' if action == 'call' else '⬇️ PUT (SELL)'}\n"
                                      f"💰 <b>Məbləğ:</b> ${amount}\n"
                                      f"⏱️ <b>Müddət:</b> {duration} Saniyə (Turbo S10)")

            trade_info['result'] = trade_result['outcome']
            trade_info['profit'] = trade_result['profit']
            trade_info['status'] = 'COMPLETED'
            self.trade_history.append(trade_info)

            if trade_result['outcome'] == 'WIN':
                sequence_won = True
                self.total_wins += 1
                self.martingale.on_win()
                msg = (f"✅ <b>TİCARƏT QAZANDI!</b> 🎉 (Hədəf: {self.total_wins}/{getattr(settings, 'TARGET_WIN_COUNT', 5)})\n"
                       f"💱 {display_name} (Addım {step})\n"
                       f"💵 Qazanc: +${trade_result['profit']:.2f}")
                logger.info(msg)
                if callback_notify:
                    await callback_notify(msg)
                
                target_count = getattr(settings, 'TARGET_WIN_COUNT', 5)
                if self.total_wins >= target_count:
                    target_msg = (f"🏆🎉 <b>{target_count} DƏFƏ QAZANC HƏDƏFİ TAMAMLANDI!</b> 🎉🏆\n\n"
                                  f"✨ Uğurla {self.total_wins} ticarət qazanıldı!\n"
                                  f"💰 Martingale mühərriki tapşırığı mükəmməl icra etdi.")
                    if callback_notify:
                        await callback_notify(target_msg)
                break
            else:
                has_next = self.martingale.on_loss()
                msg = (f"❌ <b>Ticarət Uğursuz Oldu</b> (Addım {step}/{settings.MARTINGALE_MAX_STEPS})\n"
                       f"💱 {display_name} - Məbləğ: ${amount}")
                logger.warning(msg)
                if callback_notify:
                    await callback_notify(msg)

                if has_next:
                    step += 1
                    if self.signal_engine:
                        new_sig = await self.signal_engine.generate_signal_async(symbol, timeframe) if hasattr(self.signal_engine, 'generate_signal_async') else self.signal_engine.generate_signal(symbol, timeframe)
                        if new_sig and new_sig['direction'] != 'NEUTRAL':
                            direction = new_sig['direction']
                            action = 'call' if direction == 'BUY' else 'put'
                            logger.info(f"🔄 Növbəti addım üçün yenidən analiz edildi. Yeni yön: {direction}")
                else:
                    logger.error(f"🛑 Maksimum Martingale addımına ({settings.MARTINGALE_MAX_STEPS}) çatıldı. Sıfırlanır.")
                    self.martingale.current_step = 1
                    break

        return sequence_won

    async def _place_single_trade(self, asset: str, action: str, amount: float,
                                  duration: int, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tək ticarət əmrini icra edir və Pocket Option serverində REAL BALANS dəyişikliyini yoxlayır.
        Bağlantı kəsildikdə dərhal LOSS vermir, yeniden bağlanmağa cəhd edir (RETRY).
        """
        if not self.is_connected or not self.client:
            logger.warning("🔌 Pocket Option bağlantısı kəsilib. Yenidən qoşulmağa cəhd edilir...")
            connected = await self.connect()
            if not connected:
                return {'outcome': 'RETRY', 'profit': 0.0}

        try:
            # 1. İlkin Balansı Götür
            bal_before = await self.client.get_balance()
            initial_balance = float(getattr(bal_before, 'balance', 0.0))
            
            order_dir = OrderDirection.CALL if action == 'call' else OrderDirection.PUT
            order_res = await self.client.place_order(asset=asset, amount=amount, direction=order_dir, duration=duration)
            order_id = getattr(order_res, 'order_id', None) or getattr(order_res, 'id', None) or getattr(order_res, 'request_id', None)
            
            logger.info(f"✅ PO Əmri Açıldı: ID={order_id}, ${amount}, {duration}s. İlkin Balans=${initial_balance:.2f}")
            
            # 2. Opsion müddətini tam olaraq gözlə (opsion müddəti + 4s server sync)
            await asyncio.sleep(duration + 4)

            # 3. Əməliyyat sonundakı YENİ Balansı Götür
            bal_after = await self.client.get_balance()
            final_balance = float(getattr(bal_after, 'balance', initial_balance))
            
            diff = round(final_balance - initial_balance, 2)
            logger.info(f"📊 PO Server Balans Analizi: Əvvəl=${initial_balance:.2f} -> Sonra=${final_balance:.2f} (Fərq=${diff:.2f})")

            # 4. Yalnız real olaraq balans artıbsa WIN təyin et!
            if diff > 0:
                logger.info(f"🎉 PO REAL QAZANC VERDİ! Profit: +${diff:.2f}")
                return {'outcome': 'WIN', 'profit': diff}
            elif diff < 0:
                logger.info(f"❌ PO REAL İTKİ VERDİ. Zərər: -${abs(diff):.2f}")
                return {'outcome': 'LOSS', 'profit': diff}
            else:
                if order_id and hasattr(self.client, 'check_order_result'):
                    closed_info = await self.client.check_order_result(order_id)
                    if closed_info:
                        win = (str(getattr(closed_info, 'result', '')).lower() == 'win') or (getattr(closed_info, 'profit', 0) > 0)
                        if win:
                            profit = getattr(closed_info, 'profit', round(amount * 0.85, 2))
                            return {'outcome': 'WIN', 'profit': profit}
                
                return {'outcome': 'LOSS', 'profit': -amount}
        except Exception as e:
            logger.error(f"PO Real Trade Xətası: {e}")
            self.is_connected = False
            return {'outcome': 'RETRY', 'profit': 0.0}
