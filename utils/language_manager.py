import os
import sys
import json
import logging
from typing import Dict

class LanguageManager:
    """
    Çoklu dil desteği sağlayan yönetici sınıf.
    Farklı dil dosyalarını yükler ve çevirileri yönetir.
    """
    def __init__(self):
        # Desteklenen diller ve isimleri
        self.languages = {
            'tr': 'Türkçe',
            'en': 'English',
            'es': 'Español',
            'de': 'Deutsch'
        }
        
        # Varsayılan dil
        self.current_language = 'en'
        
        # Çeviri verileri
        self.translations: Dict[str, Dict] = {}
        
        # Çeviri dosyalarını yükle
        self.load_translations()
        
        # Kayıtlı dil tercihini yükle
        self.load_language_preference()

    def __(self, key: str) -> str:
        """
        Çeviri getir (PHP benzeri kısa kullanım)
        Örnek kullanım: lang.__('hello_world')
        """
        return self.translations.get(self.current_language, {}).get(key, key)

    def set_language(self, lang_code: str) -> bool:
        """
        Dil değiştirme işlemi.
        Değişiklik başarılı olursa True döner.
        """
        if lang_code in self.languages:
            self.current_language = lang_code
            try:
                # Tercihi kaydet
                self.save_language_preference()
                return True
            except Exception as e:
                logging.error(f"Dil tercihi kaydetme hatası: {str(e)}")
        return False

    def _get_internal_dir(self) -> str:
        """İç dosyaların saklandığı dizini al"""
        if getattr(sys, 'frozen', False):
            # PyInstaller ile paketlenmiş
            base_path = os.path.dirname(sys.executable)
        else:
            # Normal Python scripti
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        internal_dir = os.path.join(base_path, '_internal')
        if not os.path.exists(internal_dir):
            os.makedirs(internal_dir)
            
        return internal_dir

    def save_language_preference(self) -> bool:
        """Dil tercihini kaydet"""
        try:
            internal_dir = self._get_internal_dir()
            config_file = os.path.join(internal_dir, 'language_preference.json')
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({'current_language': self.current_language}, f)
            return True
            
        except Exception as e:
            logging.error(f"Dil tercihi kaydetme hatası: {str(e)}")
            return False

    def load_language_preference(self):
        """Kayıtlı dil tercihini yükle"""
        try:
            config_file = os.path.join(self._get_internal_dir(), 'language_preference.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('current_language') in self.languages:
                        self.current_language = data['current_language']
                        
        except Exception as e:
            logging.error(f"Dil tercihi yükleme hatası: {str(e)}")

    def load_translations(self):
        """Dil dosyalarını yükle"""
        try:
            internal_dir = self._get_internal_dir()
            lang_dir = os.path.join(internal_dir, 'languages')
            
            # Dil dizinini oluştur
            if not os.path.exists(lang_dir):
                os.makedirs(lang_dir)
                # Varsayılan çevirileri oluştur
                self._create_default_translations(lang_dir)
            
            # Her dil için çeviri dosyasını yükle
            for lang_code in self.languages.keys():
                lang_file = os.path.join(lang_dir, f'{lang_code}.json')
                try:
                    if os.path.exists(lang_file):
                        with open(lang_file, 'r', encoding='utf-8') as f:
                            self.translations[lang_code] = json.load(f)
                    else:
                        logging.warning(f"Dil dosyası bulunamadı: {lang_file}")
                        
                except json.JSONDecodeError as e:
                    logging.error(f"JSON parse hatası ({lang_code}.json): {str(e)}")
                except Exception as e:
                    logging.error(f"Dil dosyası yükleme hatası ({lang_code}.json): {str(e)}")
                    
        except Exception as e:
            logging.error(f"Dil dosyaları yükleme hatası: {str(e)}")
            self.translations = {}

    # language_manager.py içindeki _create_default_translations metodunu güncelle

    # language_manager.py içindeki _create_default_translations metodunu güncelle

    # language_manager.py içindeki _create_default_translations metodunu güncelle

    def _create_default_translations(self, lang_dir: str):
        """Varsayılan çeviri dosyalarını oluştur"""
        default_translations = {
            'tr': {
                # Ana menü
                'settings': 'Ayarlar',
                'active_trades': 'Aktif İşlemler',
                'trades_history': 'İşlem Geçmişi',
                'statistics': 'İstatistikler',
                'opportunities': 'Fırsatlar',
                'logs': 'Kayıtlar',
                
                # Ayarlar
                'api_key': 'API Anahtarı',
                'api_secret': 'API Gizli Anahtarı',
                'max_usdt': 'Maksimum USDT',
                'position': 'Pozisyon',
                'max_positions': 'Maksimum Pozisyon',
                'min_score': 'Minimum Skor',
                'excluded_coins': 'Yasaklı Coinler',
                'ui_settings': 'UI Ayarları',
                'live_analysis_results': 'Canlı Analiz Sonuçları',
                'update_interval': 'Güncelleme Sıklığı',
                
                # Butonlar
                'start': 'Başlat',
                'stop': 'Durdur',
                'save': 'Kaydet',
                'reset_to_default': 'Varsayılana Dön',
                
                # Durumlar
                'license_status': 'Lisans Durumu',
                'days_remaining': 'gün kaldı',
                'bot_not_started': 'Bot başlatılamadı',
                'ready': 'Hazır',
                'trading_active': 'Trading aktif',
                'trading_started': 'Trading başlatıldı',
                'trading_stopping': 'Trading durduruluyor...',
                'trading_stopped': 'Trading durduruldu',
                
                # Tablolar
                'symbol': 'Sembol',
                'price': 'Fiyat',
                'change_24h': '24s Değişim',
                'volume': 'Hacim',
                'score': 'Skor',
                'status': 'Durum',
                'signal': 'Sinyal',
                'last_update': 'Son Güncelleme',
                'coin': 'Coin',
                'entry_price': 'Giriş Fiyatı',
                'current_price': 'Güncel Fiyat',
                'amount': 'Miktar',
                'profit_loss': 'Kâr/Zarar',
                'date': 'Tarih',
                'type': 'Tür',
                'total': 'Toplam',
                'trades': 'İşlemler',
                
                # Trading engine mesajları
                'trading_engine_started': 'Trading Engine başlatıldı',
                'trading_engine_start_error': 'Trading Engine başlatma hatası',
                'manual_sale_completed': 'Manuel satış gerçekleşti',
                'manual_close_error': 'Manuel kapama kaydı hatası',
                'trading_system_stopping': 'Trading sistemi durduruluyor...',
                'trading_system_stopped': 'Trading sistemi durduruldu',
                'trading_loop_error': 'Trading döngüsü hatası',
                'progress': 'İlerleme',
                'coins_analyzed': 'coin analiz edildi',
                'opportunity_found': 'Fırsat bulundu',
                'scan_completed': 'Tarama tamamlandı',
                'opportunities_found': 'fırsat bulundu',
                'market_scan_error': 'Market tarama hatası',
                'scan_error': 'Tarama hatası',
                'validation_error': 'Validasyon hatası',
                'insufficient_balance': 'Hedef USDT miktarından daha az bakiye mevcut',
                'target': 'Hedef',
                'available': 'Mevcut',
                'buy_order_failed': 'için satış emri başarısız',
                'sell_order_error': 'Satış emri hatası',
                'position_close_error': 'Pozisyon kapatma hatası',
                'position_not_found': 'Pozisyon bulunamadı',
                'coin_balance_error': 'Coin bakiyesi alınamadı',
                'amount_correction': 'Satılacak miktar düzeltiliyor',
                'no_balance_to_sell': 'Satılacak bakiye yok',
                'sell_error': 'Satış hatası',
                'position_check_error': 'Pozisyon kontrol hatası',
                'position_tracking_error': 'Pozisyon takip hatası',
                'buy_error': 'Alım hatası',
                'buy_completed': 'Alım gerçekleşti',
                'sale_completed': 'Satış gerçekleşti',
                'entry': 'Giriş',
                'exit': 'Çıkış',
                'profit': 'Kâr',
                'reason': 'Sebep',
                'analysis_score': 'Analiz Skoru',
                'manual_stop': 'MANUEL-DURDURMA',
                'open_position': 'Açık Pozisyon',
                'weak_buy': 'ZAYIF ALIM',
                'wait': 'BEKLE',
                'stop_loss_reason': 'STOP-LOSS',
                'take_profit_reason': 'TAKE-PROFIT',
                
                # İşlem türleri
                'buy': 'ALIŞ',
                'sell': 'SATIŞ',
                
                # Mesajlar
                'api_credentials_required': 'API bilgileri gerekli!',
                'trading_start_error': 'Trading başlatma hatası',
                'trading_stop_error': 'Trading durdurma hatası',
                'open_positions': 'Açık Pozisyonlar',
                'close_positions_question': 'Açık pozisyonları kapatmak istiyor musunuz?',
                'closing_positions': 'Açık pozisyonlar kapatılıyor...',
                'all_positions_closed': 'Tüm pozisyonlar başarıyla kapatıldı',
                'some_positions_not_closed': 'Bazı pozisyonlar kapatılamadı!',
                'excluded_coins_updated': 'Yasaklı coin listesi güncellendi',
                'excluded_coins_update_error': 'Yasaklı coin listesi güncellenemedi',
                
                # Cüzdan
                'usdt_balance': 'USDT Bakiye',
                'total_profit': 'Toplam Kâr',
                
                # Tarama
                'scanned_coins': 'Taranan Coin',
                'last_scan': 'Son Tarama',
                
                # Hatalar
                'balance_update_error': 'Bakiye güncelleme hatası',
                'profit_update_error': 'Kâr güncelleme hatası',
                'trade_count_update_error': 'İşlem sayısı güncelleme hatası',
                'table_update_error': 'Tablo güncelleme hatası',
                'history_table_update_error': 'Geçmiş tablosu güncelleme hatası',
                'ui_update_error': 'UI güncelleme hatası',
                
                # Dil
                'language': 'Dil',
                'language_changed': 'Dil değiştirildi'
            },
            'en': {
                # Main menu
                'settings': 'Settings',
                'active_trades': 'Active Trades',
                'trades_history': 'Trade History',
                'statistics': 'Statistics',
                'opportunities': 'Opportunities',
                'logs': 'Logs',
                
                # Settings
                'api_key': 'API Key',
                'api_secret': 'API Secret',
                'max_usdt': 'Maximum USDT',
                'position': 'Position',
                'max_positions': 'Maximum Positions',
                'min_score': 'Minimum Score',
                'excluded_coins': 'Excluded Coins',
                'ui_settings': 'UI Settings',
                'live_analysis_results': 'Live Analysis Results',
                'update_interval': 'Update Interval',
                
                # Buttons
                'start': 'Start',
                'stop': 'Stop',
                'save': 'Save',
                'reset_to_default': 'Reset to Default',
                
                # Status
                'license_status': 'License Status',
                'days_remaining': 'days remaining',
                'bot_not_started': 'Bot could not be started',
                'ready': 'Ready',
                'trading_active': 'Trading active',
                'trading_started': 'Trading started',
                'trading_stopping': 'Trading stopping...',
                'trading_stopped': 'Trading stopped',
                
                # Tables
                'symbol': 'Symbol',
                'price': 'Price',
                'change_24h': '24h Change',
                'volume': 'Volume',
                'score': 'Score',
                'status': 'Status',
                'signal': 'Signal',
                'last_update': 'Last Update',
                'coin': 'Coin',
                'entry_price': 'Entry Price',
                'current_price': 'Current Price',
                'amount': 'Amount',
                'profit_loss': 'Profit/Loss',
                'date': 'Date',
                'type': 'Type',
                'total': 'Total',
                'trades': 'Trades',
                
                # Trading engine messages
                'trading_engine_started': 'Trading Engine started',
                'trading_engine_start_error': 'Trading Engine start error',
                'manual_sale_completed': 'Manual sale completed',
                'manual_close_error': 'Manual close record error',
                'trading_system_stopping': 'Trading system stopping...',
                'trading_system_stopped': 'Trading system stopped',
                'trading_loop_error': 'Trading loop error',
                'progress': 'Progress',
                'coins_analyzed': 'coins analyzed',
                'opportunity_found': 'Opportunity found',
                'scan_completed': 'Scan completed',
                'opportunities_found': 'opportunities found',
                'market_scan_error': 'Market scan error',
                'scan_error': 'Scan error',
                'validation_error': 'Validation error',
                'insufficient_balance': 'Available balance is less than target USDT amount',
                'target': 'Target',
                'available': 'Available',
                'buy_order_failed': 'sell order failed for',
                'sell_order_error': 'Sell order error',
                'position_close_error': 'Position close error',
                'position_not_found': 'Position not found',
                'coin_balance_error': 'Could not get coin balance',
                'amount_correction': 'Correcting amount to sell',
                'no_balance_to_sell': 'No balance to sell',
                'sell_error': 'Sell error',
                'position_check_error': 'Position check error',
                'position_tracking_error': 'Position tracking error',
                'buy_error': 'Buy error',
                'buy_completed': 'Buy completed',
                'sale_completed': 'Sale completed',
                'entry': 'Entry',
                'exit': 'Exit',
                'profit': 'Profit',
                'reason': 'Reason',
                'analysis_score': 'Analysis Score',
                'manual_stop': 'MANUAL-STOP',
                'open_position': 'Open Position',
                'weak_buy': 'WEAK BUY',
                'wait': 'WAIT',
                'stop_loss_reason': 'STOP-LOSS',
                'take_profit_reason': 'TAKE-PROFIT',
                
                # Trade types
                'buy': 'BUY',
                'sell': 'SELL',
                
                # Messages
                'api_credentials_required': 'API credentials required!',
                'trading_start_error': 'Trading start error',
                'trading_stop_error': 'Trading stop error',
                'open_positions': 'Open Positions',
                'close_positions_question': 'Do you want to close open positions?',
                'closing_positions': 'Closing open positions...',
                'all_positions_closed': 'All positions closed successfully',
                'some_positions_not_closed': 'Some positions could not be closed!',
                'excluded_coins_updated': 'Excluded coins list updated',
                'excluded_coins_update_error': 'Excluded coins list could not be updated',
                
                # Wallet
                'usdt_balance': 'USDT Balance',
                'total_profit': 'Total Profit',
                
                # Scanning
                'scanned_coins': 'Scanned Coins',
                'last_scan': 'Last Scan',
                
                # Errors
                'balance_update_error': 'Balance update error',
                'profit_update_error': 'Profit update error',
                'trade_count_update_error': 'Trade count update error',
                'table_update_error': 'Table update error',
                'history_table_update_error': 'History table update error',
                'ui_update_error': 'UI update error',
                
                # Language
                'language': 'Language',
                'language_changed': 'Language changed'
            },
            'es': {
                # Menú principal
                'settings': 'Configuración',
                'active_trades': 'Operaciones Activas',
                'trades_history': 'Historial de Operaciones',
                'statistics': 'Estadísticas',
                'opportunities': 'Oportunidades',
                'logs': 'Registros',
                
                # Configuración
                'api_key': 'Clave API',
                'api_secret': 'Secreto API',
                'max_usdt': 'USDT Máximo',
                'position': 'Posición',
                'max_positions': 'Posiciones Máximas',
                'min_score': 'Puntuación Mínima',
                'excluded_coins': 'Monedas Excluidas',
                'ui_settings': 'Configuración de UI',
                'live_analysis_results': 'Resultados de Análisis en Vivo',
                'update_interval': 'Intervalo de Actualización',
                
                # Botones
                'start': 'Iniciar',
                'stop': 'Detener',
                'save': 'Guardar',
                'reset_to_default': 'Restablecer Predeterminado',
                
                # Estado
                'license_status': 'Estado de Licencia',
                'days_remaining': 'días restantes',
                'bot_not_started': 'El bot no pudo iniciarse',
                'ready': 'Listo',
                'trading_active': 'Trading activo',
                'trading_started': 'Trading iniciado',
                'trading_stopping': 'Deteniendo trading...',
                'trading_stopped': 'Trading detenido',
                
                # Tablas
                'symbol': 'Símbolo',
                'price': 'Precio',
                'change_24h': 'Cambio 24h',
                'volume': 'Volumen',
                'score': 'Puntuación',
                'status': 'Estado',
                'signal': 'Señal',
                'last_update': 'Última Actualización',
                'coin': 'Moneda',
                'entry_price': 'Precio de Entrada',
                'current_price': 'Precio Actual',
                'amount': 'Cantidad',
                'profit_loss': 'Ganancia/Pérdida',
                'date': 'Fecha',
                'type': 'Tipo',
                'total': 'Total',
                'trades': 'Operaciones',
                
                # Mensajes del motor de trading
                'trading_engine_started': 'Motor de Trading iniciado',
                'trading_engine_start_error': 'Error al iniciar Motor de Trading',
                'manual_sale_completed': 'Venta manual completada',
                'manual_close_error': 'Error de registro de cierre manual',
                'trading_system_stopping': 'Sistema de trading deteniéndose...',
                'trading_system_stopped': 'Sistema de trading detenido',
                'trading_loop_error': 'Error en bucle de trading',
                'progress': 'Progreso',
                'coins_analyzed': 'monedas analizadas',
                'opportunity_found': 'Oportunidad encontrada',
                'scan_completed': 'Escaneo completado',
                'opportunities_found': 'oportunidades encontradas',
                'market_scan_error': 'Error de escaneo de mercado',
                'scan_error': 'Error de escaneo',
                'validation_error': 'Error de validación',
                'insufficient_balance': 'El saldo disponible es menor que la cantidad USDT objetivo',
                'target': 'Objetivo',
                'available': 'Disponible',
                'buy_order_failed': 'orden de venta falló para',
                'sell_order_error': 'Error de orden de venta',
                'position_close_error': 'Error al cerrar posición',
                'position_not_found': 'Posición no encontrada',
                'coin_balance_error': 'No se pudo obtener el saldo de la moneda',
                'amount_correction': 'Corrigiendo cantidad a vender',
                'no_balance_to_sell': 'Sin saldo para vender',
                'sell_error': 'Error de venta',
                'position_check_error': 'Error de verificación de posición',
                'position_tracking_error': 'Error de seguimiento de posición',
                'buy_error': 'Error de compra',
                'buy_completed': 'Compra completada',
                'sale_completed': 'Venta completada',
                'entry': 'Entrada',
                'exit': 'Salida',
                'profit': 'Ganancia',
                'reason': 'Razón',
                'analysis_score': 'Puntuación de Análisis',
                'manual_stop': 'PARADA-MANUAL',
                'open_position': 'Posición Abierta',
                'weak_buy': 'COMPRA DÉBIL',
                'wait': 'ESPERAR',
                'stop_loss_reason': 'STOP-LOSS',
                'take_profit_reason': 'TAKE-PROFIT',
                
                # Tipos de operación
                'buy': 'COMPRA',
                'sell': 'VENTA',
                
                # Mensajes
                'api_credentials_required': '¡Se requieren credenciales API!',
                'trading_start_error': 'Error al iniciar trading',
                'trading_stop_error': 'Error al detener trading',
                'open_positions': 'Posiciones Abiertas',
                'close_positions_question': '¿Desea cerrar las posiciones abiertas?',
                'closing_positions': 'Cerrando posiciones abiertas...',
                'all_positions_closed': 'Todas las posiciones cerradas exitosamente',
                'some_positions_not_closed': '¡Algunas posiciones no pudieron cerrarse!',
                'excluded_coins_updated': 'Lista de monedas excluidas actualizada',
                'excluded_coins_update_error': 'No se pudo actualizar la lista de monedas excluidas',
                
                # Cartera
                'usdt_balance': 'Balance USDT',
                'total_profit': 'Ganancia Total',
                
                # Escaneo
                'scanned_coins': 'Monedas Escaneadas',
                'last_scan': 'Último Escaneo',
                
                # Errores
                'balance_update_error': 'Error al actualizar balance',
                'profit_update_error': 'Error al actualizar ganancia',
                'trade_count_update_error': 'Error al actualizar conteo de operaciones',
                'table_update_error': 'Error al actualizar tabla',
                'history_table_update_error': 'Error al actualizar tabla de historial',
                'ui_update_error': 'Error al actualizar UI',
                
                # Idioma
                'language': 'Idioma',
                'language_changed': 'Idioma cambiado'
            },
            'de': {
                # Hauptmenü
                'settings': 'Einstellungen',
                'active_trades': 'Aktive Trades',
                'trades_history': 'Trade-Verlauf',
                'statistics': 'Statistiken',
                'opportunities': 'Chancen',
                'logs': 'Protokolle',
                
                # Einstellungen
                'api_key': 'API-Schlüssel',
                'api_secret': 'API-Geheimnis',
                'max_usdt': 'Maximum USDT',
                'position': 'Position',
                'max_positions': 'Maximale Positionen',
                'min_score': 'Mindestpunktzahl',
                'excluded_coins': 'Ausgeschlossene Coins',
                'ui_settings': 'UI-Einstellungen',
                'live_analysis_results': 'Live-Analyseergebnisse',
                'update_interval': 'Aktualisierungsintervall',
                
                # Schaltflächen
                'start': 'Starten',
                'stop': 'Stoppen',
                'save': 'Speichern',
                'reset_to_default': 'Auf Standard zurücksetzen',
                
                # Status
                'license_status': 'Lizenzstatus',
                'days_remaining': 'Tage verbleibend',
                'bot_not_started': 'Bot konnte nicht gestartet werden',
                'ready': 'Bereit',
                'trading_active': 'Trading aktiv',
                'trading_started': 'Trading gestartet',
                'trading_stopping': 'Trading wird gestoppt...',
                'trading_stopped': 'Trading gestoppt',
                
                # Tabellen
                'symbol': 'Symbol',
                'price': 'Preis',
                'change_24h': '24h Änderung',
                'volume': 'Volumen',
                'score': 'Punktzahl',
                'status': 'Status',
                'signal': 'Signal',
                'last_update': 'Letzte Aktualisierung',
                'coin': 'Coin',
                'entry_price': 'Einstiegspreis',
                'current_price': 'Aktueller Preis',
                'amount': 'Menge',
                'profit_loss': 'Gewinn/Verlust',
                'date': 'Datum',
                'type': 'Typ',
                'total': 'Gesamt',
                'trades': 'Trades',
                
                #Trading-Engine-Nachrichten
                'trading_engine_started': 'Trading-Engine gestartet',
                'trading_engine_start_error': 'Trading-Engine-Startfehler',
                'manual_sale_completed': 'Manueller Verkauf abgeschlossen',
                'manual_close_error': 'Manueller Schließungsfehler',
                'trading_system_stopping': 'Trading-System wird gestoppt...',
                'trading_system_stopped': 'Trading-System gestoppt',
                'trading_loop_error': 'Trading-Schleifenfehler',
                'progress': 'Fortschritt',
                'coins_analyzed': 'Coins analysiert',
                'opportunity_found': 'Chance gefunden',
                'scan_completed': 'Scan abgeschlossen',
                'opportunities_found': 'Chancen gefunden',
                'market_scan_error': 'Marktscan-Fehler',
                'scan_error': 'Scan-Fehler',
                'validation_error': 'Validierungsfehler',
                'insufficient_balance': 'Verfügbares Guthaben ist kleiner als Ziel-USDT-Betrag',
                'target': 'Ziel',
                'available': 'Verfügbar',
                'buy_order_failed': 'Verkaufsauftrag fehlgeschlagen für',
                'sell_order_error': 'Verkaufsauftragsfehler',
                'position_close_error': 'Positionsschließungsfehler',
                'position_not_found': 'Position nicht gefunden',
                'coin_balance_error': 'Coin-Guthaben konnte nicht abgerufen werden',
                'amount_correction': 'Zu verkaufende Menge wird korrigiert',
                'no_balance_to_sell': 'Kein Guthaben zum Verkaufen',
                'sell_error': 'Verkaufsfehler',
                'position_check_error': 'Positionsprüfungsfehler',
                'position_tracking_error': 'Positionsverfolgungsfehler',
                'buy_error': 'Kauffehler',
                'buy_completed': 'Kauf abgeschlossen',
                'sale_completed': 'Verkauf abgeschlossen',
                'entry': 'Einstieg',
                'exit': 'Ausstieg',
                'profit': 'Gewinn',
                'reason': 'Grund',
                'analysis_score': 'Analysepunktzahl',
                'manual_stop': 'MANUELLER-STOPP',
                'open_position': 'Offene Position',
                'weak_buy': 'SCHWACHER KAUF',
                'wait': 'WARTEN',
                'stop_loss_reason': 'STOP-LOSS',
                'take_profit_reason': 'TAKE-PROFIT',
                
                # Handelstypen
                'buy': 'KAUF',
                'sell': 'VERKAUF',
                
                # Nachrichten
                'api_credentials_required': 'API-Anmeldedaten erforderlich!',
                'trading_start_error': 'Fehler beim Starten des Tradings',
                'trading_stop_error': 'Fehler beim Stoppen des Tradings',
                'open_positions': 'Offene Positionen',
                'close_positions_question': 'Möchten Sie offene Positionen schließen?',
                'closing_positions': 'Schließe offene Positionen...',
                'all_positions_closed': 'Alle Positionen erfolgreich geschlossen',
                'some_positions_not_closed': 'Einige Positionen konnten nicht geschlossen werden!',
                'excluded_coins_updated': 'Liste der ausgeschlossenen Coins aktualisiert',
                'excluded_coins_update_error': 'Liste der ausgeschlossenen Coins konnte nicht aktualisiert werden',
                
                # Geldbörse
                'usdt_balance': 'USDT-Guthaben',
                'total_profit': 'Gesamtgewinn',
                
                # Scannen
                'scanned_coins': 'Gescannte Coins',
                'last_scan': 'Letzter Scan',
                
                # Fehler
                'balance_update_error': 'Fehler beim Aktualisieren des Guthabens',
                'profit_update_error': 'Fehler beim Aktualisieren des Gewinns',
                'trade_count_update_error': 'Fehler beim Aktualisieren der Trade-Anzahl',
                'table_update_error': 'Fehler beim Aktualisieren der Tabelle',
                'history_table_update_error': 'Fehler beim Aktualisieren der Verlaufstabelle',
                'ui_update_error': 'UI-Aktualisierungsfehler',
                
                # Sprache
                'language': 'Sprache',
                'language_changed': 'Sprache geändert'
            }
        }
        
        # Her dil için varsayılan çevirileri kaydet
        for lang_code, translations in default_translations.items():
            file_path = os.path.join(lang_dir, f'{lang_code}.json')
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(translations, f, ensure_ascii=False, indent=4)
                except Exception as e:
                    logging.error(f"Varsayılan çeviri oluşturma hatası ({lang_code}): {str(e)}")