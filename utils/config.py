import os
import sys
import json
import logging
from typing import Dict

class ConfigManager:
    def __init__(self):
        # Ana dizini belirle
        if getattr(sys, 'frozen', False):
            self.app_dir = os.path.dirname(sys.executable)
        else:
            # Eğer utils içindeyse 2 seviye yukarı, değilse bulunduğu dizini al
            if os.path.basename(os.path.dirname(os.path.abspath(__file__))) == 'utils':
                self.app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            else:
                self.app_dir = os.path.dirname(os.path.abspath(__file__))

        # _internal dizini oluştur
        self.internal_dir = os.path.join(self.app_dir, '_internal')
        try:
            if not os.path.exists(self.internal_dir):
                os.makedirs(self.internal_dir)
                print(f"Created _internal directory at: {self.internal_dir}")  # Debug için
        except Exception as e:
            print(f"Error creating _internal directory: {str(e)}")  # Debug için

        # Config dosyası yolu
        self.config_file = os.path.join(self.internal_dir, 'config.json')
        
        # Varsayılan config'i hemen oluştur
        try:
            if not os.path.exists(self.config_file):
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.default_config, f, indent=4)
                print(f"Created config file at: {self.config_file}")  # Debug için
        except Exception as e:
            print(f"Error creating config file: {str(e)}")  # Debug için
        
        # Varsayılan ayarlar
        self.default_config = {
                        
            # API bilgileri
            'api_key': '',
            'api_secret': '',
            
            # Trading ayarları
            'timeframe': '15m',
            'stop_loss': 3.0,
            'take_profit': 2.0,
            'max_positions': 5,
            'max_usdt': 10.0,
            'min_score': 75,
            'min_volume': 50000,
            
            # Yasaklı coinler
            'excluded_coins': [
                'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ETH/USDT', 'EURI/USDT', 
                'AEUR/USDT', 'EUR/USDT', 'FDUSD/USDT', 'USDP/USDT', 'PAXG/USDT', 'TUSD/USDT', 
                'USDS/USDT', 'USDT/USDT', 'USD/USDT', 'USDC/USDT', 'BUSD/USDT', 'DAI/USDT', 'SUSD/USDT',
                'EURS/USDT', 'EURI/USDT', 'USDK/USDT', 'USDT/USDT', 'USNBT/USDT', 'USDP/USDT', 'USDS/USDT',
                'USDSB/USDT', 'USDT/USDT', 'USDTB/USDT', 'USDTT/USDT', 'USDTZ/USDT',
            ],
            
            # Uygulama ayarları
            'theme': 'dark',
            'language': 'tr'
        }
        
        # Mevcut ayarları yükle
        self.config = self.load_config()
        
    def load_config(self) -> Dict:
        """Ayarları dosyadan yükle"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    stored_config = json.load(f)
                    # Varsayılan ayarları güncelle
                    config = self.default_config.copy()
                    config.update(stored_config)
                    return config
            return self.default_config.copy()
            
        except Exception as e:
            logging.error(f"Ayar yükleme hatası: {str(e)}")
            return self.default_config.copy()

    def save_config(self, config_data: Dict) -> bool:
        """Ayarları dosyaya kaydet"""
        try:
            # Mevcut ayarları yükle
            current_config = self.load_config()
            
            # Yeni ayarları güncellerken mevcut değerleri koru
            for key, value in config_data.items():
                if value is not None:  # Sadece boş olmayan değerleri güncelle
                    current_config[key] = value
            
            # Tüm ayarları kaydet
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(current_config, f, indent=4)
            
            # Ayarları güncelle
            self.config = current_config
            return True
            
        except Exception as e:
            logging.error(f"Ayar kaydetme hatası: {str(e)}")
            return False
    
    def get_value(self, key: str, default=None):
        """Belirli bir ayarı getir"""
        return self.config.get(key, default)

    def set_value(self, key: str, value) -> bool:
        """Tek bir ayarı güncelle"""
        try:
            self.config[key] = value
            return self.save_config(self.config)
        except Exception as e:
            logging.error(f"Ayar güncelleme hatası: {str(e)}")
            return False

    def reset_to_defaults(self) -> bool:
        """Tüm ayarları varsayılana döndür"""
        try:
            self.config = self.default_config.copy()
            return self.save_config(self.config)
        except Exception as e:
            logging.error(f"Ayarları sıfırlama hatası: {str(e)}")
            return False

    def validate_trading_config(self) -> tuple[bool, str]:
        """Trading ayarlarının geçerliliğini kontrol et"""
        try:
            required_fields = ['api_key', 'api_secret', 'max_usdt']
            for field in required_fields:
                if not self.config.get(field):
                    return False, f"'{field}' ayarı gerekli"

            # Sayısal değer kontrolleri
            if self.config['max_usdt'] < 10:
                return False, "Minimum USDT değeri 10 olmalı"
            if self.config['max_positions'] < 1:
                return False, "En az 1 pozisyon olmalı"
            if not (0.1 <= self.config['stop_loss'] <= 100.0):
                return False, "Stop loss değeri 0.1-100 arasında olmalı"
            if not (0.1 <= self.config['take_profit'] <= 100.0):
                return False, "Take profit değeri 0.1-100 arasında olmalı"
            
            # Yasaklı ve izinli coin listesi kontrolü
            if not isinstance(self.config.get('excluded_coins', []), list):
                return False, "Yasaklı coin listesi geçersiz"
            if not isinstance(self.config.get('whitelisted_coins', []), list):
                return False, "İzinli coin listesi geçersiz"

            # Trading kuralları kontrolü
            rules = self.config.get('trading_rules', {})
            if not isinstance(rules, dict):
                return False, "Trading kuralları geçersiz"

            return True, "Geçerli ayarlar"
            
        except Exception as e:
            return False, f"Ayar doğrulama hatası: {str(e)}"
        
    def update_excluded_coins(self, coins: list) -> bool:
        """Yasaklı coin listesini güncelle"""
        try:
            # Coin formatını kontrol et ve düzelt
            formatted_coins = []
            for coin in coins:
                coin = coin.strip().upper()
                if not coin.endswith('/USDT'):
                    coin = f"{coin}/USDT"
                formatted_coins.append(coin)
            
            return self.set_value('excluded_coins', formatted_coins)
        except Exception as e:
            logging.error(f"Yasaklı coin güncelleme hatası: {str(e)}")
            return False

    def get_trading_rules(self) -> dict:
        """Trading kurallarını getir"""
        return self.config.get('trading_rules', self.default_config['trading_rules'])
    
    def ensure_resources(self):
        """Program için gerekli dosyaların varlığını kontrol et ve oluştur"""
        try:
            # İkon için kontrol
            icon_path = os.path.join(self.internal_dir, 'cryptotrader.ico')
            if not os.path.exists(icon_path):
                # İkonu _internal klasörüne kopyala
                if getattr(sys, 'frozen', False):
                    # PyInstaller ile paketlenmiş
                    source_icon = os.path.join(self.app_dir, 'cryptotrader.ico')
                else:
                    # Normal Python scripti
                    source_icon = os.path.join(self.app_dir, 'resources', 'cryptotrader.ico')
                    
                if os.path.exists(source_icon):
                    import shutil
                    shutil.copy2(source_icon, icon_path)
                
            return icon_path
                
        except Exception as e:
            logging.error(f"Kaynak dosya kontrolü hatası: {str(e)}")
            return None