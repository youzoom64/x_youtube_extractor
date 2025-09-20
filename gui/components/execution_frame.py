"""
実行ボタンフレーム
"""
import tkinter as tk
from tkinter import ttk

class ExecutionFrame:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.create_frame()
        
    def create_frame(self):
        """実行ボタンフレーム作成"""
        
        # 実行ボタンフレーム
        self.frame = ttk.LabelFrame(self.parent, text="🚀 実行", padding="10")
        self.frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # プログレスバー
        self.create_progress_bar()
        
        # 実行ボタン群
        self.create_execution_buttons()
        
        # 状態表示
        self.create_status_display()
    
    def create_progress_bar(self):
        """プログレスバー作成"""
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.frame, 
            variable=self.progress_var, 
            maximum=100
        )
        self.progress_bar.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
    
    def create_execution_buttons(self):
        """実行ボタン群作成"""
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=1, column=0, columnspan=4, pady=(0, 10))
        
        # 検索実行ボタン
        self.run_button = ttk.Button(
            button_frame, 
            text="🔍 検索実行", 
            command=self.main_app.scraping_handler.run_scraping
        )
        self.run_button.grid(row=0, column=0, padx=(0, 10))
        
        # リプライ取得ボタン
        self.reply_button = ttk.Button(
            button_frame, 
            text="📥 リプライ取得", 
            command=self.main_app.scraping_handler.get_replies
        )
        self.reply_button.grid(row=0, column=1, padx=(0, 10))
        
        # 動画処理ボタン
        self.video_button = ttk.Button(
            button_frame, 
            text="🎬 動画処理", 
            command=self.main_app.media_handler.process_media
        )
        self.video_button.grid(row=0, column=2, padx=(0, 10))
        
        # 自動実行ボタン（スマート判定）
        self.auto_button = ttk.Button(
            button_frame, 
            text="🤖 自動実行", 
            command=self.auto_execute
        )
        self.auto_button.grid(row=0, column=3, padx=(0, 10))
    
    def create_status_display(self):
        """状態表示作成"""
        self.status_var = tk.StringVar(value="待機中...")
        self.status_label = ttk.Label(self.frame, textvariable=self.status_var)
        self.status_label.grid(row=2, column=0, columnspan=4, pady=(0, 10))
    
    def auto_execute(self):
        """自動実行（URL種別を判定して適切な処理を実行）"""
        if self.main_app.is_running:
            return
        
        from ..utils.validators import URLValidator
        from tkinter import messagebox
        
        url_text = self.main_app.settings_frame.query_var.get().strip()
        if not url_text:
            messagebox.showerror("エラー", "URL または検索クエリを入力してください")
            return
        
        try:
            if URLValidator.is_youtube_url(url_text):
                self.main_app.log_message("🎥 YouTube動画として処理します")
                self.main_app.media_handler.process_media()
            elif URLValidator.is_tweet_url(url_text):
                # ツイートURLの場合、リプライ取得かどうか確認
                response = messagebox.askyesno(
                    "確認", 
                    "ツイートURLが検出されました。\n\n"
                    "「はい」→ リプライ取得\n"
                    "「いいえ」→ 動画処理（動画がある場合）\n\n"
                    "リプライを取得しますか？"
                )
                if response:
                    self.main_app.log_message("📥 リプライ取得として処理します")
                    self.main_app.scraping_handler.get_replies()
                else:
                    self.main_app.log_message("🎬 動画処理として処理します")
                    self.main_app.media_handler.process_media()
            else:
                self.main_app.log_message("🔍 検索クエリとして処理します")
                self.main_app.scraping_handler.run_scraping()
                
        except Exception as e:
            messagebox.showerror("エラー", f"自動実行エラー: {e}")
    
    def get_all_buttons(self):
        """全ての実行ボタンを取得"""
        return [
            self.run_button,
            self.reply_button, 
            self.video_button,
            self.auto_button
        ]