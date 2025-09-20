"""
スクリーンショット設定フレーム
"""
import tkinter as tk
from tkinter import ttk

class ScreenshotFrame:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.create_frame()
        
    def create_frame(self):
        """スクリーンショット設定フレーム作成"""
        
        # スクリーンショット設定フレーム
        self.frame = ttk.LabelFrame(self.parent, text="📸 スクリーンショット設定", padding="10")
        self.frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # スクリーンショット撮影オプション
        self.create_screenshot_options()
        
        # スクリーンショット撮影モード
        self.create_capture_modes()
        
        # グリッド設定
        self.frame.columnconfigure(1, weight=1)
    
    def create_screenshot_options(self):
        """スクリーンショットオプション作成"""
        screenshot_options_frame = ttk.Frame(self.frame)
        screenshot_options_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.screenshot_var = tk.BooleanVar(value=True)
        self.screenshot_checkbox = ttk.Checkbutton(
            screenshot_options_frame, 
            text="📸 スクリーンショット撮影", 
            variable=self.screenshot_var, 
            command=self.toggle_screenshot_options
        )
        self.screenshot_checkbox.grid(row=0, column=0, sticky=tk.W)
        
        self.exclude_promoted_var = tk.BooleanVar(value=False)
        self.exclude_promoted_checkbox = ttk.Checkbutton(
            screenshot_options_frame, 
            text="🚫 プロモーション除外", 
            variable=self.exclude_promoted_var
        )
        self.exclude_promoted_checkbox.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
    
    def create_capture_modes(self):
        """撮影モード選択作成"""
        ttk.Label(self.frame, text="撮影モード:").grid(row=1, column=0, sticky=(tk.W, tk.N), padx=(0, 10))
        self.capture_mode_var = tk.StringVar(value="smart_batch")
        capture_mode_frame = ttk.Frame(self.frame)
        capture_mode_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        self.smart_batch_radio = ttk.Radiobutton(
            capture_mode_frame, 
            text="効率的一括撮影", 
            variable=self.capture_mode_var, 
            value="smart_batch"
        )
        self.smart_batch_radio.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        self.full_batch_radio = ttk.Radiobutton(
            capture_mode_frame, 
            text="フルページ撮影", 
            variable=self.capture_mode_var, 
            value="full_batch"
        )
        self.full_batch_radio.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        self.individual_radio = ttk.Radiobutton(
            capture_mode_frame, 
            text="個別アクセス（遅い）", 
            variable=self.capture_mode_var, 
            value="individual"
        )
        self.individual_radio.grid(row=0, column=2, sticky=tk.W)
    
    def toggle_screenshot_options(self):
        """スクリーンショットオプションの有効/無効切り替え"""
        state = 'normal' if self.screenshot_var.get() else 'disabled'
        self.smart_batch_radio.config(state=state)
        self.full_batch_radio.config(state=state)
        self.individual_radio.config(state=state)
    
    def get_settings(self):
        """スクリーンショット設定を取得"""
        return {
            'screenshot_enabled': self.screenshot_var.get(),
            'exclude_promoted': self.exclude_promoted_var.get(),
            'capture_mode': self.capture_mode_var.get()
        }