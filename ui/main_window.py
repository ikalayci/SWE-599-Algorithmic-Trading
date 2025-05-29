from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QLineEdit, QPushButton, QTabWidget,
                           QSpinBox, QDoubleSpinBox, QComboBox, QFrame,
                           QTableWidget, QHeaderView, QGridLayout, QTableWidgetItem, QTextEdit, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QColor
from datetime import datetime
from utils.config import ConfigManager
from utils.logger import Logger
from utils.language_manager import LanguageManager
from core.trading import TradingEngine
from logging import Handler
import logging, os
from ui.tooltip import get_score_tooltip_text

APP_VERSION = "1"
APP_NAME = f"CryptoTrader v{APP_VERSION}"

class MainWindow(QMainWindow):
    # Dil değişikliği sinyali
    language_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Yöneticileri başlat
        self.config = ConfigManager()
        self.logger = Logger()
        self.lang = LanguageManager()  # Dil yöneticisini ekle
        self.trading_engine = None
        
        # Program ikonunu ayarla
        icon_path = self.config.ensure_resources()
        if icon_path and os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
                
        # UI bileşenleri
        self.tabs = None
        self.trades_table = None
        self.history_table = None
        self.log_text = None
        self.status_label = None
        self.balance_label = None
        self.profit_label = None
        
        # UI kurulumu
        self.setup_ui()
        
        # Kaydedilmiş ayarları yükle
        self.load_saved_settings()
                
        # UI güncelleme timer'ı
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(1000)  # Her saniye güncelle
        
        # Dil değişikliği sinyalini bağla
        self.language_changed.connect(self.update_ui_texts)
        
    def load_saved_settings(self):
        """Kaydedilmiş ayarları UI'a yükle"""
        try:
            # API bilgilerini yükle
            self.api_key_input.setText(self.config.get_value('api_key', ''))
            self.api_secret_input.setText(self.config.get_value('api_secret', ''))
            
            # Trading ayarlarını yükle
            self.timeframe_combo.setCurrentText(self.config.get_value('timeframe', '15m'))
            self.stop_loss_input.setValue(self.config.get_value('stop_loss', 3.0))
            self.take_profit_input.setValue(self.config.get_value('take_profit', 2.0))
            self.usdt_input.setValue(self.config.get_value('max_usdt', 10.0))
            self.max_positions_input.setValue(self.config.get_value('max_positions', 5))
            self.min_score_input.setValue(self.config.get_value('min_score', 75))
            
        except Exception as e:
            logging.error(f"Ayarları yükleme hatası: {str(e)}")

    def setup_ui(self):
        """Ana pencere arayüzünü oluştur"""
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1200, 800)

        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Üst bilgi paneli
        main_layout.addWidget(self.create_info_panel())

        # Ana tab widget
        self.tabs = QTabWidget()
        
        # Tab'ları ekle
        self.setup_settings_tab()
        self.setup_trading_tab()
        self.setup_history_tab()
        self.setup_analysis_tab()
        
        main_layout.addWidget(self.tabs)

        # Alt durum çubuğu
        self.setup_status_bar()

        # Stil ayarları
        self.apply_styles()
        
        # İlk UI metinlerini ayarla
        self.update_ui_texts()

    def create_info_panel(self) -> QFrame:
        """Üst bilgi panelini oluştur"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame { 
                background-color: #2d2d2d; 
                border-radius: 4px; 
                padding: 5px;
                max-height: 50px;
            }
        """)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(5, 2, 5, 2)

        # Sol taraf - Boş bırakıyoruz veya başka bilgi eklenebilir
        left_layout = QHBoxLayout()
        app_label = QLabel(APP_NAME)
        app_label.setStyleSheet("color: #00aa00; font-weight: bold;")
        left_layout.addWidget(app_label)
        layout.addLayout(left_layout)
        
        # Orta - Boşluk
        layout.addStretch()
        
        # Sağ taraf - Dil seçici
        right_layout = QHBoxLayout()
        right_layout.setSpacing(15)
        
        # Dil seçici
        lang_label = QLabel("Language:")
        lang_label.setStyleSheet("color: white;")
        right_layout.addWidget(lang_label)
        
        self.language_selector = QComboBox()
        self.language_selector.setFixedWidth(120)
        self.language_selector.setStyleSheet("""
            QComboBox {
                background-color: #363636;
                color: white;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 3px 5px;
                min-height: 20px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 5px;
            }
        """)
        
        # Dilleri ekle
        for code, name in self.lang.languages.items():
            self.language_selector.addItem(name, code)
        
        # Mevcut dili seç
        current_index = self.language_selector.findData(self.lang.current_language)
        if current_index >= 0:
            self.language_selector.setCurrentIndex(current_index)
        
        # Dil değişikliği olayını bağla
        self.language_selector.currentIndexChanged.connect(self.on_language_changed)
        right_layout.addWidget(self.language_selector)
        
        # Developer info
        developer = QLabel('<a href="#">İbrahim Kalaycı</a>')
        developer.setStyleSheet("color: #0066cc;")
        developer.setOpenExternalLinks(True)
        right_layout.addWidget(developer)
        
        layout.addLayout(right_layout)
        
        return panel
    
    def on_language_changed(self, index):
        """Dil değiştirildiğinde çağrılır"""
        lang_code = self.language_selector.itemData(index)
        if self.lang.set_language(lang_code):
            self.language_changed.emit()
            logging.info(f"{self.lang.__('language_changed')}: {self.lang.languages[lang_code]}")
    
    def update_ui_texts(self):
        """Tüm UI metinlerini güncelle"""
        # Pencere başlığı
        self.setWindowTitle(APP_NAME)
        
        # Tab başlıkları
        self.tabs.setTabText(0, self.lang.__('settings'))
        self.tabs.setTabText(1, self.lang.__('active_trades'))
        self.tabs.setTabText(2, self.lang.__('trades_history'))
        self.tabs.setTabText(3, self.lang.__('statistics'))
        
        # Butonlar
        self.start_button.setText(self.lang.__('start'))
        self.stop_button.setText(self.lang.__('stop'))
        
        # Ayarlar sekmesi etiketleri
        if hasattr(self, 'api_key_label'):
            self.api_key_label.setText(self.lang.__('api_key') + ":")
        if hasattr(self, 'api_secret_label'):
            self.api_secret_label.setText(self.lang.__('api_secret') + ":")
        if hasattr(self, 'timeframe_label'):
            self.timeframe_label.setText("Timeframe:")
        if hasattr(self, 'stop_loss_label'):
            self.stop_loss_label.setText("Stop Loss (%):")
        if hasattr(self, 'take_profit_label'):
            self.take_profit_label.setText("Take Profit (%):")
        if hasattr(self, 'usdt_label'):
            self.usdt_label.setText(self.lang.__('max_usdt') + ":")
        if hasattr(self, 'max_positions_label'):
            self.max_positions_label.setText(self.lang.__('max_positions') + ":")
        if hasattr(self, 'min_score_label'):
            self.min_score_label.setText(self.lang.__('min_score') + ":")
        if hasattr(self, 'excluded_coins_label'):
            self.excluded_coins_label.setText(self.lang.__('excluded_coins') + ":")
        if hasattr(self, 'ui_settings_label'):
            self.ui_settings_label.setText(self.lang.__('ui_settings'))
        if hasattr(self, 'live_analysis_checkbox'):
            self.live_analysis_checkbox.setText(self.lang.__('live_analysis_results'))
        if hasattr(self, 'update_interval_label'):
            self.update_interval_label.setText(self.lang.__('update_interval') + ":")
        if hasattr(self, 'reset_excluded_button'):
            self.reset_excluded_button.setText(self.lang.__('reset_to_default'))
        if hasattr(self, 'save_excluded_button'):
            self.save_excluded_button.setText(self.lang.__('save'))
        if hasattr(self, 'score_info_button'):
            from ui.tooltip import get_score_tooltip_text
            self.score_info_button.setToolTip(get_score_tooltip_text(self.lang))
            self.score_info_button.setToolTipDuration(15000)
        
        # Cüzdan bilgileri
        if hasattr(self, 'balance_label'):
            balance_text = self.balance_label.text()
            if ":" in balance_text:
                value = balance_text.split(":")[1].strip()
                self.balance_label.setText(f"{self.lang.__('usdt_balance')}: {value}")
        
        if hasattr(self, 'profit_label'):
            profit_text = self.profit_label.text()
            if ":" in profit_text:
                value = profit_text.split(":")[1].strip()
                self.profit_label.setText(f"{self.lang.__('total_profit')}: {value}")
        
        # Tablo başlıkları
        self.update_table_headers()
        
        # Durum çubuğu
        if self.trading_engine and self.trading_engine.is_running:
            self.status_label.setText(self.lang.__('trading_active'))
        else:
            self.status_label.setText(self.lang.__('ready'))
        
        # Tarama bilgileri
        if hasattr(self, 'scan_count_label'):
            text = self.scan_count_label.text()
            if "/" in text:
                numbers = text.split(":")[-1].strip()
                self.scan_count_label.setText(f"{self.lang.__('scanned_coins')}: {numbers}")
        
        if hasattr(self, 'last_scan_label'):
            text = self.last_scan_label.text()
            if ":" in text:
                time = text.split(":")[-3:]
                time_str = ":".join(time).strip()
                self.last_scan_label.setText(f"{self.lang.__('last_scan')}: {time_str}")
    
    def update_table_headers(self):
        """Tablo başlıklarını güncelle"""
        # İşlemler tablosu
        if self.trades_table:
            self.trades_table.setHorizontalHeaderLabels([
                self.lang.__('symbol'),
                self.lang.__('entry_price'),
                self.lang.__('current_price'),
                self.lang.__('amount'),
                self.lang.__('profit_loss'),
                "Stop Loss",
                "Take Profit"
            ])
        
        # Geçmiş tablosu
        if self.history_table:
            self.history_table.setHorizontalHeaderLabels([
                self.lang.__('date'),
                self.lang.__('symbol'),
                self.lang.__('type'),
                self.lang.__('price'),
                self.lang.__('amount'),
                self.lang.__('total'),
                self.lang.__('profit_loss'),
                self.lang.__('status')
            ])
        
        # Analiz tablosu
        if hasattr(self, 'analysis_table') and self.analysis_table:
            self.analysis_table.setHorizontalHeaderLabels([
                self.lang.__('coin'),
                self.lang.__('price'),
                self.lang.__('change_24h'),
                "RSI",
                self.lang.__('volume') + " (USDT)",
                self.lang.__('score'),
                self.lang.__('signal'),
                self.lang.__('last_update')
            ])

    def setup_settings_tab(self):
        """Ayarlar sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # API Ayarları
        api_frame = QFrame()
        api_layout = QGridLayout(api_frame)
        
        self.api_key_label = QLabel(self.lang.__('api_key') + ":")
        api_layout.addWidget(self.api_key_label, 0, 0)
        self.api_key_input = QLineEdit()
        api_layout.addWidget(self.api_key_input, 0, 1, 1, 3)
        
        self.api_secret_label = QLabel(self.lang.__('api_secret') + ":")
        api_layout.addWidget(self.api_secret_label, 1, 0)
        self.api_secret_input = QLineEdit()
        self.api_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addWidget(self.api_secret_input, 1, 1, 1, 3)
        
        layout.addWidget(api_frame)
        
        # Trading Ayarları
        trading_frame = QFrame()
        trading_layout = QGridLayout(trading_frame)
        
        # İlk satır
        self.timeframe_label = QLabel("Timeframe:")
        trading_layout.addWidget(self.timeframe_label, 0, 0)
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(['1m', '5m', '15m', '30m', '1h', '4h'])
        self.timeframe_combo.setCurrentText('15m')
        trading_layout.addWidget(self.timeframe_combo, 0, 1)
        
        self.stop_loss_label = QLabel("Stop Loss (%):")
        trading_layout.addWidget(self.stop_loss_label, 0, 2)
        self.stop_loss_input = QDoubleSpinBox()
        self.stop_loss_input.setRange(0.1, 10.0)
        self.stop_loss_input.setValue(3.0)
        trading_layout.addWidget(self.stop_loss_input, 0, 3)
        
        # İkinci satır
        self.take_profit_label = QLabel("Take Profit (%):")
        trading_layout.addWidget(self.take_profit_label, 1, 0)
        self.take_profit_input = QDoubleSpinBox()
        self.take_profit_input.setRange(0.1, 20.0)
        self.take_profit_input.setValue(2.0)
        trading_layout.addWidget(self.take_profit_input, 1, 1)
        
        self.usdt_label = QLabel(self.lang.__('max_usdt') + ":")
        trading_layout.addWidget(self.usdt_label, 1, 2)
        self.usdt_input = QDoubleSpinBox()
        self.usdt_input.setRange(10.0, 1000.0)
        self.usdt_input.setValue(10.0)
        trading_layout.addWidget(self.usdt_input, 1, 3)
        
        # Üçüncü satır
        self.max_positions_label = QLabel(self.lang.__('max_positions') + ":")
        trading_layout.addWidget(self.max_positions_label, 2, 0)
        self.max_positions_input = QSpinBox()
        self.max_positions_input.setRange(1, 100)
        self.max_positions_input.setValue(3)
        trading_layout.addWidget(self.max_positions_input, 2, 1)

        # Minimum Skor label, SpinBox ve ? butonu aynı satırda
        self.min_score_label = QLabel(self.lang.__('min_score') + ":")
        trading_layout.addWidget(self.min_score_label, 2, 2)
        self.min_score_input = QSpinBox()
        self.min_score_input.setRange(50, 100)
        self.min_score_input.setValue(65)
        self.min_score_input.setFixedWidth(75)
        trading_layout.addWidget(self.min_score_input, 2, 3)
        self.score_info_button = QPushButton("?")
        self.score_info_button.setFixedWidth(22)
        self.score_info_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.score_info_button.setStyleSheet("""
            QPushButton {
                background-color: #363636;
                color: #cccccc;
                border: 1px solid #444444;
                border-radius: 11px;
                font-weight: bold;
                font-size: 14px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
        self.score_info_button.setToolTip("Kısa test metni")
        self.score_info_button.setToolTipDuration(10000)
        trading_layout.addWidget(self.score_info_button, 2, 4)
        
        layout.addWidget(trading_frame)
        
        # Yasaklı Coinler Bölümü
        excluded_frame = QFrame()
        excluded_layout = QVBoxLayout(excluded_frame)
        excluded_layout.setContentsMargins(5, 5, 5, 5)
        
        self.excluded_coins_label = QLabel(self.lang.__('excluded_coins') + ":")
        excluded_layout.addWidget(self.excluded_coins_label)
        self.excluded_coins_text = QTextEdit()
        self.excluded_coins_text.setMaximumHeight(150)
        self.excluded_coins_text.setPlaceholderText("Her satıra bir coin yazın\nÖrnek:\nBTC/USDT\nETH/USDT")
        
        # Mevcut yasaklı coinleri yükle
        current_excluded = self.config.get_value('excluded_coins', [])
        self.excluded_coins_text.setText("\n".join(current_excluded))
        
        # Butonlar
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5) 
        
        self.reset_excluded_button = QPushButton(self.lang.__('reset_to_default'))
        self.reset_excluded_button.setFixedSize(120, 30)
        self.reset_excluded_button.clicked.connect(self.reset_excluded_coins)
        
        self.save_excluded_button = QPushButton(self.lang.__('save'))
        self.save_excluded_button.setFixedSize(120, 30)
        self.save_excluded_button.clicked.connect(self.save_excluded_coins)
        
        button_layout.addWidget(self.reset_excluded_button)
        button_layout.addWidget(self.save_excluded_button)
        
        excluded_layout.addWidget(self.excluded_coins_text)
        excluded_layout.addLayout(button_layout)
        layout.addWidget(excluded_frame)
                
        # UI Ayarları bölümü
        ui_frame = QFrame()
        ui_layout = QVBoxLayout(ui_frame)
        self.ui_settings_label = QLabel(self.lang.__('ui_settings'))
        ui_layout.addWidget(self.ui_settings_label)
        
        # Analiz tablosu için seçenekler
        analysis_panel = QHBoxLayout()
        self.live_analysis_checkbox = QCheckBox(self.lang.__('live_analysis_results'))
        self.live_analysis_checkbox.setChecked(False)  # Varsayılan olarak kapalı
        self.live_analysis_checkbox.setToolTip("Analiz sonuçlarını anlık göster (Performansı etkileyebilir)")
        analysis_panel.addWidget(self.live_analysis_checkbox)
        
        # Güncelleme sıklığı
        self.update_interval_label = QLabel(self.lang.__('update_interval') + ":")
        analysis_panel.addWidget(self.update_interval_label)
        self.update_interval_combo = QComboBox()
        self.update_interval_combo.addItems(['Every Scan', '1 per 5 scan', '1 per 10 scan'])
        self.update_interval_combo.setEnabled(False)  # Checkbox işaretli değilse devre dışı
        analysis_panel.addWidget(self.update_interval_combo)
        
        # Checkbox değişimini dinle
        self.live_analysis_checkbox.stateChanged.connect(
            lambda: self.update_interval_combo.setEnabled(self.live_analysis_checkbox.isChecked())
        )
        
        ui_layout.addLayout(analysis_panel)
        layout.addWidget(ui_frame)        
        layout.addStretch()
        
        # Tab'a ekle
        self.tabs.addTab(tab, self.lang.__('settings'))
        
        # Alt buton paneli
        bottom_panel = QFrame()
        bottom_panel.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-top: 1px solid #3d3d3d;
                padding: 10px;
            }
        """)
        bottom_layout = QHBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(10, 5, 10, 5)

        # Başlat/Durdur butonları
        self.start_button = QPushButton(self.lang.__('start'))
        self.start_button.clicked.connect(self.start_trading)
        self.start_button.setFixedSize(150, 35)

        self.stop_button = QPushButton(self.lang.__('stop'))
        self.stop_button.clicked.connect(self.stop_trading)
        self.stop_button.setEnabled(False)
        self.stop_button.setFixedSize(150, 35)

        bottom_layout.addStretch()
        bottom_layout.addWidget(self.start_button)
        bottom_layout.addWidget(self.stop_button)
        bottom_layout.addStretch()

        # Ana layout'a ekle
        layout.addWidget(bottom_panel)
        
    def save_excluded_coins(self):
        """Yasaklı coin listesini kaydet"""
        coins = [
            coin.strip() 
            for coin in self.excluded_coins_text.toPlainText().split("\n")
            if coin.strip()
        ]
        if self.config.update_excluded_coins(coins):
            self.log_text.append(f"[INFO] {self.lang.__('excluded_coins_updated')}")
        else:
            self.log_text.append(f"[ERROR] {self.lang.__('excluded_coins_update_error')}")

    def reset_excluded_coins(self):
        """Yasaklı coin listesini varsayılana döndür"""
        default_excluded = self.config.default_config['excluded_coins']
        self.excluded_coins_text.setText("\n".join(default_excluded))
        self.save_excluded_coins()

    def setup_trading_tab(self):
        """İşlemler sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # İşlem tablosu
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(7)
        self.trades_table.setHorizontalHeaderLabels([
            self.lang.__('symbol'),
            self.lang.__('entry_price'),
            self.lang.__('current_price'),
            self.lang.__('amount'),
            self.lang.__('profit_loss'),
            "Stop Loss",
            "Take Profit"
        ])
        header = self.trades_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.trades_table)
        
        # Log alanı
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #3d3d3d;
                font-family: Consolas, monospace;
            }
        """)

        # Logger'ı ayarla
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # Mevcut handler'ları temizle
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Yeni handler ekle
        log_handler = QTextEditLogger(self.log_text)
        log_handler.setFormatter(
            logging.Formatter(
                '[%(asctime)s] [%(levelname)s] %(message)s',
                datefmt='%H:%M:%S'
            )
        )
        logger.addHandler(log_handler)

        # Log frame'i layout'a ekle
        log_frame = QFrame()
        log_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                margin-top: 5px;
            }
        """)
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(5, 5, 5, 5)
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_frame)
        
        # Cüzdan bilgisi
        wallet_frame = QFrame()
        wallet_layout = QHBoxLayout(wallet_frame)
        
        self.balance_label = QLabel(f"{self.lang.__('usdt_balance')}: 0.00")
        self.balance_label.setStyleSheet("color: #44ff44;")
        wallet_layout.addWidget(self.balance_label)
        
        self.profit_label = QLabel(f"{self.lang.__('total_profit')}: 0.00 USDT")
        wallet_layout.addWidget(self.profit_label)
        
        layout.addWidget(wallet_frame)
        
        # Tab'a ekle
        self.tabs.addTab(tab, self.lang.__('active_trades'))

    def setup_history_tab(self):
        """Geçmiş sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            self.lang.__('date'),
            self.lang.__('symbol'),
            self.lang.__('type'),
            self.lang.__('price'),
            self.lang.__('amount'),
            self.lang.__('total'),
            self.lang.__('profit_loss'),
            self.lang.__('status')
        ])
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.history_table)
        
        # Tab'a ekle
        self.tabs.addTab(tab, self.lang.__('trades_history'))

    def setup_status_bar(self):
        """Alt durum çubuğu"""
        status_bar = self.statusBar()
        
        self.status_label = QLabel(self.lang.__('ready'))
        status_bar.addWidget(self.status_label)
        
        self.trades_label = QLabel(f"{self.lang.__('trades')}: 0/0")
        status_bar.addPermanentWidget(self.trades_label)

    def start_trading(self):
        """Trading'i başlat"""
        try:
            if not self.api_key_input.text() or not self.api_secret_input.text():
                self.status_label.setText(self.lang.__('api_credentials_required'))
                return

            # Ayarları kaydet
            config = {
                'api_key': self.api_key_input.text(),
                'api_secret': self.api_secret_input.text(),
                'timeframe': self.timeframe_combo.currentText(),
                'stop_loss': self.stop_loss_input.value(),
                'take_profit': self.take_profit_input.value(),
                'max_usdt': self.usdt_input.value(),
                'max_positions': self.max_positions_input.value(),
                'min_score': self.min_score_input.value()
            }

            # Ayarları kaydet
            self.config.save_config(config)

            # Trading engine'i başlat
            self.trading_engine = TradingEngine(self.config.config)
            self.trading_engine.scan_callback = self.update_analysis_table
            self.trading_engine.start()

            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText(self.lang.__('trading_started'))

        except Exception as e:
            self.log_to_ui(f"[ERROR] {self.lang.__('trading_start_error')}: {str(e)}")
            
    def log_to_ui(self, message: str):
        """Trading Engine'den gelen logları QTextEdit'e ekle"""
        self.log_text.append(message)

    def stop_trading(self):
        """Trading'i durdur"""
        try:
            # Butonları devre dışı bırak
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.status_label.setText(self.lang.__('trading_stopping'))
            
            if self.trading_engine:
                # Açık pozisyonları kontrol et
                if self.trading_engine.active_trades:
                    reply = QMessageBox.question(
                        self, 
                        self.lang.__('open_positions'),
                        self.lang.__('close_positions_question'),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        logging.info(self.lang.__('closing_positions'))
                        
                        # Pozisyonları kapatma işlemini başlat
                        if self.trading_engine.start_closing_positions():
                            logging.info(self.lang.__('all_positions_closed'))
                        else:
                            logging.error(self.lang.__('some_positions_not_closed'))
                            
                # Trading engine'i durdur
                self.trading_engine.stop()
                self.trading_engine = None
                self.trades_table.setRowCount(0)
                
                logging.info(self.lang.__('trading_stopped'))
                
        except Exception as e:
            logging.error(f"{self.lang.__('trading_stop_error')}: {str(e)}")
            
        finally:
            # Her durumda butonları düzelt
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText(self.lang.__('trading_stopped'))

    def update_ui(self):
        """UI güncellemesi yap"""
        if self.trading_engine and self.trading_engine.is_running:
            try:
                # Exchange null kontrolü
                if not self.trading_engine.exchange:
                    return
                    
                # Cüzdan bilgisini güncelle
                try:
                    balance = self.trading_engine.exchange.fetch_balance()
                    if balance and 'USDT' in balance:
                        usdt_balance = balance['USDT'].get('free', 0)
                        self.balance_label.setText(f"{self.lang.__('usdt_balance')}: {usdt_balance:.2f}")
                except Exception as e:
                    logging.error(f"{self.lang.__('balance_update_error')}: {str(e)}")
                
                # İstatistikleri güncelle
                try:
                    total_profit = self.trading_engine.stats.total_profit_usdt
                    self.profit_label.setText(f"{self.lang.__('total_profit')}: {total_profit:+.2f} USDT")
                except Exception as e:
                    logging.error(f"{self.lang.__('profit_update_error')}: {str(e)}")
                
                # İşlem sayılarını güncelle
                try:
                    active_count = len(self.trading_engine.active_trades)
                    total_trades = self.trading_engine.stats.total_trades
                    self.trades_label.setText(f"{self.lang.__('trades')}: {active_count}/{total_trades}")
                except Exception as e:
                    logging.error(f"{self.lang.__('trade_count_update_error')}: {str(e)}")
                
                # Aktif işlemleri güncelle
                try:
                    self.update_trades_table()
                except Exception as e:
                    logging.error(f"Tablo güncelleme hatası: {str(e)}")
                    
                try:
                    self.update_history_table()
                except Exception as e:
                    logging.error(f"Geçmiş tablosu güncelleme hatası: {str(e)}")
                                        
            except Exception as e:
                logging.error(f"UI güncelleme hatası: {str(e)}")
                
    def update_history_table(self):
        """İşlem geçmişi tablosunu güncelle"""
        if not self.trading_engine:
            return
            
        # Trading stats'tan geçmiş verileri al
        history = self.trading_engine.stats.trade_history
        self.history_table.setRowCount(len(history))
        
        for i, trade in enumerate(history):
            try:
                # Tarih
                date_item = QTableWidgetItem(trade.get('timestamp', '').strftime('%Y-%m-%d %H:%M:%S'))
                self.history_table.setItem(i, 0, date_item)
                
                # Sembol
                self.history_table.setItem(i, 1, QTableWidgetItem(trade.get('symbol', '')))
                
                # İşlem türü
                type_item = QTableWidgetItem(self.lang.__('buy') if trade.get('type') == 'buy' else self.lang.__('sell'))
                type_item.setForeground(QColor("#00ff00" if trade.get('type') == 'buy' else "#ff4444"))
                self.history_table.setItem(i, 2, type_item)
                
                # Fiyat
                self.history_table.setItem(i, 3, QTableWidgetItem(f"{trade.get('price', 0):.8f}"))
                
                # Miktar
                self.history_table.setItem(i, 4, QTableWidgetItem(f"{trade.get('amount', 0):.8f}"))
                
                # Toplam USDT
                total_usdt = trade.get('total_usdt', 0)
                self.history_table.setItem(i, 5, QTableWidgetItem(f"{total_usdt:.2f}"))
                
                # Kâr/Zarar
                if 'profit' in trade:
                    profit_text = f"{trade['profit']:.2f} ({trade.get('profit_percentage', 0):.2f}%)"
                    profit_item = QTableWidgetItem(profit_text)
                    profit_item.setForeground(QColor("#00ff00" if trade['profit'] > 0 else "#ff4444"))
                    self.history_table.setItem(i, 6, profit_item)
                else:
                    self.history_table.setItem(i, 6, QTableWidgetItem("-"))
                
                # Durum
                status_text = trade.get('status', '')
                if status_text == 'open_position':
                    status_text = self.lang.__('open_position')
                elif status_text == 'TAKE-PROFIT':
                    status_text = self.lang.__('take_profit_reason')
                elif status_text == 'STOP-LOSS':
                    status_text = self.lang.__('stop_loss_reason')
                self.history_table.setItem(i, 7, QTableWidgetItem(status_text))
                
            except Exception as e:
                logging.error(f"{self.lang.__('history_table_update_error')}: {str(e)}")

    def update_trades_table(self):
        """İşlem tablosunu güncelle"""
        if not self.trading_engine:
            return
            
        try:
            # Dictionary'nin bir kopyasını al
            trades = dict(self.trading_engine.active_trades)
            self.trades_table.setRowCount(len(trades))
            
            for i, (symbol, trade) in enumerate(trades.items()):
                try:
                    current_price = float(self.trading_engine.exchange.fetch_ticker(symbol)['last'])
                    profit_percent = ((current_price - trade['entry_price']) / trade['entry_price']) * 100
                    
                    # Tablo satırını güncelle
                    self.trades_table.setItem(i, 0, QTableWidgetItem(symbol))
                    self.trades_table.setItem(i, 1, QTableWidgetItem(f"{trade['entry_price']:.8f}"))
                    self.trades_table.setItem(i, 2, QTableWidgetItem(f"{current_price:.8f}"))
                    self.trades_table.setItem(i, 3, QTableWidgetItem(f"{trade['amount']:.8f}"))
                    
                    profit_item = QTableWidgetItem(f"{profit_percent:+.2f}%")
                    profit_item.setForeground(QColor("#00ff00" if profit_percent > 0 else "#ff4444"))
                    self.trades_table.setItem(i, 4, profit_item)
                    
                    self.trades_table.setItem(i, 5, QTableWidgetItem(f"{trade['stop_loss']:.8f}"))
                    self.trades_table.setItem(i, 6, QTableWidgetItem(f"{trade['take_profit']:.8f}"))
                    
                except Exception as e:
                    logging.error(f"Tablo satır güncelleme hatası ({symbol}): {str(e)}")
                    
        except Exception as e:
            logging.error(f"Tablo güncelleme hatası: {str(e)}")

    def apply_styles(self):
        """Stil ayarları"""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: white;
            }
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                margin: 0px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #363636;
                color: white;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 5px;
                min-height: 25px;
            }
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
            QPushButton:disabled {
                background-color: #333333;
            }
            QTableWidget {
                background-color: #2d2d2d;
                border: 1px solid #444444;
                border-radius: 4px;
                gridline-color: #444444;
            }
            QTableWidget::item {
            padding: 8px;
            height: 30px;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: white;
                padding: 5px;
                border: 1px solid #444444;
                min-height: 35px;
            }
            QStatusBar {
                background-color: #2d2d2d;
                border-top: 1px solid #3d3d3d;
            }
            QStatusBar QLabel {
                padding: 3px 6px;
            }
            QTabWidget::pane { 
                border: 1px solid #3d3d3d;
            }
            QTabBar::tab { 
                background-color: #2d2d2d; 
                color: white;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected { 
                background-color: #3d3d3d;
            }
        """)

    def closeEvent(self, event):
        """Program kapatılırken"""
        try:
            
            if self.trading_engine:
                logging.info("Program kapatılıyor, trading durduruluyor...")
                self.trading_engine.stop()
                self.trading_engine = None
            
            # UI timer'ları durdur
            if hasattr(self, 'update_timer'):
                self.update_timer.stop()
                
            event.accept()
            
        except Exception as e:
            logging.error(f"Kapatma hatası: {str(e)}")
            event.accept()
        finally:
            # Python'ın temiz çıkış yapmasını sağla
            import sys
            sys.exit(0)
            
    def setup_analysis_tab(self):
        """Analiz sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Analiz sonuçları tablosu
        self.analysis_table = QTableWidget()
        self.analysis_table.setColumnCount(8)
        self.analysis_table.setHorizontalHeaderLabels([
            "Coin", "Fiyat", "24s Değişim", "RSI", 
            "Hacim (USDT)", "Skor", "Sinyal", "Son Güncelleme"
        ])
        
        header = self.analysis_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Sıralama özelliği ekle
        self.analysis_table.setSortingEnabled(True)
        
        layout.addWidget(self.analysis_table)
        
        # Tarama bilgisi
        info_frame = QFrame()
        info_layout = QHBoxLayout(info_frame)
        
        self.scan_count_label = QLabel("Taranan Coin: 0/0")
        info_layout.addWidget(self.scan_count_label)
        
        self.last_scan_label = QLabel("Son Tarama: -")
        info_layout.addWidget(self.last_scan_label, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addWidget(info_frame)
        
        # Tab'a ekle
        self.tabs.addTab(tab, "Analysis")
        
    def update_analysis_table(self, scan_results, scanned, total):
        """Analiz tablosunu güncelle"""
        try:
            self.analysis_table.setRowCount(len(scan_results))
            
            for i, result in enumerate(scan_results):
                # Coin
                self.analysis_table.setItem(i, 0, QTableWidgetItem(result['symbol']))
                
                # Fiyat
                self.analysis_table.setItem(i, 1, QTableWidgetItem(f"{result['price']:.8f}"))
                
                # 24s Değişim
                change_item = QTableWidgetItem(f"{result['change_24h']:+.2f}%")
                change_item.setForeground(QColor("#00ff00" if result['change_24h'] > 0 else "#ff4444"))
                self.analysis_table.setItem(i, 2, change_item)
                
                # RSI
                self.analysis_table.setItem(i, 3, QTableWidgetItem(f"{result['rsi']:.1f}"))
                
                # Hacim
                self.analysis_table.setItem(i, 4, QTableWidgetItem(f"{result['volume']:,.0f}"))
                
                # Skor
                score_item = QTableWidgetItem(f"{result['score']:.1f}")
                if result['score'] >= 85:
                    score_item.setForeground(QColor("#00ff00"))
                elif result['score'] >= 70:
                    score_item.setForeground(QColor("#00dd00"))
                self.analysis_table.setItem(i, 5, score_item)
                
                # Sinyal
                signal_item = QTableWidgetItem(result['signal'])
                if "ALIM" in result['signal']:
                    signal_item.setForeground(QColor("#00ff00"))
                self.analysis_table.setItem(i, 6, signal_item)
                
                # Son Güncelleme
                self.analysis_table.setItem(i, 7, QTableWidgetItem(
                    result['timestamp'].strftime('%H:%M:%S')
                ))
                
            # İlerleme bilgisini güncelle
            self.scan_count_label.setText(f"Taranan Coin: {scanned}/{total}")
            self.last_scan_label.setText(f"Son Tarama: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            logging.error(f"Analiz tablosu güncelleme hatası: {str(e)}")

class QTextEditLogger(Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        try:
            # Doğrudan QTextEdit'e yazma işlemi
            if self.widget:
                # Timestamp ekle
                timestamp = datetime.now().strftime('%H:%M:%S')
                formatted_msg = f"[{timestamp}] {msg}"
                
                # Thread-safe mesaj ekleme
                from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
                QMetaObject.invokeMethod(
                    self.widget,
                    "append",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, formatted_msg)
                )

                # Otomatik scroll
                scrollbar = self.widget.verticalScrollBar()
                if scrollbar:
                    scrollbar.setValue(scrollbar.maximum())
                    
        except Exception as e:
            print(f"Log yazma hatası: {str(e)}")  # En azından konsola yazalım