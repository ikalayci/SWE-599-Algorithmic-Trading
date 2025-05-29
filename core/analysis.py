import numpy as np
import pandas as pd
from ta import momentum, trend, volatility
from typing import Dict, Optional, List
import logging
from utils.language_manager import LanguageManager

class MarketAnalyzer:
    """Market analizi yapan sınıf"""
    def __init__(self):
        # Dil yöneticisi
        self.lang = LanguageManager()
        
        # Analiz parametreleri
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.volume_ma_period = 20
        self.min_volume = 50000  # Minimum USDT hacmi

    def analyze_market(self, df: pd.DataFrame) -> Optional[Dict]:
        try:
            if len(df) < 100:  # Minimum veri gereksinimi
                return None

            # RSI hesapla
            rsi = momentum.RSIIndicator(df['close'], window=self.rsi_period)
            current_rsi = rsi.rsi().iloc[-1]

            # MACD hesapla
            macd = trend.MACD(df['close'])
            current_macd = macd.macd().iloc[-1]
            current_signal = macd.macd_signal().iloc[-1]
            current_hist = macd.macd_diff().iloc[-1]

            # Bollinger Bands
            bb = volatility.BollingerBands(df['close'])
            bb_upper = bb.bollinger_hband().iloc[-1]
            bb_middle = bb.bollinger_mavg().iloc[-1]
            bb_lower = bb.bollinger_lband().iloc[-1]

            # ADX
            adx = trend.ADXIndicator(df['high'], df['low'], df['close'])
            current_adx = adx.adx().iloc[-1]

            # Hacim analizi
            volume_sma = df['volume'].rolling(window=self.volume_ma_period).mean()
            volume_ratio = df['volume'].iloc[-1] / volume_sma.iloc[-1] if volume_sma.iloc[-1] > 0 else 0

            # Trend analizi
            ema_8 = df['close'].ewm(span=8).mean()
            ema_21 = df['close'].ewm(span=21).mean()
            trend_up = ema_8.iloc[-1] > ema_21.iloc[-1]  # Boolean olarak sakla
            trend_display = self.lang.__('trend_up') if trend_up else self.lang.__('trend_down')

            # BB pozisyonu hesapla
            current_price = df['close'].iloc[-1]
            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5

            # Skor hesapla
            score = self._calculate_score({
                'rsi': current_rsi,
                'macd': current_macd,
                'signal': current_signal,
                'hist': current_hist,
                'adx': current_adx,
                'volume_ratio': volume_ratio,
                'trend_up': trend_up,  # Boolean değer gönder
                'bb_position': bb_position
            })

            return {
                'score': score,
                'indicators': {
                    'rsi': current_rsi,
                    'macd': current_macd,
                    'macd_signal': current_signal,
                    'macd_hist': current_hist,
                    'adx': current_adx,
                    'volume_ratio': volume_ratio,
                    'bb_upper': bb_upper,
                    'bb_middle': bb_middle,
                    'bb_lower': bb_lower
                },
                'trend': trend_display,  # Görüntüleme için çevrilmiş metin
                'signals': self._generate_signals(score),
                'price_change_24h': self._calculate_price_change(df['close'])
            }

        except Exception as e:
            logging.error(f"{self.lang.__('market_analysis_error')}: {str(e)}")
            return None

    def _calculate_score(self, data: Dict) -> float:
        """
        Trading skoru hesapla (0-100 arası)
        Yüksek skor = Güçlü alım fırsatı
        """
        score = 50.0  # Başlangıç skoru

        # RSI katkısı
        if data['rsi'] < 30:
            score += 20  # Aşırı satım
        elif data['rsi'] > 70:
            score -= 20  # Aşırı alım
        else:
            score += 10 * (1 - abs(50 - data['rsi'])/50)

        # MACD katkısı
        if data['macd'] > data['signal']:
            score += 15
        else:
            score -= 15

        # ADX katkısı (trend gücü)
        if data['adx'] > 25:
            if data['trend_up']:  # Boolean değeri kontrol et
                score += 10
            else:
                score -= 10

        # Hacim katkısı
        if data['volume_ratio'] > 1.5:
            score += 10
        elif data['volume_ratio'] < 0.5:
            score -= 10

        # Bollinger Band pozisyonu
        bb_pos = data['bb_position']
        if bb_pos < 0.2:  # Alt banda yakın
            score += 15
        elif bb_pos > 0.8:  # Üst banda yakın
            score -= 15

        return max(0, min(100, score))  # 0-100 arasına sınırla

    def _generate_signals(self, score: float) -> str:
        """Skor bazlı sinyal üret"""
        if score >= 80:
            return self.lang.__('strong_buy')
        elif score >= 65:
            return self.lang.__('buy_signal')
        elif score <= 35:
            return self.lang.__('sell_signal')
        else:
            return self.lang.__('neutral')

    def _calculate_price_change(self, closes: np.ndarray) -> float:
        """24 saatlik fiyat değişimi hesapla"""
        try:
            if len(closes) >= 96:  # 15 dakikalık mum için 24 saat = 96 mum
                change = ((closes[-1] - closes[-96]) / closes[-96]) * 100
                return round(change, 2)
            return 0
        except:
            return 0

    def check_divergence(self, df: pd.DataFrame) -> Optional[Dict]:
        """RSI ve fiyat uyumsuzluklarını kontrol et"""
        try:
            closes = df['close'].values
            # ta kütüphanesi ile RSI hesaplama
            rsi_indicator = momentum.RSIIndicator(pd.Series(closes), window=self.rsi_period)
            rsi = rsi_indicator.rsi().values

            # Son 10 mumu kontrol et
            price_direction = 1 if closes[-1] > closes[-10] else -1
            rsi_direction = 1 if rsi[-1] > rsi[-10] else -1

            if price_direction != rsi_direction:
                return {
                    'type': self.lang.__('bull_divergence') if rsi_direction > price_direction else self.lang.__('bear_divergence'),
                    'strength': abs(float(rsi[-1] - rsi[-10]))
                }
            return None

        except Exception as e:
            logging.error(f"{self.lang.__('divergence_check_error')}: {str(e)}")
            return None