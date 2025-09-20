#!/usr/bin/env python3
"""
GUI構造作成スクリプト
プロジェクトルートで実行してください。
"""

import os
import sys
from pathlib import Path

def create_directory_structure():
    """ディレクトリ構造を作成"""
    
    # プロジェクトルートの確認
    root_dir = Path.cwd()
    print(f"実行ディレクトリ: {root_dir}")
    
    # guiディレクトリの存在確認
    gui_dir = root_dir / "gui"
    if gui_dir.exists() and (gui_dir / "tkinter_app.py").exists():
        print("✅ 既存のguiディレクトリを確認しました")
    else:
        print("❌ gui/tkinter_app.py が見つかりません。プロジェクトルートで実行してください。")
        return False
    
    # 作成するディレクトリ構造
    directories = [
        "gui/components",
        "gui/handlers", 
        "gui/utils"
    ]
    
    # 作成するファイル一覧
    files = [
        "gui/__init__.py",
        "gui/main_window.py",
        "gui/components/__init__.py",
        "gui/components/settings_frame.py",
        "gui/components/screenshot_frame.py", 
        "gui/components/media_frame.py",
        "gui/components/execution_frame.py",
        "gui/components/results_frame.py",
        "gui/handlers/__init__.py",
        "gui/handlers/scraping_handler.py",
        "gui/handlers/media_handler.py",
        "gui/handlers/analysis_handler.py",
        "gui/utils/__init__.py",
        "gui/utils/ui_helpers.py",
        "gui/utils/validators.py"
    ]
    
    print("\n🔧 ディレクトリ構造を作成中...")
    
    # ディレクトリ作成
    for directory in directories:
        dir_path = root_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 作成: {directory}")
    
    # ファイル作成
    print("\n📝 ファイルを作成中...")
    for file_path in files:
        full_path = root_dir / file_path
        if not full_path.exists():
            full_path.touch()
            print(f"📄 作成: {file_path}")
        else:
            print(f"⚠️  既存: {file_path}")
    
    print("\n✅ 構造作成完了!")
    return True

