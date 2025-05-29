import os
import sys
import logging
from datetime import datetime
from typing import List, Optional

class Logger:
    """
    Hem dosyaya hem UI'a log gönderebilir.
    """
    def __init__(self, log_dir: str = "logs"):
        # Log dizinini belirle
        if log_dir is None:
            if getattr(sys, 'frozen', False):
                application_path = os.path.dirname(sys.executable)
            else:
                application_path = os.path.dirname(os.path.abspath(__file__))
            
            self.log_dir = os.path.join(application_path, "logs")
        else:
            self.log_dir = log_dir
        
        self.ensure_log_directory()
        self.current_log_file = None
        self.current_date = None
        self.update_log_file()
        
    def ensure_log_directory(self):
        """Log klasörünü kontrol et/oluştur"""
        try:
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)
            # Yazma iznini test et
            test_file = os.path.join(self.log_dir, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            # Alternatif dizin kullan
            user_home = os.path.expanduser("~")
            self.log_dir = os.path.join(user_home, "CryptoTrading_Logs")
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)
        
    def update_log_file(self):
        """Günlük log dosyasını güncelle"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        if current_date != self.current_date:
            self.current_date = current_date
            self.current_log_file = os.path.join(
                self.log_dir, 
                f"cryptobot_log_{current_date}.txt"
            )
            
    def log(self, message: str, level: str = "INFO") -> Optional[str]:
        """Log mesajı yaz"""
        try:
            self.update_log_file()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message = f"[{timestamp}] [{level}] {message}\n"
            
            # Dosyaya yaz
            with open(self.current_log_file, 'a', encoding='utf-8') as f:
                f.write(log_message)
                
            return log_message.strip()  # UI için yeni satır karakteri olmadan döndür
            
        except Exception as e:
            print(f"Loglama hatası: {str(e)}")
            return None
            
    def error(self, message: str) -> Optional[str]:
        """Hata mesajı logla"""
        return self.log(message, "ERROR")
        
    def warning(self, message: str) -> Optional[str]:
        """Uyarı mesajı logla"""
        return self.log(message, "WARNING")
        
    def info(self, message: str) -> Optional[str]:
        """Bilgi mesajı logla"""
        return self.log(message, "INFO")
        
    def get_latest_logs(self, n: int = 100) -> List[str]:
        """Son n log satırını getir"""
        try:
            if not os.path.exists(self.current_log_file):
                return []
                
            with open(self.current_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[-n:]
        except Exception as e:
            print(f"Log okuma hatası: {str(e)}")
            return []

    def export_logs(self, start_date: datetime, end_date: datetime) -> bool:
        """Belirli tarih aralığındaki logları dışa aktar"""
        try:
            export_file = os.path.join(
                self.log_dir,
                f"logs_export_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.txt"
            )
            
            # Tarih aralığındaki tüm log dosyalarını bul
            log_files = []
            current_date = start_date
            while current_date <= end_date:
                file_name = f"cryptobot_log_{current_date.strftime('%Y-%m-%d')}.txt"
                file_path = os.path.join(self.log_dir, file_name)
                if os.path.exists(file_path):
                    log_files.append(file_path)
                current_date = current_date.replace(day=current_date.day + 1)
            
            # Logları birleştir ve dışa aktar
            with open(export_file, 'w', encoding='utf-8') as out_file:
                for log_file in log_files:
                    with open(log_file, 'r', encoding='utf-8') as in_file:
                        out_file.write(in_file.read())
                        
            return True
            
        except Exception as e:
            print(f"Log dışa aktarma hatası: {str(e)}")
            return False

    def cleanup_old_logs(self, days: int = 30) -> bool:
        """Eski log dosyalarını temizle"""
        try:
            current_date = datetime.now()
            for file_name in os.listdir(self.log_dir):
                if not file_name.startswith("cryptobot_log_"):
                    continue
                    
                try:
                    # Log dosyası tarihini al
                    log_date_str = file_name.split("_")[-1].replace(".txt", "")
                    log_date = datetime.strptime(log_date_str, "%Y-%m-%d")
                    
                    # Dosya yaşını kontrol et
                    days_old = (current_date - log_date).days
                    if days_old > days:
                        os.remove(os.path.join(self.log_dir, file_name))
                except:
                    continue
                    
            return True
            
        except Exception as e:
            print(f"Log temizleme hatası: {str(e)}")
            return False