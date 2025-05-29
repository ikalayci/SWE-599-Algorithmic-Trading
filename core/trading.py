import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional
import threading
import time
from .stats import TradingStats
from .analysis import MarketAnalyzer
from utils.language_manager import LanguageManager

class TradingEngine:
    def __init__(self, config: dict):
        self.config = config
        self.is_running = False
        self.is_stopping = False
        self.exchange = None
        self.stats = TradingStats()
        self.active_trades = {}
        self.markets_cache = {}
        self.scan_callback = None
        self._lock = threading.Lock()
        
        # MarketAnalyzer instance'ı oluştur
        self.analyzer = MarketAnalyzer()
        
        # Dil yöneticisi
        self.lang = LanguageManager()
        
    def start(self):
        """Trading sistemini başlat"""
        try:
            self.exchange = ccxt.binance({
                'apiKey': self.config['api_key'],
                'secret': self.config['api_secret'],
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True
                }
            })
            
            # Test API bağlantısı
            self.exchange.load_markets()
            balance = self.exchange.fetch_balance()
            
            # Trading döngüsünü başlat
            self.is_running = True
            self.trading_thread = threading.Thread(target=self._trading_loop)
            self.trading_thread.daemon = True
            self.trading_thread.start()
            
            logging.info(self.lang.__('trading_engine_started'))
            
        except Exception as e:
            error_msg = f"{self.lang.__('trading_engine_start_error')}: {str(e)}"
            logging.error(error_msg)
            raise Exception(error_msg)
        
    def start_closing_positions(self):
        """Manuel durdurma için pozisyonları kapat"""
        with self._lock:
            self.is_stopping = True
            positions_to_close = list(self.active_trades.items())
            all_closed = True
            
            for symbol, position in positions_to_close:
                try:
                    if symbol not in self.active_trades:
                        continue
                    
                    # Manuel kapatma için satış emri ver
                    try:
                        order = self.exchange.create_market_sell_order(
                            symbol=symbol,
                            amount=position['amount']
                        )
                        
                        if order['status'] == 'closed':
                            exit_price = float(order['price'])
                            self._manual_close_position(symbol, exit_price)
                        else:
                            all_closed = False
                            logging.error(f"{symbol} {self.lang.__('buy_order_failed')}: {order['status']}")
                            
                    except Exception as e:
                        all_closed = False
                        logging.error(f"{self.lang.__('sell_order_error')} ({symbol}): {str(e)}")
                        
                except Exception as e:
                    all_closed = False
                    logging.error(f"{self.lang.__('position_close_error')} ({symbol}): {str(e)}")
            
            return all_closed

    def _manual_close_position(self, symbol: str, exit_price: float):
        """Manuel durdurma için pozisyon kayıtlarını güncelle"""
        try:
            if symbol not in self.active_trades:
                return False
                
            position = self.active_trades[symbol]
            
            # Kâr/zarar hesapla
            entry_price = position['entry_price']
            amount = position['amount']
            profit_usdt = (exit_price - entry_price) * amount
            profit_percent = (exit_price - entry_price) / entry_price * 100
            
            # İşlem geçmişine ekle
            trade_data = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'type': 'sell',
                'price': exit_price,
                'amount': amount,
                'total_usdt': exit_price * amount,
                'profit': profit_usdt,
                'profit_percentage': profit_percent,
                'status': self.lang.__('manual_stop')
            }
            self.stats.add_trade_history(trade_data)
            
            # İstatistikleri güncelle
            self.stats.total_trades += 1
            if profit_usdt > 0:
                self.stats.winning_trades += 1
            else:
                self.stats.losing_trades += 1
                
            self.stats.total_profit_usdt += profit_usdt
            
            # Pozisyonu sil
            del self.active_trades[symbol]
            
            # Satış logunu yazdır
            logging.info(
                f"{self.lang.__('manual_sale_completed')}:\n"
                f"{self.lang.__('coin')}: {symbol}\n"
                f"{self.lang.__('entry')}: {entry_price:.8f}\n"
                f"{self.lang.__('exit')}: {exit_price:.8f}\n"
                f"{self.lang.__('profit')}: {profit_usdt:.2f} USDT ({profit_percent:.2f}%)\n"
                f"{self.lang.__('reason')}: {self.lang.__('manual_stop')}"
            )
            
            return True
            
        except Exception as e:
            logging.error(f"{self.lang.__('manual_close_error')} ({symbol}): {str(e)}")
            return False
        
    def stop(self):
        """Trading sistemini durdur"""
        logging.info(self.lang.__('trading_system_stopping'))
        self.is_running = False
        self.is_stopping = True
        
        try:
            # Thread'i durdur
            if hasattr(self, 'trading_thread'):
                self.trading_thread.join(timeout=5)
                self.trading_thread = None
                
            # Exchange'i temizle
            if self.exchange:
                try:
                    self.exchange.close()
                except:
                    pass
                self.exchange = None
                
            # Diğer verileri temizle
            self.active_trades.clear()
            self.markets_cache.clear()
            
            logging.info(self.lang.__('trading_system_stopped'))
            
        except Exception as e:
            logging.error(f"{self.lang.__('trading_stop_error')}: {str(e)}")

    def _trading_loop(self):
        """Ana trading döngüsü"""
        while self.is_running:
            try:                
                # Eğer durdurma işlemi başladıysa, sadece pozisyon kontrolü yap
                if self.is_stopping:
                    self._check_positions()
                    time.sleep(1)
                    continue
                
                # Fırsatları tara
                opportunities = self._scan_markets()
                
                for opp in opportunities:
                    if len(self.active_trades) >= self.config.get('max_positions', 3):
                        break
                        
                    if self._validate_trade(opp):
                        self._execute_trade(opp)
                        
                # Açık pozisyonları kontrol et
                self._check_positions()
                
            except Exception as e:
                logging.error(f"{self.lang.__('trading_loop_error')}: {str(e)}")
            
            time.sleep(1)

    def _scan_markets(self):        
        if self.is_stopping:
            return []
        
        """Piyasaları tara"""
        opportunities = []
        total_opportunities = 0
        scan_results = []
        scan_count = 0
        
        try:
            # Market bilgilerini güncelle (15 dakikada bir)
            current_time = datetime.now()
            if not hasattr(self, '_last_market_update') or \
            (current_time - self._last_market_update).seconds > 900:
                self.markets_cache = {
                    symbol: market for symbol, market in self.exchange.load_markets().items()
                    if (symbol.endswith('/USDT') and 
                        not symbol.startswith(('USDC/', 'BUSD/', 'USDT/')) and
                        market.get('active', False) and  
                        not market.get('info', {}).get('isSpotTradingAllowed', False) is False)
                }
                self._last_market_update = current_time

            # Sadece aktif marketleri tara
            total_markets = len(self.markets_cache)
            scanned_count = 0
            
            for i, (symbol, market) in enumerate(self.markets_cache.items(), 1):
                if not self.is_running:  # Erken çıkış kontrolü
                    return []
                    
                try:
                    scanned_count += 1
                    scan_count += 1
                    
                    if (i % 10 == 0):  # Her 10 coinde bir ilerleme bilgisi
                        logging.info(f"{self.lang.__('progress')}: {i}/{total_markets} {self.lang.__('coins_analyzed')}")
                    
                    # OHLCV verileri al
                    ohlcv = self.exchange.fetch_ohlcv(
                        symbol,
                        self.config.get('timeframe', '15m'),
                        limit=100
                    )
                    
                    if not ohlcv or len(ohlcv) < 100:
                        continue
                        
                    df = pd.DataFrame(
                        ohlcv,
                        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    )
                    
                    ticker = self.exchange.fetch_ticker(symbol)
                    
                    # MarketAnalyzer sınıfını kullan
                    analysis_result = self.analyzer.analyze_market(df)
                    
                    if not analysis_result:
                        continue
                    
                    # Sonuçları sakla
                    scan_result = {
                        'symbol': symbol,
                        'price': float(df['close'].iloc[-1]),
                        'change_24h': ticker.get('percentage', 0),
                        'rsi': analysis_result['indicators']['rsi'],
                        'volume': float(df['volume'].iloc[-1]) * float(df['close'].iloc[-1]),  # USDT cinsinden hacim
                        'score': analysis_result['score'],
                        'signal': analysis_result['signals'],
                        'timestamp': datetime.now()
                    }
                    scan_results.append(scan_result)
                    
                    # UI güncellemesi - ayarlara göre kontrol et
                    if self.scan_callback and self.config.get('live_analysis', False):
                        update_interval = self.config.get('update_interval', 1)
                        if scan_count % update_interval == 0:  # Belirlenen aralıkta güncelle
                            self.scan_callback(scan_results, scanned_count, total_markets)
                    
                    # Minimum hacim kontrolü
                    usdt_volume = float(df['volume'].iloc[-1]) * float(df['close'].iloc[-1])
                    if usdt_volume < self.analyzer.min_volume:
                        continue
                    
                    if analysis_result['score'] >= self.config.get('min_score', 65):
                        opportunity = {
                            'symbol': symbol,
                            'price': float(df['close'].iloc[-1]),
                            'volume': usdt_volume,
                            'analysis': analysis_result
                        }
                        logging.info(f"{self.lang.__('opportunity_found')} - {symbol} - {self.lang.__('score')}: {analysis_result['score']}")
                        total_opportunities += 1
                        
                        # Fırsat bulunur bulunmaz alım kontrolü yap
                        if len(self.active_trades) < self.config.get('max_positions', 3):
                            if self._validate_trade(opportunity):
                                self._execute_trade(opportunity)
                        
                except Exception as e:
                    if 'Market is closed' not in str(e):
                        logging.error(f"{self.lang.__('scan_error')} ({symbol}): {str(e)}")
                    continue
                
            if self.scan_callback:
                self.scan_callback(scan_results, total_markets, total_markets)
                        
            logging.info(f"{self.lang.__('scan_completed')}. {total_opportunities} {self.lang.__('opportunities_found')}.")
            return opportunities
                
        except Exception as e:
            logging.error(f"{self.lang.__('market_scan_error')}: {str(e)}")
            return []

    def _validate_trade(self, opportunity: dict) -> bool:
        """İşlem kurallarını kontrol et"""
        try:
            symbol = opportunity['symbol']
            
            # Aynı coin kontrolü
            if symbol in self.active_trades:
                return False
                
            # Minimum hacim kontrolü (zaten scan_markets'ta kontrol ediliyor ama bir daha kontrol edelim)
            if opportunity['volume'] < self.analyzer.min_volume:
                return False
                
            # Yasaklı coin kontrolü
            excluded_coins = self.config.get('excluded_coins', [])
            if symbol in excluded_coins:
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"{self.lang.__('validation_error')}: {str(e)}")
            return False

    def _execute_trade(self, opportunity: dict):
        if self.is_stopping:
            return []
        
        """Alım emri ver"""
        try:
            symbol = opportunity['symbol']
            
            # İşlem miktarını hesapla
            target_usdt = float(self.config.get('max_usdt', 10))
            available_usdt = float(self.exchange.fetch_balance()['USDT']['free'])
            usdt_amount = min(target_usdt, available_usdt)

            if usdt_amount < target_usdt:
                logging.warning(f"{self.lang.__('insufficient_balance')}. "
                            f"{self.lang.__('target')}: {target_usdt}, {self.lang.__('available')}: {usdt_amount}")
            
            price = opportunity['price']
            amount = usdt_amount / price
            
            # Market emri ver
            order = self.exchange.create_market_buy_order(symbol, amount)
            
            if order['status'] == 'closed':
                # Stop loss ve take profit hesapla
                entry_price = float(order['price'])
                stop_loss = entry_price * (1 - self.config.get('stop_loss', 3) / 100)
                take_profit = entry_price * (1 + self.config.get('take_profit', 2) / 100)
                
                # İşlem geçmişine ekle
                trade_data = {
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'type': 'buy',
                    'price': entry_price,
                    'amount': amount,
                    'total_usdt': entry_price * amount,
                    'status': self.lang.__('open_position')
                }
                self.stats.add_trade_history(trade_data)
                
                # Pozisyonu kaydet
                self.active_trades[symbol] = {
                    'entry_price': entry_price,
                    'amount': float(order['amount']),
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'entry_time': datetime.now(),
                    'analysis_score': opportunity['analysis']['score']
                }
                
                logging.info(
                    f"{self.lang.__('buy_completed')}:\n"
                    f"{self.lang.__('coin')}: {symbol}\n"
                    f"{self.lang.__('price')}: {entry_price:.8f}\n"
                    f"{self.lang.__('amount')}: {amount:.8f}\n"
                    f"Stop Loss: {stop_loss:.8f}\n"
                    f"Take Profit: {take_profit:.8f}\n"
                    f"{self.lang.__('analysis_score')}: {opportunity['analysis']['score']}"
                )
                
        except Exception as e:
            logging.error(f"{self.lang.__('buy_error')} ({symbol}): {str(e)}")

    def _check_positions(self):
        """Açık pozisyonları kontrol et"""
        try:
            for symbol in list(self.active_trades.keys()):
                position = self.active_trades[symbol]
                
                try:
                    current_price = float(self.exchange.fetch_ticker(symbol)['last'])
                    
                    # Stop loss kontrolü
                    if current_price <= position['stop_loss']:
                        self._close_position(symbol, current_price, "STOP-LOSS")
                        continue
                        
                    # Take profit kontrolü
                    if current_price >= position['take_profit']:
                        self._close_position(symbol, current_price, "TAKE-PROFIT")
                        continue
                        
                except Exception as e:
                    logging.error(f"{self.lang.__('position_check_error')} ({symbol}): {str(e)}")
                    
        except Exception as e:
            logging.error(f"{self.lang.__('position_tracking_error')}: {str(e)}")

    def _close_position(self, symbol: str, current_price: float, reason: str):
        """Pozisyonu kapat"""
        try:
            if symbol not in self.active_trades:
                logging.error(f"{self.lang.__('position_not_found')}: {symbol}")
                return False
                
            position = self.active_trades[symbol]
            
            # Bakiye kontrolü
            coin = symbol.split('/')[0]
            balance = self.exchange.fetch_balance()
            
            if coin not in balance or 'free' not in balance[coin]:
                logging.error(f"{self.lang.__('coin_balance_error')}: {coin}")
                return False
                
            available_amount = float(balance[coin]['free'])
            
            if available_amount < position['amount']:
                logging.warning(f"{self.lang.__('amount_correction')}: {available_amount} < {position['amount']}")
                position['amount'] = available_amount
            
            if available_amount <= 0:
                logging.error(f"{self.lang.__('no_balance_to_sell')}: {coin}")
                return False
                
            # Market satış emri
            order = self.exchange.create_market_sell_order(
                symbol=symbol,
                amount=position['amount']
            )
            
            if order['status'] == 'closed':
                # Kâr/zarar hesapla...
                entry_price = position['entry_price']
                exit_price = float(order['price'])
                amount = position['amount']
                
                profit_usdt = (exit_price - entry_price) * amount
                profit_percent = (exit_price - entry_price) / entry_price * 100
                
                # İşlem geçmişine ekle
                trade_data = {
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'type': 'sell',
                    'price': exit_price,
                    'amount': amount,
                    'total_usdt': exit_price * amount,
                    'profit': profit_usdt,
                    'profit_percentage': profit_percent,
                    'status': reason
                }
                self.stats.add_trade_history(trade_data)
                
                # İstatistikleri güncelle...
                self.stats.total_trades += 1
                if profit_usdt > 0:
                    self.stats.winning_trades += 1
                else:
                    self.stats.losing_trades += 1
                    
                self.stats.total_profit_usdt += profit_usdt
                
                # Pozisyonu sil
                del self.active_trades[symbol]
                
                # Satış logunu yazdır
                logging.info(
                    f"{self.lang.__('sale_completed')}:\n"
                    f"{self.lang.__('coin')}: {symbol}\n"
                    f"{self.lang.__('entry')}: {entry_price:.8f}\n"
                    f"{self.lang.__('exit')}: {exit_price:.8f}\n"
                    f"{self.lang.__('profit')}: {profit_usdt:.2f} USDT ({profit_percent:.2f}%)\n"
                    f"{self.lang.__('reason')}: {reason}"
                )
                
                return True
                
            return False
            
        except Exception as e:
            logging.error(f"{self.lang.__('sell_error')} ({symbol}): {str(e)}")
            return False
    
    def _get_signal(self, score: float) -> str:
        """Skora göre sinyal üret - Dil desteği için analyzer'ı kullan"""
        if score >= 85:
            return self.analyzer.lang.__('strong_buy')
        elif score >= 70:
            return self.analyzer.lang.__('buy_signal')
        elif score >= 65:
            return self.analyzer.lang.__('weak_buy')
        elif score <= 35:
            return self.analyzer.lang.__('wait')
        else:
            return self.analyzer.lang.__('neutral')