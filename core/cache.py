from threading import Lock
from datetime import datetime
from typing import Dict, Any, Optional

class CacheBase:
    """Temel cache sınıfı"""
    def __init__(self, max_size: int = 1000, expiry_seconds: int = 60):
        self.max_size = max_size
        self.expiry_seconds = expiry_seconds
        self.cache: Dict = {}
        self.lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """Cache'den veri al"""
        with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                if (datetime.now() - timestamp).seconds < self.expiry_seconds:
                    return value
                del self.cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Cache'e veri ekle"""
        with self.lock:
            # Cache doluysa en eski %10'u temizle
            if len(self.cache) >= self.max_size:
                sorted_items = sorted(self.cache.items(), key=lambda x: x[1][1])
                for old_key, _ in sorted_items[:self.max_size//10]:
                    del self.cache[old_key]
            
            self.cache[key] = (value, datetime.now())

    def clear(self) -> None:
        """Cache'i temizle"""
        with self.lock:
            self.cache.clear()

class PriceCache(CacheBase):
    """Fiyat bilgileri için özelleştirilmiş cache"""
    def __init__(self):
        super().__init__(max_size=500, expiry_seconds=2)  # Fiyatlar için kısa ömür

class OHLCVCache(CacheBase):
    """OHLCV verileri için özelleştirilmiş cache"""
    def __init__(self):
        super().__init__(max_size=100, expiry_seconds=300)  # 5 dakika cache süresi

    def get_for_timeframe(self, symbol: str, timeframe: str) -> Optional[Any]:
        """Belirli bir timeframe için OHLCV verisi al"""
        return self.get(f"{symbol}_{timeframe}")

    def set_for_timeframe(self, symbol: str, timeframe: str, data: Any) -> None:
        """Belirli bir timeframe için OHLCV verisi kaydet"""
        self.set(f"{symbol}_{timeframe}", data)

class IndicatorCache(CacheBase):
    """Teknik göstergeler için cache"""
    def __init__(self):
        super().__init__(max_size=200, expiry_seconds=60)  # 1 dakika cache süresi

    def get_indicator(self, symbol: str, indicator: str) -> Optional[Any]:
        """Belirli bir gösterge değerini al"""
        return self.get(f"{symbol}_{indicator}")

    def set_indicator(self, symbol: str, indicator: str, value: Any) -> None:
        """Belirli bir gösterge değerini kaydet"""
        self.set(f"{symbol}_{indicator}", value)