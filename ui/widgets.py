from PyQt6.QtWidgets import (QTableWidget, QHeaderView, QFrame, 
                           QVBoxLayout, QLabel, QStatusBar, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
import logging
from typing import Dict, Any

class OptimizedTableWidget(QTableWidget):
    """
    Optimize edilmiş tablo widget'ı.
    Büyük veri setleri için performans iyileştirmeleri içerir.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_table()
        self.update_buffer = {}
        self.last_update = 0

    def setup_table(self):
        """Tablo özelliklerini ayarla"""
        # Performans optimizasyonları
        self.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.verticalHeader().setVisible(False)
        
        # Görsel ayarlar
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        # Stil ayarları
        self.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: white;
                gridline-color: #3d3d3d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #0066cc;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: white;
                padding: 5px;
                border: 1px solid #3d3d3d;
            }
        """)

    def batch_update(self, data: Dict[str, Any], throttle_ms: int = 100):
        """
        Tablo verilerini toplu güncelle.
        Güncelleme hızını kontrol eder (throttling).
        """
        import time
        current_time = time.time() * 1000  # milisaniye

        # Throttling kontrolü
        if current_time - self.last_update < throttle_ms:
            self.update_buffer.update(data)
            return

        self.setUpdatesEnabled(False)
        try:
            # Eğer buffer'da veri varsa onları da ekle
            all_updates = {**self.update_buffer, **data}
            self.update_buffer.clear()

            # Satır sayısını ayarla
            self.setRowCount(len(all_updates))

            # Verileri güncelle
            for row, (key, item_data) in enumerate(all_updates.items()):
                self._update_row(row, item_data)

        finally:
            self.setUpdatesEnabled(True)
            self.last_update = current_time

    def _update_row(self, row: int, data: Dict):
        """Tek bir satırı güncelle"""
        try:
            for col, value in enumerate(data.values()):
                item = self.item(row, col)
                if item is None:
                    from PyQt6.QtWidgets import QTableWidgetItem
                    item = QTableWidgetItem()
                    self.setItem(row, col, item)

                # Sayısal değerler için formatlama
                if isinstance(value, float):
                    if col in [1, 2]:  # Fiyat kolonları
                        formatted_value = f"{value:.8f}"
                    else:
                        formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)

                item.setText(formatted_value)

                # Renklendirme
                if 'change' in str(data.keys()).lower():
                    if value > 0:
                        item.setForeground(QColor("#00ff00"))
                    elif value < 0:
                        item.setForeground(QColor("#ff4444"))

        except Exception as e:
            logging.error(f"Satır güncelleme hatası: {str(e)}")

class StatusBar(QStatusBar):
    """
    Özelleştirilmiş durum çubuğu.
    Trading durumu ve metrikleri gösterir.
    """
    def __init__(self, parent=None, lang_manager=None):
        super().__init__(parent)
        self.lang = lang_manager
        
        # Profit label
        self.profit_label = QLabel()
        self.addWidget(self.profit_label)
        
        # Trades label
        self.trades_label = QLabel()
        self.addWidget(self.trades_label)

    def update_metrics(self, metrics: Dict):
        """Update trading metrics"""
        try:
            # Update profit/loss
            profit = metrics.get('total_profit', 0)
            profit_color = "#00ff00" if profit >= 0 else "#ff4444"
            self.profit_label.setStyleSheet(f"color: {profit_color};")
            self.profit_label.setText(f"{self.lang.__('total_profit')}: {profit:+.2f} USDT")

            # Update trade counts
            active = len(metrics.get('active_trades', {}))
            total = metrics.get('total_trades', 0)
            self.trades_label.setText(f"{self.lang.__('trades')}: {active}/{total}")

        except Exception as e:
            logging.error(f"{self.lang.__('ui_update_error')}: {str(e)}")

