import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
import time
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import binance.client
from binance.client import Client
import configparser
import os
import ta  # Teknik analiz için ta-lib

class BinanceTradingBot:
    def __init__(self, root):
        self.root = root
        self.root.title("Binance Çoklu Coin Analiz ve Alım Satım Botu")
        self.root.geometry("1400x900")
        self.root.resizable(True, True)
        
        # Bot durumu
        self.running = False
        self.client = None
        self.analysis_threads = {}
        
        # Kullanıcı bilgileri ve ayarlar
        self.api_key = ""
        self.api_secret = ""
        self.trade_interval = "1h"
        self.strategy = "MULTI"  # Çoklu strateji
        self.stop_loss = 2.0  # Varsayılan stop loss yüzdesi
        self.take_profit = 3.0  # Varsayılan take profit yüzdesi
        
        # İzlenen coinler
        self.watch_list = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]
        self.active_coins = {}  # İzlenen aktif coinler ve miktarları
        self.coin_data = {}  # Her coin için analiz verileri
        self.signals = {}  # Her coin için sinyal bilgileri
        
        # Config dosyası işlemleri
        self.config = configparser.ConfigParser()
        self.load_config()
        
        # Ana frame oluşturma
        self.create_widgets()
        
        # Günlük tutma
        self.log("Bot başlatıldı")
    
    def create_widgets(self):
        # Ana notebook oluşturma
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Ana sekmeler
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.tab_coin_analysis = ttk.Frame(self.notebook)
        self.tab_settings = ttk.Frame(self.notebook)
        self.tab_logs = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_dashboard, text="Kontrol Paneli")
        self.notebook.add(self.tab_coin_analysis, text="Coin Analizleri")
        self.notebook.add(self.tab_settings, text="Ayarlar")
        self.notebook.add(self.tab_logs, text="Günlük")
        
        # Dashboard içeriği
        self.create_dashboard()
        
        # Coin Analiz sekmesi
        self.create_coin_analysis_tab()
        
        # Ayarlar içeriği
        self.create_settings()
        
        # Logs içeriği
        self.create_logs()
    
    def create_dashboard(self):
        # Sol Panel - Kontrol ve Durum
        left_frame = ttk.LabelFrame(self.tab_dashboard, text="Kontrol Paneli")
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Bağlantı durumu
        ttk.Label(left_frame, text="Bağlantı Durumu:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.lbl_status = ttk.Label(left_frame, text="Bağlı Değil", foreground="red")
        self.lbl_status.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Bağlan/Bağlantıyı Kes butonu
        self.btn_connect = ttk.Button(left_frame, text="Bağlan", command=self.toggle_connection)
        self.btn_connect.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Zaman aralığı
        ttk.Label(left_frame, text="Zaman Aralığı:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.cmb_interval = ttk.Combobox(left_frame, values=["5m", "15m", "30m", "1h", "4h", "1d"])
        self.cmb_interval.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.cmb_interval.set(self.trade_interval)
        
        # Bot başlat/durdur butonu
        self.btn_start_bot = ttk.Button(left_frame, text="Botu Başlat", command=self.toggle_bot, state="disabled")
        self.btn_start_bot.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # İzlenen coinler listesi
        watch_list_frame = ttk.LabelFrame(left_frame, text="İzlenen Coinler")
        watch_list_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # İzlenen coinler listbox
        self.listbox_coins = tk.Listbox(watch_list_frame, height=10, selectmode=tk.MULTIPLE)
        self.listbox_coins.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # İzlenen coinleri doldur
        for coin in self.watch_list:
            self.listbox_coins.insert(tk.END, coin)
        
        # Coin ekle/çıkar butonları
        coin_buttons_frame = ttk.Frame(watch_list_frame)
        coin_buttons_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        self.entry_new_coin = ttk.Entry(coin_buttons_frame)
        self.entry_new_coin.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        ttk.Button(coin_buttons_frame, text="Ekle", command=self.add_coin).pack(side=tk.LEFT, padx=2)
        ttk.Button(coin_buttons_frame, text="Çıkar", command=self.remove_coin).pack(side=tk.LEFT, padx=2)
        
        # Cüzdan Bakiyesi gösterimi
        balance_frame = ttk.LabelFrame(left_frame, text="Cüzdan Bakiyesi")
        balance_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        ttk.Label(balance_frame, text="USDT:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.lbl_usdt_balance = ttk.Label(balance_frame, text="0.00")
        self.lbl_usdt_balance.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Sağ Panel - Sinyal Tablosu
        right_frame = ttk.LabelFrame(self.tab_dashboard, text="Coin Sinyal Tablosu")
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Sinyal tablosu
        columns = ("sembol", "fiyat", "değişim_24s", "sinyal", "sma", "rsi", "macd", "bollinger", "son_güncelleme")
        self.tree_signals = ttk.Treeview(right_frame, columns=columns, show="headings")
        
        self.tree_signals.heading("sembol", text="Sembol")
        self.tree_signals.heading("fiyat", text="Fiyat")
        self.tree_signals.heading("değişim_24s", text="24s Değişim")
        self.tree_signals.heading("sinyal", text="Genel Sinyal")
        self.tree_signals.heading("sma", text="SMA")
        self.tree_signals.heading("rsi", text="RSI")
        self.tree_signals.heading("macd", text="MACD")
        self.tree_signals.heading("bollinger", text="Bollinger")
        self.tree_signals.heading("son_güncelleme", text="Son Güncelleme")
        
        self.tree_signals.column("sembol", width=80)
        self.tree_signals.column("fiyat", width=100)
        self.tree_signals.column("değişim_24s", width=100)
        self.tree_signals.column("sinyal", width=100)
        self.tree_signals.column("sma", width=80)
        self.tree_signals.column("rsi", width=80)
        self.tree_signals.column("macd", width=80)
        self.tree_signals.column("bollinger", width=80)
        self.tree_signals.column("son_güncelleme", width=140)
        
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.tree_signals.yview)
        self.tree_signals.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_signals.pack(fill=tk.BOTH, expand=True)
        
        # İşlem Tablosu
        bottom_frame = ttk.LabelFrame(self.tab_dashboard, text="Son İşlemler")
        bottom_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        columns = ("tarih", "sembol", "işlem", "fiyat", "miktar", "toplam")
        self.tree_transactions = ttk.Treeview(bottom_frame, columns=columns, show="headings")
        
        self.tree_transactions.heading("tarih", text="Tarih")
        self.tree_transactions.heading("sembol", text="Sembol")
        self.tree_transactions.heading("işlem", text="İşlem")
        self.tree_transactions.heading("fiyat", text="Fiyat")
        self.tree_transactions.heading("miktar", text="Miktar")
        self.tree_transactions.heading("toplam", text="Toplam")
        
        self.tree_transactions.column("tarih", width=140)
        self.tree_transactions.column("sembol", width=80)
        self.tree_transactions.column("işlem", width=80)
        self.tree_transactions.column("fiyat", width=100)
        self.tree_transactions.column("miktar", width=100)
        self.tree_transactions.column("toplam", width=100)
        
        scrollbar = ttk.Scrollbar(bottom_frame, orient="vertical", command=self.tree_transactions.yview)
        self.tree_transactions.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_transactions.pack(fill=tk.BOTH, expand=True)
        
        # Grid ağırlıklarını ayarla
        self.tab_dashboard.grid_columnconfigure(0, weight=1)
        self.tab_dashboard.grid_columnconfigure(1, weight=3)
        self.tab_dashboard.grid_rowconfigure(0, weight=3)
        self.tab_dashboard.grid_rowconfigure(1, weight=1)
    
    def create_coin_analysis_tab(self):
        # Coin analiz sekmesi
        # Sol panel - Coin listesi
        left_frame = ttk.Frame(self.tab_coin_analysis)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        ttk.Label(left_frame, text="Coin Seçimi").pack(pady=5)
        
        self.listbox_analysis_coins = tk.Listbox(left_frame, height=20, width=15)
        self.listbox_analysis_coins.pack(fill=tk.Y, expand=True, pady=5)
        
        # Listeyi doldur
        for coin in self.watch_list:
            self.listbox_analysis_coins.insert(tk.END, coin)
        
        # Coin seçildiğinde analiz gösterme
        self.listbox_analysis_coins.bind('<<ListboxSelect>>', self.show_coin_analysis)
        
        # Sağ panel - Analiz gösterimi
        self.right_frame_analysis = ttk.Frame(self.tab_coin_analysis)
        self.right_frame_analysis.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Grafik başlığı
        self.lbl_coin_title = ttk.Label(self.right_frame_analysis, text="Coin seçiniz", font=("Arial", 14, "bold"))
        self.lbl_coin_title.pack(pady=10)
        
        # Grafik alanı
        self.fig_analysis, self.ax_analysis = plt.subplots(figsize=(10, 6))
        self.canvas_analysis = FigureCanvasTkAgg(self.fig_analysis, master=self.right_frame_analysis)
        self.canvas_widget_analysis = self.canvas_analysis.get_tk_widget()
        self.canvas_widget_analysis.pack(fill=tk.BOTH, expand=True)
        
        # Alt panel - Analiz detayları
        bottom_frame = ttk.LabelFrame(self.right_frame_analysis, text="Teknik Analiz Detayları")
        bottom_frame.pack(fill=tk.BOTH, expand=False, pady=10)
        
        # Teknik göstergeler detayı
        self.txt_analysis_details = scrolledtext.ScrolledText(bottom_frame, height=12, wrap=tk.WORD)
        self.txt_analysis_details.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_settings(self):
        # API Ayarları
        api_frame = ttk.LabelFrame(self.tab_settings, text="API Ayarları")
        api_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_api_key = ttk.Entry(api_frame, width=50)
        self.entry_api_key.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.entry_api_key.insert(0, self.api_key)
        
        ttk.Label(api_frame, text="API Secret:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_api_secret = ttk.Entry(api_frame, width=50, show="*")
        self.entry_api_secret.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.entry_api_secret.insert(0, self.api_secret)
        
        # İşlem Ayarları
        trade_frame = ttk.LabelFrame(self.tab_settings, text="İşlem Ayarları")
        trade_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        ttk.Label(trade_frame, text="Stop Loss (%):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_stop_loss = ttk.Entry(trade_frame)
        self.entry_stop_loss.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.entry_stop_loss.insert(0, str(self.stop_loss))
        
        ttk.Label(trade_frame, text="Take Profit (%):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_take_profit = ttk.Entry(trade_frame)
        self.entry_take_profit.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.entry_take_profit.insert(0, str(self.take_profit))
        
        # Strateji Ağırlıkları
        strategy_frame = ttk.LabelFrame(self.tab_settings, text="Strateji Ağırlıkları")
        strategy_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        ttk.Label(strategy_frame, text="SMA Ağırlığı (%):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_weight_sma = ttk.Entry(strategy_frame)
        self.entry_weight_sma.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.entry_weight_sma.insert(0, "25")
        
        ttk.Label(strategy_frame, text="RSI Ağırlığı (%):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_weight_rsi = ttk.Entry(strategy_frame)
        self.entry_weight_rsi.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.entry_weight_rsi.insert(0, "25")
        
        ttk.Label(strategy_frame, text="MACD Ağırlığı (%):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_weight_macd = ttk.Entry(strategy_frame)
        self.entry_weight_macd.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.entry_weight_macd.insert(0, "25")
        
        ttk.Label(strategy_frame, text="Bollinger Ağırlığı (%):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.entry_weight_bollinger = ttk.Entry(strategy_frame)
        self.entry_weight_bollinger.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.entry_weight_bollinger.insert(0, "25")
        
        # Strateji Parametreleri
        strategy_params_frame = ttk.LabelFrame(self.tab_settings, text="Strateji Parametreleri")
        strategy_params_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        ttk.Label(strategy_params_frame, text="SMA Kısa Dönem:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_sma_short = ttk.Entry(strategy_params_frame)
        self.entry_sma_short.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.entry_sma_short.insert(0, "9")
        
        ttk.Label(strategy_params_frame, text="SMA Uzun Dönem:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_sma_long = ttk.Entry(strategy_params_frame)
        self.entry_sma_long.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.entry_sma_long.insert(0, "20")
        
        ttk.Label(strategy_params_frame, text="RSI Dönem:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_rsi_period = ttk.Entry(strategy_params_frame)
        self.entry_rsi_period.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.entry_rsi_period.insert(0, "14")
        
        ttk.Label(strategy_params_frame, text="RSI Aşırı Satım:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.entry_rsi_oversold = ttk.Entry(strategy_params_frame)
        self.entry_rsi_oversold.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.entry_rsi_oversold.insert(0, "30")
        
        ttk.Label(strategy_params_frame, text="RSI Aşırı Alım:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.entry_rsi_overbought = ttk.Entry(strategy_params_frame)
        self.entry_rsi_overbought.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.entry_rsi_overbought.insert(0, "70")
        
        # Para yönetimi
        money_frame = ttk.LabelFrame(self.tab_settings, text="Para Yönetimi")
        money_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        ttk.Label(money_frame, text="İşlem Başına USDT Miktarı:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_trade_amount = ttk.Entry(money_frame)
        self.entry_trade_amount.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.entry_trade_amount.insert(0, "100")
        
        ttk.Label(money_frame, text="Maks. Eş Zamanlı İşlem:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_max_trades = ttk.Entry(money_frame)
        self.entry_max_trades.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.entry_max_trades.insert(0, "5")
        
        # Ayarları Kaydet butonu
        save_frame = ttk.Frame(self.tab_settings)
        save_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        self.btn_save = ttk.Button(save_frame, text="Ayarları Kaydet", command=self.save_settings)
        self.btn_save.pack(side=tk.RIGHT)
    
    def create_logs(self):
        # Günlük alanı
        self.txt_logs = scrolledtext.ScrolledText(self.tab_logs, wrap=tk.WORD)
        self.txt_logs.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Günlük temizleme butonu
        btn_clear_logs = ttk.Button(self.tab_logs, text="Günlüğü Temizle", command=self.clear_logs)
        btn_clear_logs.pack(side=tk.RIGHT, padx=10, pady=10)
    
    def log(self, message):
        """Günlük kaydı ekleme fonksiyonu"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # GUI'ye ekleme
        if hasattr(self, 'txt_logs'):
            self.txt_logs.insert(tk.END, log_message)
            self.txt_logs.see(tk.END)
        
        # Konsola yazdırma
        print(log_message, end="")
    
    def clear_logs(self):
        """Günlük kayıtlarını temizleme"""
        self.txt_logs.delete(1.0, tk.END)
        self.log("Günlük temizlendi")
    
    def add_coin(self):
        """Listeye yeni coin ekleme"""
        coin = self.entry_new_coin.get().strip().upper()
        if coin and coin not in self.watch_list:
            # Coin çifti kontrolü - USDT ile bitiyorsa ekle
            if not coin.endswith("USDT"):
                coin = coin + "USDT"
            
            self.watch_list.append(coin)
            self.listbox_coins.insert(tk.END, coin)
            self.listbox_analysis_coins.insert(tk.END, coin)
            self.entry_new_coin.delete(0, tk.END)
            self.log(f"{coin} izleme listesine eklendi")
            
            # Eğer bot çalışıyorsa, yeni coin için analiz thread'i başlat
            if self.running and self.client:
                self.start_coin_analysis(coin)
    
    def remove_coin(self):
        """Listeden seçili coini çıkarma"""
        selected = self.listbox_coins.curselection()
        if selected:
            for index in selected[::-1]:
                coin = self.listbox_coins.get(index)
                self.watch_list.remove(coin)
                self.listbox_coins.delete(index)
                
                # Analiz listesinden de kaldır
                for i in range(self.listbox_analysis_coins.size()):
                    if self.listbox_analysis_coins.get(i) == coin:
                        self.listbox_analysis_coins.delete(i)
                        break
                
                # Sinyal tablosundan kaldır
                for item in self.tree_signals.get_children():
                    if self.tree_signals.item(item, 'values')[0] == coin:
                        self.tree_signals.delete(item)
                        break
                
                # İlgili thread'i durdur
                if coin in self.analysis_threads:
                    self.analysis_threads[coin] = False
                
                self.log(f"{coin} izleme listesinden çıkarıldı")
    
    def toggle_connection(self):
        """Binance API bağlantısı açma/kapama"""
        if not self.client:
            # Bağlantı kurma
            api_key = self.entry_api_key.get()
            api_secret = self.entry_api_secret.get()
            
            if not api_key or not api_secret:
                messagebox.showerror("Hata", "API Key ve API Secret girilmelidir!")
                return
            
            try:
                self.client = Client(api_key, api_secret)
                # Test API bağlantısı
                account_info = self.client.get_account()
                
                self.lbl_status.config(text="Bağlı", foreground="green")
                self.btn_connect.config(text="Bağlantıyı Kes")
                self.btn_start_bot.config(state="normal")
                self.api_key = api_key
                self.api_secret = api_secret
                
                self.log("Binance API'ye başarıyla bağlanıldı")
                self.update_balance()
                
            except Exception as e:
                messagebox.showerror("Bağlantı Hatası", f"API bağlantısı kurulamadı: {str(e)}")
                self.log(f"Bağlantı hatası: {str(e)}")
                self.client = None
        else:
            # Bağlantıyı kesme
            self.stop_bot()
            self.client = None
            self.lbl_status.config(text="Bağlı Değil", foreground="red")
            self.btn_connect.config(text="Bağlan")
            self.btn_start_bot.config(state="disabled")
            self.log("Binance API bağlantısı kesildi")
    
    def update_balance(self):
        """Bakiye bilgilerini güncelleme"""
        if not self.client:
            return
        
        try:
            account = self.client.get_account()
            balances = account['balances']
            
            usdt_balance = next((float(b['free']) for b in balances if b['asset'] == 'USDT'), 0)
            
            self.lbl_usdt_balance.config(text=f"{usdt_balance:.2f}")
            
            self.log(f"Bakiye güncellendi - USDT: {usdt_balance:.2f}")
        
        except Exception as e:
            self.log(f"Bakiye güncelleme hatası: {str(e)}")
    
    def toggle_bot(self):
        """Botu başlatma/durdurma"""
        if not self.running:
            # Botu başlat
            self.running = True
            self.btn_start_bot.config(text="Botu Durdur")
            
            # Bot ayarlarını güncelle
            self.trade_interval = self.cmb_interval.get()
            
            # Her coin için analiz thread'i başlat
            for coin in self.watch_list:
                self.start_coin_analysis(coin)
            
            self.log(f"Bot başlatıldı. Strateji: Çoklu, İşlem aralığı: {self.trade_interval}")
        else:
            # Botu durdur
            self.stop_bot()
    
    def stop_bot(self):
        """Botu durdurma"""
        if self.running:
            self.running = False
            self.btn_start_bot.config(text="Botu Başlat")
            
            # Tüm analiz thread'lerini durdur
            for coin in self.analysis_threads:
                self.analysis_threads[coin] = False
            
            self.log("Bot durduruldu")
    
    def start_coin_analysis(self, coin):
        """Belirli bir coin için analiz thread'i başlatma"""
        self.analysis_threads[coin] = True
        thread = threading.Thread(target=self.analyze_coin, args=(coin,))
        thread.daemon = True
        thread.start()
        self.log(f"{coin} analizi başlatıldı")
    
    def analyze_coin(self, coin):
        """Coin için sürekli analiz yapma"""
        while self.analysis_threads.get(coin, False) and self.running:
            try:
                # Coin verilerini al
                klines = self.client.get_historical_klines(
                    coin,
                    self.trade_interval,
                    "100 hours ago UTC"
                )
                
                # Pandas DataFrame'e dönüştür
                df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 
                                                'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
                                                'taker_buy_quote_asset_volume', 'ignore'])
                
                # Veri tipi dönüşümleri
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df['close'] = df['close'].astype(float)
                df['high'] = df['high'].astype(float)
                df['low'] = df['low'].astype(float)
                df['open'] = df['open'].astype(float)
                df['volume'] = df['volume'].astype(float)
                
                # Son fiyat bilgisi
                last_price = float(df['close'].iloc[-1])
                
                # 24 saatlik değişim
                change_24h = ((last_price / float(df['close'].iloc[-24])) - 1) * 100 if len(df) >= 24 else 0
                
                # Teknik göstergeler
                self.calculate_indicators(df, coin)
                
                # Coin verilerini sakla
                self.coin_data[coin] = df
                
                # Strateji sinyalleri
                sma_signal = self.strategy_sma(df)
                rsi_signal = self.strategy_rsi(df)
                macd_signal = self.strategy_macd(df)
                bollinger_signal = self.strategy_bollinger(df)
                
                # Genel sinyal hesaplama (ağırlıklı)
                general_signal = self.calculate_general_signal(sma_signal, rsi_signal, macd_signal, bollinger_signal)
                
                # Sinyal tablosunu güncelle
                self.update_signal_table(
                    coin, 
                    last_price, 
                    change_24h, 
                    general_signal, 
                    sma_signal, 
                    rsi_signal, 
                    macd_signal, 
                    bollinger_signal
                )
                
                # Alım/satım kararı
                if general_signal == "BUY":
                    self.execute_buy(coin, last_price)
                elif general_signal == "SELL":
                    self.execute_sell(coin, last_price)
                
                # 30 saniye bekle
                for i in range(30):
                    if not self.analysis_threads.get(coin, False) or not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.log(f"{coin} analiz hatası: {str(e)}")
                time.sleep(10)  # Hata durumunda 10 saniye bekle
    
    def calculate_indicators(self, df, coin):
        """Tüm teknik göstergeleri hesaplama"""
        try:
            # SMA göstergeleri
            short_period = int(self.entry_sma_short.get())
            long_period = int(self.entry_sma_long.get())
            df['sma_short'] = df['close'].rolling(window=short_period).mean()
            df['sma_long'] = df['close'].rolling(window=long_period).mean()
            
            # RSI göstergesi
            rsi_period = int(self.entry_rsi_period.get())
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD göstergeleri
            fast_period = 12
            slow_period = 26
            signal_period = 9
            df['ema_fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
            df['ema_slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()
            df['macd'] = df['ema_fast'] - df['ema_slow']
            df['macd_signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
            
            # Bollinger Bantları
            period = 20
            stdev_factor = 2
            df['sma'] = df['close'].rolling(window=period).mean()
            df['stdev'] = df['close'].rolling(window=period).std()
            df['upper_band'] = df['sma'] + (df['stdev'] * stdev_factor)
            df['lower_band'] = df['sma'] - (df['stdev'] * stdev_factor)
            
            # Ek göstergeler
            # Stokastik
            stoch_k_period = 14
            stoch_d_period = 3
            low_min = df['low'].rolling(window=stoch_k_period).min()
            high_max = df['high'].rolling(window=stoch_k_period).max()
            df['stoch_k'] = 100 * ((df['close'] - low_min) / (high_max - low_min))
            df['stoch_d'] = df['stoch_k'].rolling(window=stoch_d_period).mean()
            
            # ADX (Average Directional Index)
            adx_period = 14
            df['tr1'] = abs(df['high'] - df['low'])
            df['tr2'] = abs(df['high'] - df['close'].shift())
            df['tr3'] = abs(df['low'] - df['close'].shift())
            df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
            df['atr'] = df['tr'].rolling(window=adx_period).mean()
            
        except Exception as e:
            self.log(f"{coin} gösterge hesaplama hatası: {str(e)}")
    
    def calculate_general_signal(self, sma_signal, rsi_signal, macd_signal, bollinger_signal):
        """Ağırlıklı genel sinyal hesaplama"""
        try:
            # Ağırlıkları al
            w_sma = float(self.entry_weight_sma.get()) / 100.0
            w_rsi = float(self.entry_weight_rsi.get()) / 100.0
            w_macd = float(self.entry_weight_macd.get()) / 100.0
            w_bollinger = float(self.entry_weight_bollinger.get()) / 100.0
            
            # Sinyalleri sayısal değerlere dönüştür
            signal_values = {
                'BUY': 1,
                'HOLD': 0,
                'SELL': -1
            }
            
            # Ağırlıklı toplam hesapla
            weighted_sum = (
                w_sma * signal_values[sma_signal] +
                w_rsi * signal_values[rsi_signal] +
                w_macd * signal_values[macd_signal] +
                w_bollinger * signal_values[bollinger_signal]
            )
            
            # Karara dönüştür
            if weighted_sum > 0.3:
                return "BUY"
            elif weighted_sum < -0.3:
                return "SELL"
            else:
                return "HOLD"
                
        except Exception as e:
            self.log(f"Genel sinyal hesaplama hatası: {str(e)}")
            return "HOLD"
    
    def update_signal_table(self, coin, price, change_24h, general_signal, sma_signal, rsi_signal, macd_signal, bollinger_signal):
        """Sinyal tablosunu güncelleme"""
        try:
            # Thread güvenliği için ana thread'de çalıştır
            self.root.after(0, self._update_signal_table_main_thread, coin, price, change_24h, 
                          general_signal, sma_signal, rsi_signal, macd_signal, bollinger_signal)
        except Exception as e:
            self.log(f"Sinyal tablosu güncelleme hatası: {str(e)}")
    
    def _update_signal_table_main_thread(self, coin, price, change_24h, general_signal, sma_signal, rsi_signal, macd_signal, bollinger_signal):
        """Ana thread'de sinyal tablosu güncelleme"""
        try:
            # Tarih formatı
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Coin mevcut mu kontrol et
            exists = False
            for item in self.tree_signals.get_children():
                if self.tree_signals.item(item, 'values')[0] == coin:
                    # Mevcut satırı güncelle
                    self.tree_signals.item(item, values=(
                        coin, 
                        f"{price:.8f}", 
                        f"{change_24h:.2f}%", 
                        general_signal, 
                        sma_signal, 
                        rsi_signal, 
                        macd_signal, 
                        bollinger_signal, 
                        update_time
                    ))
                    exists = True
                    break
            
            # Yoksa yeni satır ekle
            if not exists:
                self.tree_signals.insert('', tk.END, values=(
                    coin, 
                    f"{price:.8f}", 
                    f"{change_24h:.2f}%", 
                    general_signal, 
                    sma_signal, 
                    rsi_signal, 
                    macd_signal, 
                    bollinger_signal, 
                    update_time
                ))
                
            # Sinyal renklerini ayarla
            self._color_signal_table()
            
        except Exception as e:
            self.log(f"Sinyal tablosu güncelleme hatası (ana thread): {str(e)}")
    
    def _color_signal_table(self):
        """Sinyal tablosundaki satırları sinyale göre renklendir"""
        for item in self.tree_signals.get_children():
            values = self.tree_signals.item(item, 'values')
            general_signal = values[3]
            
            if general_signal == "BUY":
                self.tree_signals.item(item, tags=('buy',))
            elif general_signal == "SELL":
                self.tree_signals.item(item, tags=('sell',))
            else:
                self.tree_signals.item(item, tags=('hold',))
        
        # Tag renklendirmelerini tanımla
        self.tree_signals.tag_configure('buy', background='#d0f0d0')  # Açık yeşil
        self.tree_signals.tag_configure('sell', background='#f0d0d0')  # Açık kırmızı
        self.tree_signals.tag_configure('hold', background='#f0f0d0')  # Açık sarı
    
    def show_coin_analysis(self, event):
        """Seçili coin için detaylı analiz gösterme"""
        try:
            # Listeden seçili coin'i al
            selection = self.listbox_analysis_coins.curselection()
            if not selection:
                return
            
            coin = self.listbox_analysis_coins.get(selection[0])
            
            # Coin verisi var mı kontrol et
            if coin not in self.coin_data:
                self.txt_analysis_details.delete(1.0, tk.END)
                self.txt_analysis_details.insert(tk.END, f"{coin} için henüz veri yok. Bot çalışınca veriler güncellenecek.")
                return
            
            # Coin verilerini al
            df = self.coin_data[coin]
            
            # Başlık güncelle
            self.lbl_coin_title.config(text=f"{coin} Analizi")
            
            # Grafik çiz
            self._draw_analysis_chart(df, coin)
            
            # Detaylı analiz
            self._update_analysis_details(df, coin)
            
        except Exception as e:
            self.log(f"Coin analizi gösterme hatası: {str(e)}")
    
    def _draw_analysis_chart(self, df, coin):
        """Analiz grafiğini çizme"""
        try:
            # Grafik temizleme
            self.ax_analysis.clear()
            
            # Son 30 mum
            data = df.iloc[-30:]
            
            # Mum grafiği
            dates = data['timestamp']
            
            # Mum çubukları için renkler
            colors = ['green' if close >= open else 'red' for close, open in zip(data['close'], data['open'])]
            
            # Mum gövdelerini çiz
            self.ax_analysis.bar(dates, data['close'] - data['open'], bottom=data['open'], color=colors, width=0.6)
            
            # Mum fitillerini çiz
            for i in range(len(dates)):
                date = dates.iloc[i]
                low = data['low'].iloc[i]
                high = data['high'].iloc[i]
                open_price = data['open'].iloc[i]
                close_price = data['close'].iloc[i]
                
                self.ax_analysis.plot([date, date], [low, min(open_price, close_price)], color='black', linewidth=1)
                self.ax_analysis.plot([date, date], [max(open_price, close_price), high], color='black', linewidth=1)
            
            # Göstergeleri çiz
            self.ax_analysis.plot(dates, data['sma_short'], color='blue', linewidth=1, label=f"SMA Kısa")
            self.ax_analysis.plot(dates, data['sma_long'], color='orange', linewidth=1, label=f"SMA Uzun")
            
            # Bollinger bantları
            self.ax_analysis.plot(dates, data['upper_band'], color='red', linestyle='--', linewidth=1, label="Üst Bant")
            self.ax_analysis.plot(dates, data['sma'], color='gray', linestyle='-', linewidth=1, label="SMA-20")
            self.ax_analysis.plot(dates, data['lower_band'], color='green', linestyle='--', linewidth=1, label="Alt Bant")
            
            # Alt grafik için ikinci y ekseni
            ax2 = self.ax_analysis.twinx()
            
            # RSI grafiği
            ax2.plot(dates, data['rsi'], color='purple', linewidth=1, label="RSI")
            ax2.axhline(y=int(self.entry_rsi_oversold.get()), color='green', linestyle='--')
            ax2.axhline(y=int(self.entry_rsi_overbought.get()), color='red', linestyle='--')
            ax2.set_ylim(0, 100)
            
            # Grafik ayarları
            self.ax_analysis.set_xlabel('Tarih')
            self.ax_analysis.set_ylabel('Fiyat')
            ax2.set_ylabel('RSI')
            self.ax_analysis.grid(True, alpha=0.3)
            
            # Efsaneler
            self.ax_analysis.legend(loc='upper left')
            ax2.legend(loc='upper right')
            
            # X ekseni tarih formatını ayarla
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Grafiği yenile
            self.canvas_analysis.draw()
            
        except Exception as e:
            self.log(f"Analiz grafiği çizme hatası: {str(e)}")
    
    def _update_analysis_details(self, df, coin):
        """Analiz detaylarını güncelleme"""
        try:
            # Analiz detaylarını temizle
            self.txt_analysis_details.delete(1.0, tk.END)
            
            # Son satır verilerini al
            last_row = df.iloc[-1]
            
            # Fiyat bilgileri
            last_price = last_row['close']
            prev_day_close = df.iloc[-24]['close'] if len(df) >= 24 else df.iloc[0]['close']
            change_24h = ((last_price / prev_day_close) - 1) * 100
            
            # Teknik göstergeler
            sma_short = last_row['sma_short']
            sma_long = last_row['sma_long']
            rsi = last_row['rsi']
            macd = last_row['macd']
            macd_signal = last_row['macd_signal']
            macd_hist = last_row['macd_hist']
            upper_band = last_row['upper_band']
            lower_band = last_row['lower_band']
            sma20 = last_row['sma']
            
            # SMA durumu
            sma_status = "Altında" if last_price < sma_long else "Üstünde"
            sma_cross = "Alttan Kesiyor (Alım)" if df['sma_short'].iloc[-2] < df['sma_long'].iloc[-2] and sma_short > sma_long else \
                       "Üstten Kesiyor (Satım)" if df['sma_short'].iloc[-2] > df['sma_long'].iloc[-2] and sma_short < sma_long else \
                       "Kesişme Yok"
            
            # RSI durumu
            oversold = int(self.entry_rsi_oversold.get())
            overbought = int(self.entry_rsi_overbought.get())
            rsi_status = "Aşırı Satım Bölgesi (Alım Fırsatı)" if rsi < oversold else \
                         "Aşırı Alım Bölgesi (Satım Fırsatı)" if rsi > overbought else \
                         "Nötr Bölge"
            
            # MACD durumu
            macd_status = "MACD, Sinyal Çizgisinin Üstünde (Yükseliş)" if macd > macd_signal else \
                         "MACD, Sinyal Çizgisinin Altında (Düşüş)"
            macd_cross = "Alttan Kesiyor (Alım)" if df['macd'].iloc[-2] < df['macd_signal'].iloc[-2] and macd > macd_signal else \
                        "Üstten Kesiyor (Satım)" if df['macd'].iloc[-2] > df['macd_signal'].iloc[-2] and macd < macd_signal else \
                        "Kesişme Yok"
            
            # Bollinger Bantları durumu
            bb_status = "Alt Bandın Altında (Aşırı Satım)" if last_price < lower_band else \
                       "Üst Bandın Üstünde (Aşırı Alım)" if last_price > upper_band else \
                       "Bantlar İçinde (Nötr)"
            
            # Destek ve direnç seviyeleri
            # Son 30 veriden destek ve direnç hesapla
            recent_data = df.iloc[-30:]
            supports = recent_data.nsmallest(3, 'low')['low'].tolist()
            resistances = recent_data.nlargest(3, 'high')['high'].tolist()
            
            # Analiz metnini oluştur
            analysis_text = f"{coin} TEKNİK ANALİZ DETAYLARI\n"
            analysis_text += "="*50 + "\n\n"
            
            analysis_text += f"Fiyat Bilgileri:\n"
            analysis_text += f"Son Fiyat: {last_price:.8f}\n"
            analysis_text += f"24s Değişim: {change_24h:.2f}%\n\n"
            
            analysis_text += f"SMA Analizi:\n"
            analysis_text += f"SMA Kısa ({self.entry_sma_short.get()}): {sma_short:.8f}\n"
            analysis_text += f"SMA Uzun ({self.entry_sma_long.get()}): {sma_long:.8f}\n"
            analysis_text += f"Fiyat, Uzun SMA'nın {sma_status}\n"
            analysis_text += f"SMA Kesişim Durumu: {sma_cross}\n\n"
            
            analysis_text += f"RSI Analizi:\n"
            analysis_text += f"RSI ({self.entry_rsi_period.get()}): {rsi:.2f}\n"
            analysis_text += f"RSI Durumu: {rsi_status}\n\n"
            
            analysis_text += f"MACD Analizi:\n"
            analysis_text += f"MACD: {macd:.8f}\n"
            analysis_text += f"MACD Sinyal: {macd_signal:.8f}\n"
            analysis_text += f"MACD Histogram: {macd_hist:.8f}\n"
            analysis_text += f"MACD Durumu: {macd_status}\n"
            analysis_text += f"MACD Kesişim: {macd_cross}\n\n"
            
            analysis_text += f"Bollinger Bantları Analizi:\n"
            analysis_text += f"Üst Bant: {upper_band:.8f}\n"
            analysis_text += f"Orta Bant (SMA-20): {sma20:.8f}\n"
            analysis_text += f"Alt Bant: {lower_band:.8f}\n"
            analysis_text += f"Bollinger Durumu: {bb_status}\n\n"
            
            analysis_text += f"Destek Seviyeleri:\n"
            for i, level in enumerate(supports, 1):
                analysis_text += f"Destek {i}: {level:.8f}\n"
            
            analysis_text += f"\nDirenç Seviyeleri:\n"
            for i, level in enumerate(resistances, 1):
                analysis_text += f"Direnç {i}: {level:.8f}\n"
            
            # Genel durum
            sma_signal = self.strategy_sma(df)
            rsi_signal = self.strategy_rsi(df)
            macd_signal = self.strategy_macd(df)
            bollinger_signal = self.strategy_bollinger(df)
            general_signal = self.calculate_general_signal(sma_signal, rsi_signal, macd_signal, bollinger_signal)
            
            analysis_text += f"\nGenel Durum:\n"
            analysis_text += f"SMA Sinyali: {sma_signal}\n"
            analysis_text += f"RSI Sinyali: {rsi_signal}\n"
            analysis_text += f"MACD Sinyali: {macd_signal}\n"
            analysis_text += f"Bollinger Sinyali: {bollinger_signal}\n"
            analysis_text += f"GENEL SİNYAL: {general_signal}\n"
            
            # Analiz detaylarını göster
            self.txt_analysis_details.insert(tk.END, analysis_text)
            
        except Exception as e:
            self.log(f"Analiz detayları güncelleme hatası: {str(e)}")
            self.txt_analysis_details.delete(1.0, tk.END)
            self.txt_analysis_details.insert(tk.END, f"Hata: {str(e)}")
    
    def strategy_sma(self, df):
        """SMA kesişim stratejisi"""
        try:
            short_period = int(self.entry_sma_short.get())
            long_period = int(self.entry_sma_long.get())
            
            # Kısa ve uzun dönem SMA hesaplama
            if 'sma_short' not in df.columns or 'sma_long' not in df.columns:
                df['sma_short'] = df['close'].rolling(window=short_period).mean()
                df['sma_long'] = df['close'].rolling(window=long_period).mean()
            
            # Önceki ve şu anki kesişim durumlarını kontrol et
            if len(df) < 3:
                return "HOLD"
                
            prev_short = df['sma_short'].iloc[-3]
            prev_long = df['sma_long'].iloc[-3]
            current_short = df['sma_short'].iloc[-1]
            current_long = df['sma_long'].iloc[-1]
            
            # Alttan kesme (golden cross) - Alım sinyali
            if prev_short < prev_long and current_short > current_long:
                return "BUY"
            
            # Üstten kesme (death cross) - Satım sinyali
            elif prev_short > prev_long and current_short < current_long:
                return "SELL"
            
            # Son fiyat SMA'nın çok üstündeyse satım sinyali
            last_price = df['close'].iloc[-1]
            if last_price > current_long * 1.05:  # %5 üzerindeyse
                return "SELL"
                
            # Son fiyat SMA'nın çok altındaysa alım sinyali
            if last_price < current_long * 0.95:  # %5 altındaysa
                return "BUY"
            
            return "HOLD"
        except Exception as e:
            self.log(f"SMA strateji hatası: {str(e)}")
            return "HOLD"
    
    def strategy_rsi(self, df):
        """RSI stratejisi"""
        try:
            period = int(self.entry_rsi_period.get())
            oversold = int(self.entry_rsi_oversold.get())
            overbought = int(self.entry_rsi_overbought.get())
            
            # RSI hesaplama
            if 'rsi' not in df.columns:
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                df['rsi'] = 100 - (100 / (1 + rs))
            
            if len(df) < 2:
                return "HOLD"
                
            current_rsi = df['rsi'].iloc[-1]
            prev_rsi = df['rsi'].iloc[-2]
            
            # Aşırı satım bölgesinden çıkış - Alım sinyali
            if prev_rsi < oversold and current_rsi > oversold:
                return "BUY"
            
            # Aşırı alım bölgesinden çıkış - Satım sinyali
            elif prev_rsi > overbought and current_rsi < overbought:
                return "SELL"
            
            # RSI aşırı bölgelerdeyse
            if current_rsi < oversold:
                return "BUY"
            elif current_rsi > overbought:
                return "SELL"
            
            return "HOLD"
        except Exception as e:
            self.log(f"RSI strateji hatası: {str(e)}")
            return "HOLD"
    
    def strategy_macd(self, df):
        """MACD stratejisi"""
        try:
            # MACD parametreleri
            if 'macd' not in df.columns or 'macd_signal' not in df.columns:
                fast_period = 12
                slow_period = 26
                signal_period = 9
                
                # EMA hesaplama
                df['ema_fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
                df['ema_slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()
                
                # MACD çizgisi
                df['macd'] = df['ema_fast'] - df['ema_slow']
                
                # Sinyal çizgisi
                df['macd_signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean()
                
                # MACD histogramı
                df['macd_hist'] = df['macd'] - df['macd_signal']
            
            if len(df) < 3:
                return "HOLD"
                
            # Önceki ve şimdiki histogram ve MACD değerleri
            prev_hist = df['macd_hist'].iloc[-2]
            current_hist = df['macd_hist'].iloc[-1]
            prev_macd = df['macd'].iloc[-2]
            current_macd = df['macd'].iloc[-1]
            prev_signal = df['macd_signal'].iloc[-2]
            current_signal = df['macd_signal'].iloc[-1]
            
            # Histogramın sıfırı yukarı kesmesi - Alım sinyali
            if prev_hist < 0 and current_hist > 0:
                return "BUY"
            
            # Histogramın sıfırı aşağı kesmesi - Satım sinyali
            elif prev_hist > 0 and current_hist < 0:
                return "SELL"
            
            # MACD sinyal çizgisini alttan kesmesi - Alım sinyali
            if prev_macd < prev_signal and current_macd > current_signal:
                return "BUY"
            
            # MACD sinyal çizgisini üstten kesmesi - Satım sinyali
            elif prev_macd > prev_signal and current_macd < current_signal:
                return "SELL"
            
            return "HOLD"
        except Exception as e:
            self.log(f"MACD strateji hatası: {str(e)}")
            return "HOLD"
    
    def strategy_bollinger(self, df):
        """Bollinger Bant stratejisi"""
        try:
            # Bollinger parametreleri
            if 'upper_band' not in df.columns or 'lower_band' not in df.columns:
                period = 20
                stdev_factor = 2
                
                # Ortalama ve standart sapma hesaplama
                df['sma'] = df['close'].rolling(window=period).mean()
                df['stdev'] = df['close'].rolling(window=period).std()
                
                # Üst ve alt bantları hesaplama
                df['upper_band'] = df['sma'] + (df['stdev'] * stdev_factor)
                df['lower_band'] = df['sma'] - (df['stdev'] * stdev_factor)
            
            # Son kapanış fiyatı
            last_close = df['close'].iloc[-1]
            
            # Son fiyat alt bandın altında - Alım sinyali
            if last_close < df['lower_band'].iloc[-1]:
                return "BUY"
            
            # Son fiyat üst bandın üstünde - Satım sinyali
            elif last_close > df['upper_band'].iloc[-1]:
                return "SELL"
            
            # Son 3 mumu kontrol et - alt banda yaklaşıyor mu?
            if len(df) >= 3:
                if df['close'].iloc[-3] > df['close'].iloc[-2] > df['close'].iloc[-1] and last_close < df['sma'].iloc[-1]:
                    # Düşüş trendi ve orta bandın altında
                    return "SELL"
                
                if df['close'].iloc[-3] < df['close'].iloc[-2] < df['close'].iloc[-1] and last_close > df['sma'].iloc[-1]:
                    # Yükseliş trendi ve orta bandın üstünde
                    return "BUY"
            
            return "HOLD"
        except Exception as e:
            self.log(f"Bollinger strateji hatası: {str(e)}")
            return "HOLD"
    
    def execute_buy(self, coin, price):
        """Alım emri gerçekleştirme"""
        try:
            # Aktif coin sayısı kontrolü
            max_trades = int(self.entry_max_trades.get())
            active_trade_count = len(self.active_coins)
            
            # Eğer maksimum işlem sayısına ulaşıldıysa işlem yapma
            if active_trade_count >= max_trades:
                return
                
            # Coin zaten aktif işlemdeyse işlem yapma
            if coin in self.active_coins:
                return
                
            # USDT miktarını al
            trade_amount = float(self.entry_trade_amount.get())
            
            # Bakiye kontrolü yap
            account = self.client.get_account()
            balances = account['balances']
            usdt_balance = next((float(b['free']) for b in balances if b['asset'] == 'USDT'), 0)
            
            if usdt_balance < trade_amount:
                self.log(f"Yetersiz USDT bakiyesi: {usdt_balance:.2f} < {trade_amount:.2f}")
                return
            
            # Alınacak coin miktarı hesapla
            quantity = trade_amount / price
            
            # Miktar formatını ayarla (Binance için)
            step_size = 0.00001  # Varsayılan adım
            try:
                # Symbol bilgilerini al
                symbol_info = self.client.get_symbol_info(coin)
                if symbol_info:
                    for filter in symbol_info['filters']:
                        if filter['filterType'] == 'LOT_SIZE':
                            step_size = float(filter['stepSize'])
                            break
            except:
                pass
            
            # Adım büyüklüğüne göre yuvarla
            precision = len(str(step_size).rstrip('0').split('.')[-1])
            quantity = float(f"{quantity:.{precision}f}")
            
            # Gerçek alım emri (canlı modda aç)
            # order = self.client.create_order(
            #     symbol=coin,
            #     side=Client.SIDE_BUY,
            #     type=Client.ORDER_TYPE_MARKET,
            #     quantity=quantity
            # )
            
            # Simülasyon modu
            order_id = f"test-{int(time.time())}"
            total = price * quantity
            
            # Aktif coinlere ekle
            self.active_coins[coin] = {
                'buy_price': price,
                'quantity': quantity,
                'buy_time': datetime.now(),
                'stop_loss': price * (1 - (self.stop_loss / 100)),
                'take_profit': price * (1 + (self.take_profit / 100))
            }
            
            # İşlemi tabloya ekle
            self.add_transaction(coin, "ALIM", price, quantity, total)
            
            self.log(f"Alım gerçekleştirildi: {coin} {quantity:.8f} @ {price:.8f} USDT = {total:.2f} USDT")
            
        except Exception as e:
            self.log(f"Alım hatası ({coin}): {str(e)}")
    
    def execute_sell(self, coin, price):
        """Satım emri gerçekleştirme"""
        try:
            # Coin aktif işlemde değilse satış yapma
            if coin not in self.active_coins:
                return
                
            # Satılacak miktarı al
            quantity = self.active_coins[coin]['quantity']
            
            # Gerçek satım emri (canlı modda aç)
            # order = self.client.create_order(
            #     symbol=coin,
            #     side=Client.SIDE_SELL,
            #     type=Client.ORDER_TYPE_MARKET,
            #     quantity=quantity
            # )
            
            # Simülasyon modu
            order_id = f"test-{int(time.time())}"
            total = price * quantity
            buy_price = self.active_coins[coin]['buy_price']
            profit_percent = ((price / buy_price) - 1) * 100
            
            # İşlemi tabloya ekle
            self.add_transaction(coin, "SATIM", price, quantity, total)
            
            # Aktif coinlerden çıkar
            del self.active_coins[coin]
            
            self.log(f"Satım gerçekleştirildi: {coin} {quantity:.8f} @ {price:.8f} USDT = {total:.2f} USDT (Kâr/Zarar: {profit_percent:.2f}%)")
            
        except Exception as e:
            self.log(f"Satım hatası ({coin}): {str(e)}")
    
    def add_transaction(self, coin, transaction_type, price, quantity, total):
        """İşlemi tabloya ekleme"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Thread güvenliği için ana thread'de çalıştır
            self.root.after(0, lambda: self.tree_transactions.insert('', 0, values=(
                timestamp, coin, transaction_type, f"{price:.8f}", f"{quantity:.8f}", f"{total:.2f}"
            )))
        except Exception as e:
            self.log(f"İşlem ekleme hatası: {str(e)}")
    
    def save_settings(self):
        """Ayarları kaydetme"""
        try:
            # API bilgileri
            self.api_key = self.entry_api_key.get()
            self.api_secret = self.entry_api_secret.get()
            
            # İşlem ayarları
            self.trade_interval = self.cmb_interval.get()
            self.stop_loss = float(self.entry_stop_loss.get())
            self.take_profit = float(self.entry_take_profit.get())
            
            # Config dosyasına kaydet
            self.save_config()
            
            messagebox.showinfo("Bilgi", "Ayarlar başarıyla kaydedildi.")
            self.log("Ayarlar kaydedildi")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Ayarlar kaydedilirken hata oluştu: {str(e)}")
            self.log(f"Ayar kaydetme hatası: {str(e)}")
    
    def load_config(self):
        """Config dosyasından ayarları yükleme"""
        config_file = "bot_config.ini"
        
        if os.path.exists(config_file):
            try:
                self.config.read(config_file)
                
                # API bilgileri
                if 'API' in self.config:
                    self.api_key = self.config['API'].get('api_key', '')
                    self.api_secret = self.config['API'].get('api_secret', '')
                
                # İşlem ayarları
                if 'Trading' in self.config:
                    self.trade_interval = self.config['Trading'].get('interval', '1h')
                    self.stop_loss = float(self.config['Trading'].get('stop_loss', '2.0'))
                    self.take_profit = float(self.config['Trading'].get('take_profit', '3.0'))
                
                # İzlenen coinler
                if 'WatchList' in self.config:
                    coins_str = self.config['WatchList'].get('coins', '')
                    if coins_str:
                        self.watch_list = coins_str.split(',')
                
                self.log("Ayarlar config dosyasından yüklendi")
                
            except Exception as e:
                self.log(f"Config yükleme hatası: {str(e)}")
    
    def save_config(self):
        """Ayarları config dosyasına kaydetme"""
        try:
            # API bölümü
            if 'API' not in self.config:
                self.config['API'] = {}
            
            self.config['API']['api_key'] = self.api_key
            self.config['API']['api_secret'] = self.api_secret
            
            # İşlem ayarları bölümü
            if 'Trading' not in self.config:
                self.config['Trading'] = {}
            
            self.config['Trading']['interval'] = self.trade_interval
            self.config['Trading']['stop_loss'] = str(self.stop_loss)
            self.config['Trading']['take_profit'] = str(self.take_profit)
            
            # İzlenen coinler
            if 'WatchList' not in self.config:
                self.config['WatchList'] = {}
                
            self.config['WatchList']['coins'] = ','.join(self.watch_list)
            
            # Dosyaya kaydet
            with open('bot_config.ini', 'w') as configfile:
                self.config.write(configfile)
            
        except Exception as e:
            self.log(f"Config kaydetme hatası: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BinanceTradingBot(root)
    root.mainloop()