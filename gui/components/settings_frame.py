"""
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