class MetricsPanel(QFrame):
    """Metrics panel widget"""
    def __init__(self, parent=None, lang_manager=None):
        super().__init__(parent)
        self.lang = lang_manager
        self.labels = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup metrics panel UI"""
        layout = QGridLayout(self)
        layout.setSpacing(10)
        
        # Create metric labels
        metrics = [
            'total_trades',
            'winning_trades',
            'losing_trades',
            'total_profit',
            'win_rate',
            'avg_profit',
            'max_drawdown'
        ]
        
        for i, metric in enumerate(metrics):
            label = QLabel()
            self.labels[metric] = label
            layout.addWidget(label, i // 2, i % 2)

    def update_metrics(self, metrics: Dict):
        """Update metrics"""
        try:
            # Update each metric and colorize
            self.labels['total_trades'].setText(f"{self.lang.__('total_trades')}: {metrics.get('total_trades', 0)}")
            self.labels['winning_trades'].setText(f"{self.lang.__('winning_trades')}: {metrics.get('winning_trades', 0)}")
            self.labels['losing_trades'].setText(f"{self.lang.__('losing_trades')}: {metrics.get('losing_trades', 0)}")
            
            # Total profit
            profit = metrics.get('total_profit', 0)
            profit_label = self.labels['total_profit']
            profit_label.setText(f"{self.lang.__('total_profit')}: {profit:+.2f} USDT")
            profit_label.setStyleSheet(f"color: {'#00ff00' if profit >= 0 else '#ff4444'}")
            
            # Win rate
            win_rate = metrics.get('win_rate', 0)
            self.labels['win_rate'].setText(f"{self.lang.__('win_rate')}: {win_rate:.1f}%")
            
            # Average profit
            avg_profit = metrics.get('avg_profit', 0)
            avg_label = self.labels['avg_profit']
            avg_label.setText(f"{self.lang.__('avg_profit')}: {avg_profit:+.2f} USDT")
            avg_label.setStyleSheet(f"color: {'#00ff00' if avg_profit >= 0 else '#ff4444'}")
            
            # Drawdown
            drawdown = metrics.get('max_drawdown', 0)
            self.labels['max_drawdown'].setText(f"{self.lang.__('max_drawdown')}: {drawdown:.2f}%")
            
        except Exception as e:
            logging.error(f"{self.lang.__('ui_update_error')}: {str(e)}")

class TradeHistoryWidget(OptimizedTableWidget):
    """
    İşlem geçmişi için özelleştirilmiş tablo widget'ı.
    İşlem filtrelerini ve özet istatistikleri içerir.
    """
    def __init__(self):
        super().__init__()
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels([
            "Tarih", "Sembol", "İşlem", "Fiyat", 
            "Miktar", "Toplam", "Kâr/Zarar", "Durum"
        ])
        
    def update_history(self, trades: list):
        """İşlem geçmişini güncelle"""
        self.setRowCount(len(trades))
        for i, trade in enumerate(trades):
            try:
                # Tarih
                self.setItem(i, 0, self._create_item(trade.get('timestamp', '')))
                
                # Sembol
                self.setItem(i, 1, self._create_item(trade.get('symbol', '')))
                
                # İşlem türü (Alış/Satış)
                trade_type = "ALIŞ" if trade.get('type') == 'buy' else "SATIŞ"
                type_item = self._create_item(trade_type)
                type_item.setForeground(QColor("#00ff00" if trade_type == "ALIŞ" else "#ff4444"))
                self.setItem(i, 2, type_item)
                
                # Fiyat
                self.setItem(i, 3, self._create_item(f"{trade.get('price', 0):.8f}"))
                
                # Miktar
                self.setItem(i, 4, self._create_item(f"{trade.get('amount', 0):.8f}"))
                
                # Toplam USDT
                self.setItem(i, 5, self._create_item(f"{trade.get('total_usdt', 0):.2f}"))
                
                # Kâr/Zarar
                profit = trade.get('profit', 0)
                profit_item = self._create_item(f"{profit:+.2f}")
                profit_item.setForeground(QColor("#00ff00" if profit >= 0 else "#ff4444"))
                self.setItem(i, 6, profit_item)
                
                # Durum
                self.setItem(i, 7, self._create_item(trade.get('status', '')))
                
            except Exception as e:
                logging.error(f"İşlem geçmişi satır güncelleme hatası: {str(e)}")
                
    def _create_item(self, text):
        """TableWidgetItem oluştur"""
        from PyQt6.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item