def write_initial_content():
    """初期コンテンツを各ファイルに書き込み"""
    
    root_dir = Path.cwd()
    
    # 各ファイルの初期内容
    file_contents = {
        "gui/__init__.py": '''"""
GUI パッケージ
Twitter スクレイピング + Claude 分析ツール
"""

from .main_window import TwitterScraperGUI

__all__ = ['TwitterScraperGUI']
''',
        
        "gui/main_window.py": '''"""
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

from .components.settings_frame import SettingsFrame
from .components.screenshot_frame import ScreenshotFrame
from .components.media_frame import MediaFrame
from .components.execution_frame import ExecutionFrame
from .components.results_frame import ResultsFrame
from .handlers.scraping_handler import ScrapingHandler
from .handlers.media_handler import MediaHandler
from .handlers.analysis_handler import AnalysisHandler
from .utils.ui_helpers import UIHelpers
from .utils.validators import URLValidator

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
''',
        
        "gui/components/__init__.py": '''"""
GUI コンポーネント
"""

from .settings_frame import SettingsFrame
from .screenshot_frame import ScreenshotFrame
from .media_frame import MediaFrame
from .execution_frame import ExecutionFrame
from .results_frame import ResultsFrame

__all__ = [
    'SettingsFrame',
    'ScreenshotFrame', 
    'MediaFrame',
    'ExecutionFrame',
    'ResultsFrame'
]
''',
        
        "gui/components/settings_frame.py": '''"""
基本設定フレーム
"""
import tkinter as tk
from tkinter import ttk

class SettingsFrame:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.create_frame()
        
    def create_frame(self):
        """基本設定フレーム作成"""
        
        # 基本設定フレーム
        self.frame = ttk.LabelFrame(self.parent, text="⚙️ 基本設定", padding="10")
        self.frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Chrome接続状態
        self.chrome_status_label = ttk.Label(self.frame, text="Chrome接続状態: 確認中...")
        self.chrome_status_label.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # 共用URL/クエリ入力
        ttk.Label(self.frame, text="URL / 検索クエリ:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.query_var = tk.StringVar()
        self.query_entry = ttk.Entry(self.frame, textvariable=self.query_var, width=70)
        self.query_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # URL/クエリ種別表示
        self.url_type_label = ttk.Label(self.frame, text="種別: 自動判定", foreground="blue")
        self.url_type_label.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        # URL/クエリ変更時の自動判定
        self.query_var.trace('w', self._on_url_change)
        
        # 取得件数設定
        self.create_count_setting()
        
        # 出力形式とソート順
        self.create_format_and_sort_options()
        
        # グリッド設定
        self.frame.columnconfigure(1, weight=1)
    
    def create_count_setting(self):
        """取得件数設定作成"""
        ttk.Label(self.frame, text="取得件数:").grid(row=3, column=0, sticky=tk.W, padx=(0, 10))
        self.count_var = tk.IntVar(value=20)
        count_frame = ttk.Frame(self.frame)
        count_frame.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.count_scale = ttk.Scale(count_frame, from_=1, to=100, orient=tk.HORIZONTAL, 
                                    variable=self.count_var, length=300)
        self.count_scale.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.count_label = ttk.Label(count_frame, text="20")
        self.count_label.grid(row=0, column=1, padx=(10, 0))
        self.count_scale.configure(command=self.update_count_label)
        
        count_frame.columnconfigure(0, weight=1)
    
    def create_format_and_sort_options(self):
        """出力形式とソート順オプション作成"""
        options_frame = ttk.Frame(self.frame)
        options_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 出力形式
        ttk.Label(options_frame, text="出力形式:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.format_var = tk.StringVar(value="txt")
        format_frame = ttk.Frame(options_frame)
        format_frame.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Radiobutton(format_frame, text="TXT", variable=self.format_var, value="txt").grid(row=0, column=0, padx=(0, 10))
        ttk.Radiobutton(format_frame, text="JSON", variable=self.format_var, value="json").grid(row=0, column=1)
        
        # ソート順選択
        ttk.Label(options_frame, text="ソート順:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.sort_var = tk.StringVar(value="latest")
        sort_frame = ttk.Frame(options_frame)
        sort_frame.grid(row=0, column=3, sticky=tk.W)
        
        ttk.Radiobutton(sort_frame, text="最新順", variable=self.sort_var, value="latest").grid(row=0, column=0, padx=(0, 10))
        ttk.Radiobutton(sort_frame, text="話題順", variable=self.sort_var, value="top").grid(row=0, column=1)
    
    def update_count_label(self, value):
        """カウントラベルを更新"""
        self.count_label.config(text=str(int(float(value))))
    
    def _on_url_change(self, *args):
        """URL/クエリ変更時の自動判定"""
        from ..utils.validators import URLValidator
        URLValidator.update_url_type_display(self.query_var, self.url_type_label)
''',
        
        "gui/handlers/__init__.py": '''"""
ビジネスロジックハンドラー
"""

from .scraping_handler import ScrapingHandler
from .media_handler import MediaHandler
from .analysis_handler import AnalysisHandler

__all__ = [
    'ScrapingHandler',
    'MediaHandler', 
    'AnalysisHandler'
]
''',
        
        "gui/utils/__init__.py": '''"""
GUI ユーティリティ
"""

from .ui_helpers import UIHelpers
from .validators import URLValidator

__all__ = ['UIHelpers', 'URLValidator']
'''
    }
    
    print("\n📝 初期コンテンツを書き込み中...")
    
    for file_path, content in file_contents.items():
        full_path = root_dir / file_path
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content.lstrip())
            print(f"✅ 書き込み完了: {file_path}")
        except Exception as e:
            print(f"❌ 書き込み失敗: {file_path} - {e}")

def main():
    print("🚀 GUI構造作成スクリプト")
    print("=" * 50)
    
    # ディレクトリ構造作成
    if not create_directory_structure():
        sys.exit(1)
    
    # 初期コンテンツ書き込み
    write_initial_content()
    
    print("\n" + "=" * 50)
    print("🎉 GUI構造作成完了!")
    print("\n📋 次のステップ:")
    print("1. 残りのファイルの実装")
    print("2. 既存のtkinter_app.pyから機能移植")
    print("3. インポート修正とテスト")
    print("\n📁 作成された構造:")
    print("""
gui/
├── __init__.py
├── main_window.py
├── components/
│   ├── __init__.py
│   ├── settings_frame.py
│   ├── screenshot_frame.py
│   ├── media_frame.py
│   ├── execution_frame.py
│   └── results_frame.py
├── handlers/
│   ├── __init__.py
│   ├── scraping_handler.py
│   ├── media_handler.py
│   └── analysis_handler.py
└── utils/
    ├── __init__.py
    ├── ui_helpers.py
    └── validators.py
    """)

if __name__ == "__main__":
    main()