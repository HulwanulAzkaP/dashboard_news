import os
import sys
import re
from datetime import datetime

class AppLogger:
    def __init__(self, log_dir="logs"):
        try:
            self.log_dir = log_dir
            os.makedirs(self.log_dir, exist_ok=True)
            
            self.filename = os.path.join(
                self.log_dir,
                f"news_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            )
            
            self._write("="*70, to_console=True)
            self._write(f" SESSION START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", to_console=True)
            self._write(f" LOG FILE: {self.filename}", to_console=True)
            self._write("="*70, to_console=True)
        except Exception as e:
            print(f"[Logger Error] {e}")
            raise
    
    def _write(self, msg, to_console=True):
        if to_console:
            print(msg)
        try:
            with open(self.filename, "a", encoding="utf-8") as f:
                f.write(self._strip_ansi(msg) + "\n")
                f.flush()
        except Exception as e:
            print(f"[File Write Error] {e}")
    
    def _strip_ansi(self, text):
        ansi = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi.sub('', str(text))
    
    def info(self, msg):
        now = datetime.now().strftime("%H:%M:%S")
        self._write(f"[{now}] [INFO] {msg}")
    
    def warning(self, msg):
        now = datetime.now().strftime("%H:%M:%S")
        self._write(f"[{now}] [WARN] {msg}")
    
    def error(self, msg):
        now = datetime.now().strftime("%H:%M:%S")
        self._write(f"[{now}] [ERROR] {msg}")
    
    def request(self, ip, method, path, status, duration_ms):
        now = datetime.now().strftime("%H:%M:%S")
        c = "\033[92m" if status < 300 else "\033[93m" if status < 400 else "\033[91m"
        r = "\033[0m"
        console_msg = f"[{now}] [{ip}] {method} {path} {c}{status}{r} ({duration_ms:.0f}ms)"
        print(console_msg)
        
        file_msg = f"[{now}] [{ip}] {method} {path} {status} ({duration_ms:.0f}ms)"
        try:
            with open(self.filename, "a", encoding="utf-8") as f:
                f.write(file_msg + "\n")
                f.flush()
        except:
            pass

# Global instance
logger = AppLogger()