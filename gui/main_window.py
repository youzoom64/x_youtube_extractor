"""
メインウィンドウクラス（軽量化版）
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
import os
from datetime import datetime
import logging

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.components.settings_frame import SettingsFrame
from gui.components.screenshot_frame import ScreenshotFrame
from gui.components.media_frame import MediaFrame
from gui.components.execution_frame import ExecutionFrame
from gui.components.results_frame import ResultsFrame
from gui.handlers.scraping_handler import ScrapingHandler
from gui.handlers.media_handler import MediaHandler
from gui.handlers.analysis_handler import AnalysisHandler
from gui.utils.ui_helpers import UIHelpers
from gui.utils.validators import URLValidator

logger = logging.getLogger(__name__)

class TwitterScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Twitter スクレイピング + Claude 分析ツール")
        self.root.geometry("1100x900")
        
        # 実行中フラグ
        self.is_running = False
        
        # ハンドラー初期化
        self.scraping_handler = ScrapingHandler(self)
        self.media_handler = MediaHandler(self)
        self.analysis_handler = AnalysisHandler(self)
        
        # UI作成
        self.create_widgets()
        self.check_chrome_connection()

    def create_widgets(self):
        """GUI要素を作成"""
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # タイトル
        title_label = ttk.Label(main_frame, text="🐦 Twitter + YouTube + AI分析ツール", 
                            font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # フレーム作成
        self.settings_frame = SettingsFrame(main_frame, self)
        self.screenshot_frame = ScreenshotFrame(main_frame, self)
        self.media_frame = MediaFrame(main_frame, self)
        self.execution_frame = ExecutionFrame(main_frame, self)
        
        # ログ・結果フレーム
        self.create_log_frame(main_frame)
        self.results_frame = ResultsFrame(main_frame, self)
        
        # グリッド設定
        self.setup_grid_weights(main_frame)

    def create_log_frame(self, parent):
        """ログ表示フレーム作成"""
        log_frame = ttk.LabelFrame(parent, text="📝 ログ", padding="10")
        log_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=18, width=90)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

    def setup_grid_weights(self, main_frame):
        """グリッド重み設定"""
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def check_chrome_connection(self):
        """Chrome接続確認"""
        UIHelpers.check_chrome_connection_async(self.settings_frame.chrome_status_label)
    
    def log_message(self, message):
        """ログメッセージを追加"""
        UIHelpers.log_message(self.log_text, message, self.root)

def main():
    root = tk.Tk()
    app = TwitterScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
