"""
結果表示・操作フレーム
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os

class ResultsFrame:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        
        # 結果ファイルパス
        self.result_file_path = None
        self.video_file_path = None
        self.screenshot_files = None
        self.summary_file = None
        self.comments_file_path = None
        
        self.create_frame()
        
    def create_frame(self):
        """結果表示フレーム作成"""
        
        # 結果表示フレーム
        self.frame = ttk.LabelFrame(self.parent, text="📄 結果", padding="10")
        self.frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 結果表示ラベル
        self.result_label = ttk.Label(self.frame, text="結果はここに表示されます")
        self.result_label.grid(row=0, column=0, columnspan=5, sticky=tk.W, pady=(0, 10))
        
        # 結果操作ボタン群
        self.create_result_buttons()
        
        # グリッド設定
        self.frame.columnconfigure(0, weight=1)
    
    def create_result_buttons(self):
        """結果操作ボタン群作成"""
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=1, column=0, columnspan=5, sticky=(tk.W, tk.E))
        
        self.open_file_button = ttk.Button(
            button_frame, 
            text="📁 ファイルを開く", 
            command=self.open_result_file, 
            state='disabled'
        )
        self.open_file_button.grid(row=0, column=0, padx=(0, 10))
        
        self.open_folder_button = ttk.Button(
            button_frame, 
            text="📂 フォルダを開く", 
            command=self.open_result_folder, 
            state='disabled'
        )
        self.open_folder_button.grid(row=0, column=1, padx=(0, 10))
        
        self.analyze_button = ttk.Button(
            button_frame, 
            text="📤 Claudeで分析", 
            command=self.analyze_with_claude, 
            state='disabled'
        )
        self.analyze_button.grid(row=0, column=2, padx=(0, 10))
        
        self.comment_analysis_button = ttk.Button(
            button_frame, 
            text="💬 コメント分析", 
            command=self.analyze_comments, 
            state='disabled'
        )
        self.comment_analysis_button.grid(row=0, column=3, padx=(0, 10))
        
        self.screenshot_folder_button = ttk.Button(
            button_frame, 
            text="📷 スクリーンショット表示", 
            command=self.open_screenshot_folder, 
            state='disabled'
        )
        self.screenshot_folder_button.grid(row=0, column=4, padx=(0, 10))
    
    def set_result(self, file_path, **kwargs):
        """結果設定"""
        self.result_file_path = file_path
        self.video_file_path = kwargs.get('video_file_path')
        self.screenshot_files = kwargs.get('screenshot_files')
        self.summary_file = kwargs.get('summary_file')
        self.comments_file_path = kwargs.get('comments_file_path')
        
        # 結果表示更新
        if file_path:
            filename = os.path.basename(file_path)
            result_text = f"保存先: {filename}"
            
            # 追加情報表示
            if self.screenshot_files:
                result_text += f" (+{len(self.screenshot_files)}枚のスクリーンショット)"
            if self.video_file_path:
                result_text += " + 動画ファイル"
            
            self.result_label.config(text=result_text)
            
            # ボタン有効化
            self.open_file_button.config(state='normal')
            self.open_folder_button.config(state='normal')
            self.analyze_button.config(state='normal')
            
            # 条件付きボタン有効化
            if self.screenshot_files:
                self.screenshot_folder_button.config(state='normal')
            
            if self.comments_file_path and os.path.exists(self.comments_file_path):
                self.comment_analysis_button.config(state='normal')
    
    def open_result_file(self):
        """結果ファイルを開く"""
        if self.result_file_path and os.path.exists(self.result_file_path):
            os.startfile(self.result_file_path)
        else:
            messagebox.showerror("エラー", "ファイルが見つかりません")

    def open_result_folder(self):
        """結果フォルダを開く"""
        if self.result_file_path:
            folder_path = os.path.dirname(self.result_file_path)
            if os.path.exists(folder_path):
                os.startfile(folder_path)
                self.main_app.log_message(f"フォルダを開きました: {folder_path}")
            else:
                messagebox.showerror("エラー", "フォルダが見つかりません")

    def open_screenshot_folder(self):
        """スクリーンショットフォルダを開く"""
        if self.screenshot_files and len(self.screenshot_files) > 0:
            folder_path = os.path.dirname(self.screenshot_files[0])
            
            # 絶対パスに変換
            if not os.path.isabs(folder_path):
                folder_path = os.path.abspath(folder_path)
            
            self.main_app.log_message(f"フォルダパス: {folder_path}")
            
            if os.path.exists(folder_path):
                os.startfile(folder_path)
                self.main_app.log_message(f"スクリーンショットフォルダを開きました: {folder_path}")
            else:
                self.main_app.log_message(f"フォルダが見つかりません: {folder_path}")
        else:
            self.main_app.log_message("スクリーンショットファイルが存在しません")

    def analyze_with_claude(self):
        """Claudeで分析"""
        if not self.result_file_path:
            messagebox.showerror("エラー", "分析するファイルがありません")
            return
        
        self.main_app.analysis_handler.analyze_with_claude(self.result_file_path)

    def analyze_comments(self):
        """YouTubeコメント分析"""
        if not self.comments_file_path or not os.path.exists(self.comments_file_path):
            messagebox.showerror("エラー", "分析するコメントファイルがありません")
            return
        
        self.main_app.analysis_handler.analyze_comments(self.comments_file_path)
    
    def get_all_buttons(self):
        """全ての結果ボタンを取得"""
        return [
            self.open_file_button,
            self.open_folder_button,
            self.analyze_button,
            self.comment_analysis_button,
            self.screenshot_folder_button
        ]