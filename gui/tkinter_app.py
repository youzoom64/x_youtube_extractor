"""Tkinter GUI アプリケーション"""
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import sys
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflows.scrape_only import ScrapeOnlyWorkflow
from workflows.scrape_and_analyze import ScrapeAndAnalyzeWorkflow
from lib.utils import setup_logging, create_directories, validate_query

logger = logging.getLogger(__name__)

class TwitterScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Twitter スクレイピング + Claude 分析ツール")
        self.root.geometry("1100x900")
        
        # 実行中フラグ
        self.is_running = False
        
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
        
        # ===== 基本設定フレーム =====
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ 基本設定", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Chrome接続状態
        self.chrome_status_label = ttk.Label(settings_frame, text="Chrome接続状態: 確認中...")
        self.chrome_status_label.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # 共用URL/クエリ入力
        ttk.Label(settings_frame, text="URL / 検索クエリ:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.query_var = tk.StringVar()
        self.query_entry = ttk.Entry(settings_frame, textvariable=self.query_var, width=70)
        self.query_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # URL/クエリ種別表示
        self.url_type_label = ttk.Label(settings_frame, text="種別: 自動判定", foreground="blue")
        self.url_type_label.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        # URL/クエリ変更時の自動判定
        self.query_var.trace('w', self._on_url_change)
        
        # 取得件数（共用）
        ttk.Label(settings_frame, text="取得件数:").grid(row=3, column=0, sticky=tk.W, padx=(0, 10))
        self.count_var = tk.IntVar(value=20)
        count_frame = ttk.Frame(settings_frame)
        count_frame.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.count_scale = ttk.Scale(count_frame, from_=1, to=100, orient=tk.HORIZONTAL, 
                                    variable=self.count_var, length=300)
        self.count_scale.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.count_label = ttk.Label(count_frame, text="20")
        self.count_label.grid(row=0, column=1, padx=(10, 0))
        self.count_scale.configure(command=self.update_count_label)
        
        # 出力形式とソート順
        options_frame = ttk.Frame(settings_frame)
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
        
        # ===== スクリーンショット設定フレーム =====
        screenshot_frame = ttk.LabelFrame(main_frame, text="📸 スクリーンショット設定", padding="10")
        screenshot_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # スクリーンショット撮影オプション
        screenshot_options_frame = ttk.Frame(screenshot_frame)
        screenshot_options_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.screenshot_var = tk.BooleanVar(value=True)
        self.screenshot_checkbox = ttk.Checkbutton(screenshot_options_frame, text="📸 スクリーンショット撮影", 
                                                variable=self.screenshot_var, command=self.toggle_screenshot_options)
        self.screenshot_checkbox.grid(row=0, column=0, sticky=tk.W)
        
        self.exclude_promoted_var = tk.BooleanVar(value=False)
        self.exclude_promoted_checkbox = ttk.Checkbutton(screenshot_options_frame, text="🚫 プロモーション除外", 
                                                        variable=self.exclude_promoted_var)
        self.exclude_promoted_checkbox.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # スクリーンショット撮影モード
        ttk.Label(screenshot_frame, text="撮影モード:").grid(row=1, column=0, sticky=(tk.W, tk.N), padx=(0, 10))
        self.capture_mode_var = tk.StringVar(value="smart_batch")
        capture_mode_frame = ttk.Frame(screenshot_frame)
        capture_mode_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        self.smart_batch_radio = ttk.Radiobutton(capture_mode_frame, text="効率的一括撮影", 
                                                variable=self.capture_mode_var, value="smart_batch")
        self.smart_batch_radio.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        self.full_batch_radio = ttk.Radiobutton(capture_mode_frame, text="フルページ撮影", 
                                            variable=self.capture_mode_var, value="full_batch")
        self.full_batch_radio.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        self.individual_radio = ttk.Radiobutton(capture_mode_frame, text="個別アクセス（遅い）", 
                                            variable=self.capture_mode_var, value="individual")
        self.individual_radio.grid(row=0, column=2, sticky=tk.W)
        
        # ===== 動画・音声設定フレーム =====
        media_frame = ttk.LabelFrame(main_frame, text="🎥 動画・音声処理", padding="10")
        media_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # 動画処理オプション（第1行）
        media_options_frame1 = ttk.Frame(media_frame)
        media_options_frame1.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        self.translate_var = tk.BooleanVar(value=False)
        self.translate_checkbox = ttk.Checkbutton(media_options_frame1, text="🌐 英語翻訳", 
                                                variable=self.translate_var)
        self.translate_checkbox.grid(row=0, column=0, sticky=tk.W)

        self.timestamp_var = tk.BooleanVar(value=True)
        self.timestamp_checkbox = ttk.Checkbutton(media_options_frame1, text="⏰ タイムスタンプ付与", 
                                                variable=self.timestamp_var)
        self.timestamp_checkbox.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))

        self.download_video_var = tk.BooleanVar(value=True)
        self.download_video_checkbox = ttk.Checkbutton(media_options_frame1, text="📥 動画ダウンロード", 
                                                     variable=self.download_video_var)
        self.download_video_checkbox.grid(row=0, column=2, sticky=tk.W, padx=(20, 0))

        self.force_whisper_var = tk.BooleanVar(value=False)
        self.force_whisper_checkbox = ttk.Checkbutton(media_options_frame1, text="🎵 Whisper強制実行", 
                                                    variable=self.force_whisper_var)
        self.force_whisper_checkbox.grid(row=0, column=3, sticky=tk.W, padx=(20, 0))

        # Whisperモデル選択（第2行）
        media_options_frame2 = ttk.Frame(media_frame)
        media_options_frame2.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(media_options_frame2, text="Whisperモデル:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.whisper_model_var = tk.StringVar(value="base")
        whisper_combo = ttk.Combobox(media_options_frame2, textvariable=self.whisper_model_var, 
                                    values=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"], 
                                    width=12, state="readonly")
        whisper_combo.grid(row=0, column=1, sticky=tk.W)

        # モデル説明ラベル
        self.model_info_label = ttk.Label(media_options_frame2, text="精度: 中 | 速度: 高", foreground="blue")
        self.model_info_label.grid(row=0, column=2, sticky=tk.W, padx=(10, 0))

        # Whisperモデル変更時の説明更新
        whisper_combo.bind('<<ComboboxSelected>>', self._on_whisper_model_change)

        # 音声品質設定
        ttk.Label(media_options_frame2, text="音声品質:").grid(row=0, column=3, sticky=tk.W, padx=(20, 10))
        self.audio_quality_var = tk.StringVar(value="best")
        quality_combo = ttk.Combobox(media_options_frame2, textvariable=self.audio_quality_var,
                                    values=["best", "good", "medium"], width=8, state="readonly")
        quality_combo.grid(row=0, column=4, sticky=tk.W)

        # Claudeチャット URL
        ttk.Label(media_frame, text="ClaudeチャットURL (任意):").grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        self.claude_chat_url_var = tk.StringVar()
        self.claude_chat_url_entry = ttk.Entry(media_frame, textvariable=self.claude_chat_url_var, width=70)
        self.claude_chat_url_entry.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # ===== 実行ボタンフレーム =====
        exec_frame = ttk.LabelFrame(main_frame, text="🚀 実行", padding="10")
        exec_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        button_exec_frame = ttk.Frame(exec_frame)
        button_exec_frame.grid(row=0, column=0, columnspan=3)
        
        # 実行ボタン群
        self.run_button = ttk.Button(button_exec_frame, text="🔍 検索実行", command=self.run_scraping)
        self.run_button.grid(row=0, column=0, padx=(0, 10))
        
        self.reply_button = ttk.Button(button_exec_frame, text="📥 リプライ取得", command=self.get_replies)
        self.reply_button.grid(row=0, column=1, padx=(0, 10))
        
        self.video_button = ttk.Button(button_exec_frame, text="🎬 動画処理", command=self.process_media)
        self.video_button.grid(row=0, column=2, padx=(0, 10))
        
        # 自動実行ボタン（スマート判定）
        self.auto_button = ttk.Button(button_exec_frame, text="🤖 自動実行", command=self.auto_execute)
        self.auto_button.grid(row=0, column=3, padx=(0, 10))
        
        # ===== プログレスバー =====
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 5))
        
        # ===== 状態表示 =====
        self.status_var = tk.StringVar(value="待機中...")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.grid(row=6, column=0, columnspan=3, pady=(0, 10))
        
        # ===== ログ表示フレーム =====
        log_frame = ttk.LabelFrame(main_frame, text="📝 ログ", padding="10")
        log_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=18, width=90)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=3)  # ログフレームの比重を大きく
        
        # ===== 結果表示フレーム =====
        result_frame = ttk.LabelFrame(main_frame, text="📄 結果", padding="10")
        result_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.result_label = ttk.Label(result_frame, text="結果はここに表示されます")
        self.result_label.grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 10))
        
        # 結果操作ボタン群
        button_frame = ttk.Frame(result_frame)
        button_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E))
        
        self.open_file_button = ttk.Button(button_frame, text="📁 ファイルを開く", 
                                        command=self.open_result_file, state='disabled')
        self.open_file_button.grid(row=0, column=0, padx=(0, 10))
        
        self.open_folder_button = ttk.Button(button_frame, text="📂 フォルダを開く", 
                                            command=self.open_result_folder, state='disabled')
        self.open_folder_button.grid(row=0, column=1, padx=(0, 10))
        
        self.file_button = ttk.Button(button_frame, text="📤 Claudeで分析", 
                                    command=self.analyze_with_claude, state='disabled')
        self.file_button.grid(row=0, column=2, padx=(0, 10))
        
        self.comment_analysis_button = ttk.Button(button_frame, text="💬 コメント分析", 
                                                 command=self.analyze_comments, state='disabled')
        self.comment_analysis_button.grid(row=0, column=3, padx=(0, 10))
        
        self.screenshot_folder_button = ttk.Button(button_frame, text="📷 スクリーンショット表示", 
                                                command=self.open_screenshot_folder, state='disabled')
        self.screenshot_folder_button.grid(row=0, column=4, padx=(0, 10))
        
        # ===== グリッド設定 =====
        # メインフレームの設定
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)  # ログフレームを拡張可能に
        
        # 各フレームの設定
        settings_frame.columnconfigure(1, weight=1)
        count_frame.columnconfigure(0, weight=1)
        screenshot_frame.columnconfigure(1, weight=1)
        media_frame.columnconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # ルートウィンドウの設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def update_count_label(self, value):
        """カウントラベルを更新"""
        self.count_label.config(text=str(int(float(value))))
    
    def toggle_screenshot_options(self):
        """スクリーンショットオプションの有効/無効切り替え"""
        if self.screenshot_var.get():
            self.smart_batch_radio.config(state='normal')
            self.full_batch_radio.config(state='normal')
            self.individual_radio.config(state='normal')
        else:
            self.smart_batch_radio.config(state='disabled')
            self.full_batch_radio.config(state='disabled')
            self.individual_radio.config(state='disabled')
    
    def check_chrome_connection(self):
        """Chrome接続確認"""
        def check():
            try:
                import requests
                response = requests.get("http://localhost:9222/json", timeout=5)
                if response.status_code == 200:
                    self.chrome_status_label.config(text="Chrome接続状態: ✅ 接続OK", foreground="green")
                else:
                    self.chrome_status_label.config(text="Chrome接続状態: ❌ 接続エラー", foreground="red")
            except:
                self.chrome_status_label.config(text="Chrome接続状態: ❌ デバッグモードで起動してください", foreground="red")
        
        threading.Thread(target=check, daemon=True).start()
    
    def log_message(self, message):
        """ログメッセージを追加"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def _is_tweet_url(self, text):
        """入力がツイートURLかどうか判定"""
        return ('x.com' in text or 'twitter.com' in text) and '/status/' in text
    
    def run_scraping(self):
        """スクレイピング実行"""
        if self.is_running:
            return
        
        query = self.query_var.get().strip()
        if not query:
            messagebox.showerror("エラー", "検索クエリを入力してください")
            return
        
        # ツイートURLの場合はリプライ取得を提案
        if self._is_tweet_url(query):
            response = messagebox.askyesno(
                "確認", 
                "ツイートURLが入力されています。\n\n"
                "「はい」→ リプライ取得\n"
                "「いいえ」→ 通常の検索実行\n\n"
                "リプライを取得しますか？"
            )
            if response:
                self.get_replies()
                return
        
        # 入力チェック
        is_valid, error_msg = validate_query(query)
        if not is_valid:
            messagebox.showerror("エラー", error_msg)
            return
        
        # UI状態更新
        self.is_running = True
        self.run_button.config(state='disabled')
        self.reply_button.config(state='disabled')
        self.progress_var.set(0)
        self.log_text.delete(1.0, tk.END)
        
        # 別スレッドで実行
        thread = threading.Thread(target=self._run_scraping_thread, daemon=True)
        thread.start()

    def _run_scraping_thread(self):
        """スクレイピング実行スレッド"""
        try:
            query = self.query_var.get().strip()
            count = int(self.count_var.get())
            format_type = self.format_var.get()
            sort_type = self.sort_var.get()
            screenshot_enabled = self.screenshot_var.get()
            capture_mode = self.capture_mode_var.get()
            
            # 初期設定
            setup_logging("INFO")
            create_directories()
            
            self.log_message("処理開始...")
            self.status_var.set("Chrome接続中...")
            self.progress_var.set(10)
            
            # ワークフロー実行
            if screenshot_enabled:
                from workflows.scrape_with_screenshots import ScrapeWithScreenshotsWorkflow
                self.log_message("スクリーンショット撮影モードで実行")
                workflow = ScrapeWithScreenshotsWorkflow()
                self.status_var.set("ツイート取得＋スクリーンショット撮影中...")
                self.progress_var.set(30)
                
                txt_file, screenshot_files, summary_file = workflow.execute(
                    query, count, format_type, sort_type, capture_mode
                )
                
                self.progress_var.set(100)
                
                if txt_file and screenshot_files:
                    self.result_file_path = txt_file
                    self.screenshot_files = screenshot_files
                    self.summary_file = summary_file
                    
                    filename = os.path.basename(txt_file)
                    self.result_label.config(text=f"保存先: {filename} (+{len(screenshot_files)}枚のスクリーンショット)")
                    
                    # ボタン有効化
                    self.open_file_button.config(state='normal')
                    self.open_folder_button.config(state='normal')
                    self.file_button.config(state='normal')
                    self.screenshot_folder_button.config(state='normal')
                    
                    self.log_message(f"✅ 処理完了: {txt_file}")
                    self.log_message(f"📸 スクリーンショット: {len(screenshot_files)}枚")
                    self.status_var.set("完了!")
                    messagebox.showinfo("完了", f"処理が完了しました\nテキスト: {txt_file}\nスクリーンショット: {len(screenshot_files)}枚")
                else:
                    self.log_message("❌ 処理に失敗しました")
                    self.status_var.set("失敗")
                    messagebox.showerror("エラー", "処理に失敗しました")
                    
            else:
                # 通常のスクレイピングのみ
                from workflows.scrape_only import ScrapeOnlyWorkflow
                self.log_message("通常モードで実行")
                workflow = ScrapeOnlyWorkflow()
                self.status_var.set("ツイート取得中...")
                self.progress_var.set(50)
                
                result = workflow.execute(query, count, format_type, sort_type)
                self.progress_var.set(100)
                
                if result:
                    self.log_message(f"✅ 処理完了: {result}")
                    self.status_var.set("完了!")
                    
                    filename = os.path.basename(result)
                    self.result_label.config(text=f"保存先: {filename}")
                    
                    # ボタン有効化
                    self.open_file_button.config(state='normal')
                    self.open_folder_button.config(state='normal')
                    self.file_button.config(state='normal')
                    
                    self.result_file_path = result
                    messagebox.showinfo("完了", f"処理が完了しました\n保存先: {result}")
                else:
                    self.log_message("❌ 処理に失敗しました")
                    self.status_var.set("失敗")
                    messagebox.showerror("エラー", "処理に失敗しました")
                
        except Exception as e:
            self.log_message(f"❌ エラー: {e}")
            self.status_var.set("エラー")
            messagebox.showerror("エラー", f"エラーが発生しました: {e}")
        finally:
            self.is_running = False
            self.run_button.config(state='normal')
            self.reply_button.config(state='normal')

    def get_replies(self):
        """リプライ取得実行"""
        if self.is_running:
            return
        
        tweet_url = self.query_var.get().strip()  # 共用フィールドから取得
        if not tweet_url:
            messagebox.showerror("エラー", "ツイートURLを入力してください")
            return
        
        # URL検証
        if not self._is_tweet_url(tweet_url):
            messagebox.showerror("エラー", "有効なツイートURLを入力してください\n例: https://x.com/username/status/1234567890")
            return
        
        # UI状態更新
        self.is_running = True
        self.run_button.config(state='disabled')
        self.reply_button.config(state='disabled')
        self.progress_var.set(0)
        self.log_text.delete(1.0, tk.END)
        
        # 別スレッドで実行
        thread = threading.Thread(target=self._get_replies_thread, daemon=True)
        thread.start()

    def _get_replies_thread(self):
        """リプライ取得スレッド"""
        try:
            tweet_url = self.query_var.get().strip()  # 共用フィールドから取得
            count = int(self.count_var.get())  # 共用の件数を使用
            format_type = self.format_var.get()
            screenshot_enabled = self.screenshot_var.get()
            capture_mode = self.capture_mode_var.get()
            
            # 初期設定
            setup_logging("INFO")
            create_directories()
            
            self.log_message("リプライ取得開始...")
            self.status_var.set("Chrome接続中...")
            self.progress_var.set(10)
            
            # ワークフロー実行（スクリーンショット対応）
            if screenshot_enabled:
                from workflows.scrape_replies_with_screenshots import ScrapeRepliesWithScreenshotsWorkflow
                self.log_message("リプライ + スクリーンショット撮影モードで実行")
                workflow = ScrapeRepliesWithScreenshotsWorkflow()
                self.status_var.set("リプライ取得＋スクリーンショット撮影中...")
                self.progress_var.set(30)
                
                txt_file, screenshot_files, summary_file = workflow.execute(
                    tweet_url, count, format_type, capture_mode
                )
                
                self.progress_var.set(100)
                
                if txt_file and screenshot_files:
                    self.result_file_path = txt_file
                    self.screenshot_files = screenshot_files
                    self.summary_file = summary_file
                    
                    filename = os.path.basename(txt_file)
                    self.result_label.config(text=f"リプライ保存先: {filename} (+{len(screenshot_files)}枚のスクリーンショット)")
                    
                    # ボタン有効化
                    self.open_file_button.config(state='normal')
                    self.open_folder_button.config(state='normal')
                    self.file_button.config(state='normal')
                    self.screenshot_folder_button.config(state='normal')
                    
                    self.log_message(f"✅ リプライ取得完了: {txt_file}")
                    self.log_message(f"📸 スクリーンショット: {len(screenshot_files)}枚")
                    self.status_var.set("完了!")
                    messagebox.showinfo("完了", f"リプライ取得が完了しました\nテキスト: {txt_file}\nスクリーンショット: {len(screenshot_files)}枚")
                else:
                    self.log_message("❌ リプライ取得に失敗しました")
                    self.status_var.set("失敗")
                    messagebox.showerror("エラー", "リプライ取得に失敗しました")
            else:
                # 通常のリプライ取得のみ
                from workflows.scrape_replies import ScrapeRepliesWorkflow
                workflow = ScrapeRepliesWorkflow()
                self.status_var.set("リプライ取得中...")
                self.progress_var.set(30)
                
                result = workflow.execute(tweet_url, count, format_type)
                self.progress_var.set(100)
                
                if result:
                    self.log_message(f"✅ リプライ取得完了: {result}")
                    self.status_var.set("完了!")
                    
                    filename = os.path.basename(result)
                    self.result_label.config(text=f"リプライ保存先: {filename}")
                    
                    # ボタンを有効化
                    self.open_file_button.config(state='normal')
                    self.open_folder_button.config(state='normal')
                    self.file_button.config(state='normal')
                    
                    self.result_file_path = result
                    messagebox.showinfo("完了", f"リプライ取得が完了しました\n保存先: {result}")
                else:
                    self.log_message("❌ リプライ取得に失敗しました")
                    self.status_var.set("失敗")
                    messagebox.showerror("エラー", "リプライ取得に失敗しました")
                
        except Exception as e:
            self.log_message(f"❌ エラー: {e}")
            self.status_var.set("エラー")
            messagebox.showerror("エラー", f"エラーが発生しました: {e}")
        finally:
            self.is_running = False
            self.run_button.config(state='normal')
            self.reply_button.config(state='normal')

    def open_result_file(self):
        """結果ファイルを開く"""
        if hasattr(self, 'result_file_path'):
            os.startfile(self.result_file_path)

    def open_result_folder(self):
        """結果フォルダを開く"""
        if hasattr(self, 'result_file_path'):
            folder_path = os.path.dirname(self.result_file_path)
            os.startfile(folder_path)
            self.log_message(f"フォルダを開きました: {folder_path}")

    def open_screenshot_folder(self):
        """スクリーンショットフォルダを開く"""
        if hasattr(self, 'screenshot_files') and self.screenshot_files:
            folder_path = os.path.dirname(self.screenshot_files[0])
            os.startfile(folder_path)
            self.log_message(f"スクリーンショットフォルダを開きました: {folder_path}")
        else:
            messagebox.showinfo("情報", "スクリーンショットがありません。先にスクリーンショット撮影を実行してください。")

    def analyze_with_claude(self):
        """既存ファイルをClaudeで分析"""
        if hasattr(self, 'result_file_path'):
            # 分析プロンプト入力ダイアログ（修正版）
            dialog = tk.Toplevel(self.root)
            dialog.title("Claude分析プロンプト")
            dialog.geometry("600x400")
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
            
            frame = ttk.Frame(dialog, padding="10")
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text="分析内容を指定してください:", font=("Arial", 12)).pack(pady=(0, 10))
            
            text_area = tk.Text(frame, height=15, width=70, font=("Arial", 11), wrap=tk.WORD)
            text_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            default_text = """この内容を分析してください。

    【分析してほしい内容】
    1. 全体的な傾向と特徴
    2. 主要なポイント・キーワード
    3. エンゲージメントの高い内容の特徴
    4. 要約（3-5行程度）

    【出力形式】
    - 簡潔で分かりやすく
    - 具体的な数値や例を含めて
    - 実用的な洞察を提供"""
            
            text_area.insert(tk.END, default_text)
            text_area.focus()
            
            button_frame = ttk.Frame(frame)
            button_frame.pack(pady=(10, 0))
            
            result = [None]
            
            def ok_clicked():
                # 修正: get("1.0", tk.END) で全てのテキストを取得
                result[0] = text_area.get("1.0", tk.END).strip()
                dialog.destroy()
            
            def cancel_clicked():
                result[0] = None
                dialog.destroy()
            
            ttk.Button(button_frame, text="OK", command=ok_clicked).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(button_frame, text="キャンセル", command=cancel_clicked).pack(side=tk.LEFT)
            
            def on_key(event):
                if event.state & 0x4 and event.keysym == 'Return':  # Ctrl+Enter
                    ok_clicked()
                    return 'break'
            
            text_area.bind('<Key>', on_key)
            dialog.wait_window()
            
            prompt = result[0]
            if prompt is None or prompt == "":
                return  # キャンセル時は何もしない
                
            thread = threading.Thread(
                target=self._claude_analysis_thread,
                args=(self.result_file_path, prompt),
                daemon=True
            )
            thread.start()
        else:
            self.log_message("❌ 分析するファイルがありません。先にメディア処理を実行してください。")

    def _claude_analysis_thread(self, file_path, prompt):
        """Claude分析スレッド（ファイルアップロード版、URL自動取得対応）"""
        try:
            from lib.claude_automation import ClaudeAutomation
            from lib.chrome_connector import ChromeConnector
            
            self.log_message("Claude ファイルアップロード分析開始...")
            self.status_var.set("Claudeでファイル分析中...")
            
            # Chrome接続してClaude自動操作
            chrome = ChromeConnector()
            if not chrome.connect():
                self.log_message("❌ Chrome接続に失敗しました")
                return
            
            claude = ClaudeAutomation(chrome)
            
            # 入力されたClaudeチャットURLを使用
            claude_chat_url = self.claude_chat_url_var.get().strip() if hasattr(self, 'claude_chat_url_var') else None
            result, chat_url = claude.upload_and_analyze_file(file_path, prompt, chat_url=(claude_chat_url if claude_chat_url else None))
            
            if result:
                self.log_message(f"✅ Claude分析完了")
                self.status_var.set("Claude分析完了")
                
                # 分析結果を保存（transcription.txtと同じフォルダ）
                try:
                    import os
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    base_dir = os.path.dirname(file_path)
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    analysis_file = os.path.join(base_dir, f"{timestamp}_{base_name}_claude_analysis.txt")
                    with open(analysis_file, 'w', encoding='utf-8') as f:
                        f.write(f"元ファイル: {file_path}\n")
                        if chat_url:
                            f.write(f"Claude URL: {chat_url}\n")
                        f.write(f"分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write("=" * 50 + "\n\n")
                        f.write("【Claude分析結果】\n")
                        f.write(result)
                    self.log_message(f"Claude分析結果保存: {analysis_file}")
                except Exception as e:
                    self.log_message(f"Claude分析結果保存エラー: {e}")
                
                # Claude URLを自動入力
                if chat_url and hasattr(self, 'claude_chat_url_var'):
                    self.claude_chat_url_var.set(chat_url)
                    self.log_message(f"🔗 Claude URL自動設定: {chat_url}")
                
                messagebox.showinfo("完了", f"Claude分析が完了しました\nClaude URLも自動設定されました")
            else:
                self.log_message("❌ Claude分析失敗")
                self.status_var.set("Claude分析失敗")
                messagebox.showerror("エラー", "Claude分析に失敗しました")
                
        except Exception as e:
            self.log_message(f"❌ Claude分析エラー: {e}")
            self.status_var.set("エラー")
            messagebox.showerror("エラー", f"Claude分析エラー: {e}")
        finally:
            # ボタンを再有効化
            self.file_button.config(state='normal')

    def analyze_comments(self):
        """YouTubeコメント分析実行"""
        if not hasattr(self, 'comments_file_path') or not self.comments_file_path:
            self.log_message("❌ 分析するコメントファイルがありません。先にYouTube動画の処理を実行してください。")
            return
        
        if not os.path.exists(self.comments_file_path):
            self.log_message("❌ コメントファイルが見つかりません。")
            return
        
        # ボタンを無効化
        self.comment_analysis_button.config(state='disabled')
        
        # 別スレッドでコメント分析を実行
        thread = threading.Thread(
            target=self._comment_analysis_thread,
            args=(self.comments_file_path,),
            daemon=True
        )
        thread.start()

    def _comment_analysis_thread(self, comments_file_path):
        """コメント分析スレッド"""
        try:
            from lib.claude_automation import ClaudeAutomation
            from lib.chrome_connector import ChromeConnector
            
            self.log_message("YouTubeコメント分析開始...")
            self.status_var.set("Claudeでコメント分析中...")
            
            # Chrome接続してClaude自動操作
            chrome = ChromeConnector()
            if not chrome.connect():
                self.log_message("❌ Chrome接続に失敗しました")
                return
            
            claude = ClaudeAutomation(chrome)
            
            # 入力されたClaudeチャットURLを使用
            claude_chat_url = self.claude_chat_url_var.get().strip() if hasattr(self, 'claude_chat_url_var') else None
            
            self.log_message("🔄 Claude分析処理を実行中...")
            result, chat_url = claude.analyze_comments(comments_file_path, chat_url=(claude_chat_url if claude_chat_url else None))
            
            # デバッグ情報をログ出力
            self.log_message(f"🔍 分析結果検証: result={'有' if result else '無'}, chat_url={'有' if chat_url else '無'}")
            if result:
                self.log_message(f"🔍 結果の長さ: {len(result.strip())} 文字")
                self.log_message(f"🔍 結果の先頭: {result.strip()[:200]}...")
            
            # 結果の詳細チェック（偽の成功を防ぐ）
            if result and len(result.strip()) > 50 and "分析" in result:
                self.log_message(f"✅ コメント分析完了")
                self.status_var.set("コメント分析完了")
                
                # コメント分析結果を保存（コメントファイルと同じフォルダ）
                try:
                    import os
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    base_dir = os.path.dirname(comments_file_path)
                    analysis_file = os.path.join(base_dir, f"{timestamp}_youtube_comments_claude_analysis.txt")
                    with open(analysis_file, 'w', encoding='utf-8') as f:
                        f.write(f"コメントファイル: {comments_file_path}\n")
                        if chat_url:
                            f.write(f"Claude URL: {chat_url}\n")
                        f.write(f"分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write("=" * 50 + "\n\n")
                        f.write("【Claudeコメント分析結果】\n")
                        f.write(result)
                    self.log_message(f"コメント分析結果保存: {analysis_file}")
                except Exception as e:
                    self.log_message(f"コメント分析結果保存エラー: {e}")
                
                # Claude URLを自動入力
                if chat_url and hasattr(self, 'claude_chat_url_var'):
                    self.claude_chat_url_var.set(chat_url)
                    self.log_message(f"🔗 Claude URL自動設定: {chat_url}")
                
                # UI更新を安全に実行（メインスレッドで実行）
                self.root.after(0, lambda: messagebox.showinfo("完了", f"YouTubeコメント分析が完了しました\nClaude URLも自動設定されました"))
            else:
                self.log_message("❌ コメント分析失敗（結果が無効または不完全）")
                self.status_var.set("コメント分析失敗")
                # デバッグ情報をログに出力
                if result:
                    self.log_message(f"📝 取得した結果: {result[:100]}...")
                else:
                    self.log_message("📝 結果がNullまたは空文字")
                self.root.after(0, lambda: messagebox.showerror("エラー", "コメント分析に失敗しました\n（結果が無効または不完全）"))
                
        except Exception as e:
            self.log_message(f"❌ コメント分析エラー: {e}")
            self.status_var.set("エラー")
            # エラーメッセージボックスもメインスレッドで実行
            self.root.after(0, lambda: messagebox.showerror("エラー", f"コメント分析エラー: {e}"))
        finally:
            # ボタンを再有効化
            self.comment_analysis_button.config(state='normal')

    # 新しいメソッドを追加
    def process_video(self):
        """動画文字おこし実行"""
        if self.is_running:
            return
        
        video_url = self.video_url_var.get().strip()
        if not video_url:
            messagebox.showerror("エラー", "動画ツイートURLを入力してください")
            return
        
        # URL検証
        if not self._is_tweet_url(video_url):
            messagebox.showerror("エラー", "有効なツイートURLを入力してください")
            return
        
        # UI状態更新
        self.is_running = True
        self.video_button.config(state='disabled')
        self.progress_var.set(0)
        self.log_text.delete(1.0, tk.END)
        
        # 別スレッドで実行
        thread = threading.Thread(target=self._process_video_thread, daemon=True)
        thread.start()

    def _process_video_thread(self):
        """動画処理スレッド"""
        try:
            video_url = self.video_url_var.get().strip()
            translate = self.translate_var.get()
            whisper_model = self.whisper_model_var.get()
            claude_chat_url = self.claude_chat_url_var.get().strip()
            
            # 初期設定
            setup_logging("INFO")
            create_directories()
            
            self.log_message("動画文字おこし開始...")
            self.status_var.set("動画ダウンロード中...")
            self.progress_var.set(10)
            
            # ワークフロー実行
            from workflows.video_transcription import VideoTranscriptionWorkflow
            workflow = VideoTranscriptionWorkflow()
            
            self.progress_var.set(30)
            video_path, text_file, transcription_text, translation = workflow.execute(
                video_url, translate, "en", whisper_model
            )
            
            self.progress_var.set(70)
            
            if transcription_text:
                # ログに文字おこし結果を表示
                self.log_message("=== 文字おこし結果 ===")
                lines = transcription_text.split('\n')
                for line in lines[:10]:  # 最初の10行のみログに表示
                    if line.strip():
                        self.log_message(f"📝 {line.strip()}")
                if len(lines) > 10:
                    self.log_message(f"... （続きは保存ファイルを確認）")
                
                if translation:
                    self.log_message("=== 翻訳結果（英語） ===")
                    trans_lines = translation.split('\n')
                    for line in trans_lines[:5]:
                        if line.strip():
                            self.log_message(f"🌐 {line.strip()}")
                
                # Claude分析（オプション）
                claude_analysis = None
                if messagebox.askyesno("Claude分析", "この文字おこし結果をClaude分析しますか？"):
                    try:
                        from lib.claude_automation import ClaudeAutomation
                        claude = ClaudeAutomation(workflow.chrome)
                        
                        self.log_message("Claude分析開始...")
                        self.status_var.set("Claude分析中...")
                        
                        claude_analysis = claude.analyze_transcription(
                            transcription_text, 
                            chat_url=claude_chat_url if claude_chat_url else None
                        )
                        
                        if claude_analysis:
                            self.log_message("=== Claude分析結果 ===")
                            analysis_lines = claude_analysis.split('\n')
                            for line in analysis_lines[:8]:
                                if line.strip():
                                    self.log_message(f"🤖 {line.strip()}")
                            
                            # 分析結果も保存
                            if text_file:
                                analysis_file = text_file.replace('.txt', '_claude_analysis.txt')
                                with open(analysis_file, 'w', encoding='utf-8') as f:
                                    f.write(f"Claude分析結果\n")
                                    f.write(f"分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                                    f.write("=" * 50 + "\n\n")
                                    f.write(claude_analysis)
                                self.log_message(f"Claude分析結果保存: {analysis_file}")
                        
                    except Exception as e:
                        self.log_message(f"Claude分析エラー: {e}")
                
                self.progress_var.set(100)
                
                # 結果表示
                if text_file:
                    self.result_file_path = text_file
                    self.video_file_path = video_path
                    
                    filename = os.path.basename(text_file)
                    result_text = f"文字おこし保存先: {filename}"
                    if video_path:
                        result_text += f" + 動画ファイル"
                    
                    self.result_label.config(text=result_text)
                    
                    # ボタン有効化
                    self.open_file_button.config(state='normal')
                    self.open_folder_button.config(state='normal')
                    self.file_button.config(state='normal')
                    
                    self.log_message(f"✅ 動画処理完了: {text_file}")
                    self.status_var.set("完了!")
                    messagebox.showinfo("完了", f"動画文字おこしが完了しました\n保存先: {text_file}")
                else:
                    self.log_message("❌ 処理に失敗しました")
                    self.status_var.set("失敗")
                    messagebox.showerror("エラー", "動画処理に失敗しました")
            else:
                self.log_message("❌ 文字おこしに失敗しました")
                self.status_var.set("失敗")
                messagebox.showerror("エラー", "文字おこしに失敗しました")
                
        except Exception as e:
            self.log_message(f"❌ エラー: {e}")
            self.status_var.set("エラー")
            messagebox.showerror("エラー", f"エラーが発生しました: {e}")
        finally:
            self.is_running = False
            self.video_button.config(state='normal')

    def _on_url_change(self, *args):
        """URL/クエリ変更時の自動判定"""
        try:
            url_text = self.query_var.get().strip()
            
            if not url_text:
                self.url_type_label.config(text="種別: 自動判定", foreground="blue")
                return
            
            if self._is_youtube_url(url_text):
                self.url_type_label.config(text="種別: YouTube動画", foreground="red")
            elif self._is_tweet_url(url_text):
                self.url_type_label.config(text="種別: ツイート", foreground="green")
            else:
                self.url_type_label.config(text="種別: 検索クエリ", foreground="purple")
                
        except Exception as e:
            self.url_type_label.config(text="種別: 不明", foreground="gray")

    def _is_youtube_url(self, text):
        """YouTubeURLかどうか判定"""
        youtube_patterns = [
            'youtube.com/watch',
            'youtu.be/',
            'm.youtube.com',
            'youtube.com/shorts',
            'youtube.com/embed'
        ]
        return any(pattern in text.lower() for pattern in youtube_patterns)

    def auto_execute(self):
        """自動実行（URL種別を判定して適切な処理を実行）"""
        if self.is_running:
            return
        
        url_text = self.query_var.get().strip()
        if not url_text:
            messagebox.showerror("エラー", "URL または検索クエリを入力してください")
            return
        
        try:
            if self._is_youtube_url(url_text):
                self.log_message("🎥 YouTube動画として処理します")
                self.process_media()
            elif self._is_tweet_url(url_text):
                # ツイートURLの場合、リプライ取得かどうか確認
                response = messagebox.askyesno(
                    "確認", 
                    "ツイートURLが検出されました。\n\n"
                    "「はい」→ リプライ取得\n"
                    "「いいえ」→ 動画処理（動画がある場合）\n\n"
                    "リプライを取得しますか？"
                )
                if response:
                    self.log_message("📥 リプライ取得として処理します")
                    self.get_replies()
                else:
                    self.log_message("🎬 動画処理として処理します")
                    self.process_media()
            else:
                self.log_message("🔍 検索クエリとして処理します")
                self.run_scraping()
                
        except Exception as e:
            messagebox.showerror("エラー", f"自動実行エラー: {e}")

    def process_media(self):
        """統合メディア処理（非同期版・スレッドなし）"""
        if self.is_running:
            return
        
        url_text = self.query_var.get().strip()
        if not url_text:
            self.log_message("❌ 動画URLを入力してください")
            return
        
        # URL検証
        if not (self._is_tweet_url(url_text) or self._is_youtube_url(url_text)):
            self.log_message("❌ 有効なツイートURL または YouTubeURL を入力してください")
            return
        
        # UI状態更新
        self.is_running = True
        self.video_button.config(state='disabled')
        self.progress_var.set(0)
        self.log_text.delete(1.0, tk.END)
        
        # 非同期で段階的に実行
        self.root.after(100, self._start_media_processing, url_text)

    def _start_media_processing(self, url_text):
        """メディア処理開始（非同期実行）"""
        try:
            translate = self.translate_var.get()
            use_timestamps = self.timestamp_var.get()
            whisper_model = self.whisper_model_var.get()
            audio_quality = self.audio_quality_var.get()
            download_video = self.download_video_var.get()
            force_whisper = self.force_whisper_var.get()
            
            # 初期設定
            setup_logging("INFO")
            create_directories()
            
            self.log_message("メディア処理開始...")
            self.log_message(f"Whisperモデル: {whisper_model}")
            
            if self._is_youtube_url(url_text):
                self.log_message("🎥 YouTube動画を処理中...")
                self.status_var.set("YouTube動画ダウンロード中...")
            else:
                self.log_message("🐦 ツイート動画を処理中...")
                self.status_var.set("ツイート動画ダウンロード中...")
            
            self.progress_var.set(10)
            
            # 統合動画処理ワークフロー実行（同期処理）
            from workflows.universal_media_transcription import UniversalMediaTranscriptionWorkflow
            workflow = UniversalMediaTranscriptionWorkflow()
            
            self.progress_var.set(30)
            self.log_message("🎤 Whisper文字おこし開始...")
            self.status_var.set("文字おこし処理中...")
            
            # 同期実行（スレッドなし）
            # 既存の件数スライダーを YouTubeコメント取得数に流用
            comment_count = int(self.count_var.get())

            video_path, text_file, transcription_text, translation = workflow.execute_with_callback(
                url_text, translate, "en", whisper_model, audio_quality, use_timestamps,
                progress_callback=None, comment_count=comment_count, download_video=download_video,
                force_whisper=force_whisper
            )
            
            self.progress_var.set(100)
            
            # 結果処理
            if transcription_text and text_file:
                self.log_message("✅ 文字おこし完了！")
                
                # 統計情報
                lines = transcription_text.split('\n')
                text_lines = [line for line in lines if line.strip()]
                
                self.log_message(f"📊 統計情報:")
                self.log_message(f"   - 総行数: {len(text_lines)}")
                self.log_message(f"   - 文字数: {len(transcription_text)}")
                
                # 結果設定
                self.result_file_path = text_file
                self.video_file_path = video_path
                
                # コメントファイルパスを設定（YouTubeの場合）
                self.comments_file_path = None
                if self._is_youtube_url(url_text) and text_file:
                    output_dir = os.path.dirname(text_file)
                    comments_path = os.path.join(output_dir, "youtube_comments.jsonl")
                    if os.path.exists(comments_path):
                        self.comments_file_path = comments_path
                        self.log_message(f"📝 コメントファイル検出: {os.path.basename(comments_path)}")
                
                filename = os.path.basename(text_file)
                platform = "YouTube" if self._is_youtube_url(url_text) else "Twitter"
                result_text = f"{platform}文字おこし完了: {filename}"
                
                self.result_label.config(text=result_text)
                
                # ボタン有効化
                self.open_file_button.config(state='normal')
                self.open_folder_button.config(state='normal')
                self.file_button.config(state='normal')
                
                # コメントファイルがあればコメント分析ボタンも有効化
                if self.comments_file_path:
                    self.comment_analysis_button.config(state='normal')
                    self.log_message("💬 コメント分析ボタンが有効になりました")
                
                self.log_message(f"🎉 全処理完了: {text_file}")
                self.status_var.set("完了!")
            else:
                self.log_message("❌ 文字おこしに失敗しました")
                self.status_var.set("失敗")
                
        except Exception as e:
            self.log_message(f"❌ エラー: {e}")
            self.status_var.set("エラー")
        finally:
            # ボタン復元
            self.is_running = False
            self.video_button.config(state='normal')

    def _process_media_thread(self):
        print("=== スレッド開始 ===")
        try:
            url_text = self.query_var.get().strip()
            translate = self.translate_var.get()
            use_timestamps = self.timestamp_var.get()
            whisper_model = self.whisper_model_var.get()
            audio_quality = self.audio_quality_var.get()
            claude_chat_url = self.claude_chat_url_var.get().strip()
            
            # 初期設定
            setup_logging("INFO")
            create_directories()
            
            self.log_message("メディア処理開始...")
            self.log_message(f"Whisperモデル: {whisper_model}")
            
            if self._is_youtube_url(url_text):
                self.log_message("🎥 YouTube動画を処理中...")
                self.status_var.set("YouTube動画ダウンロード中...")
            else:
                self.log_message("🐦 ツイート動画を処理中...")
                self.status_var.set("ツイート動画ダウンロード中...")
            
            self.progress_var.set(10)
            
            # 統合動画処理ワークフロー実行
            from workflows.universal_media_transcription import UniversalMediaTranscriptionWorkflow
            workflow = UniversalMediaTranscriptionWorkflow()
            
            self.progress_var.set(30)
            self.log_message("🎤 Whisper文字おこし開始...")
            self.status_var.set("文字おこし処理中...")
            
            print("=== ワークフロー実行前 ===")
            video_path, text_file, transcription_text, translation = workflow.execute_with_callback(
                url_text, translate, "en", whisper_model, audio_quality, use_timestamps,
                progress_callback=None
            )
            print("=== ワークフロー実行後 ===")
            
            self.progress_var.set(80)
            
            # 処理完了後のログ
            if transcription_text:
                self.log_message("=" * 40)
                self.log_message("✅ 文字おこし完了！")
                
                # 統計情報をログに表示
                lines = transcription_text.split('\n')
                text_lines = [line for line in lines if line.strip()]
                
                self.log_message(f"📊 統計情報:")
                self.log_message(f"   - 総行数: {len(text_lines)}")
                self.log_message(f"   - 文字数: {len(transcription_text)}")
                self.log_message(f"   - 動画ファイル: {os.path.basename(video_path) if video_path else 'なし'}")
                
                # 最初と最後の数行をプレビュー
                self.log_message("🔍 文字おこし内容プレビュー:")
                for i, line in enumerate(text_lines[:3]):
                    if line.strip():
                        self.log_message(f"   {line.strip()}")
                
                if len(text_lines) > 6:
                    self.log_message("   ...")
                    for line in text_lines[-3:]:
                        if line.strip():
                            self.log_message(f"   {line.strip()}")
                
                # 翻訳結果（ある場合）
                if translation:
                    self.log_message("🌐 翻訳結果:")
                    trans_lines = translation.split('\n')[:3]
                    for line in trans_lines:
                        if line.strip():
                            self.log_message(f"   🔤 {line.strip()}")
                
                self.log_message("🤖 Claude分析をスキップ（手動でファイルを分析してください）")
                
                self.progress_var.set(100)
                
                # 結果表示（メインスレッドで実行）
                def update_result():
                    if text_file:
                        self.result_file_path = text_file
                        self.video_file_path = video_path
                        
                        filename = os.path.basename(text_file)
                        platform = "YouTube" if self._is_youtube_url(url_text) else "Twitter"
                        result_text = f"{platform}文字おこし完了: {filename}"
                        if video_path:
                            result_text += f" + 動画ファイル"
                        
                        self.result_label.config(text=result_text)
                        
                        # ボタン有効化
                        self.open_file_button.config(state='normal')
                        self.open_folder_button.config(state='normal')
                        self.file_button.config(state='normal')
                        
                        self.status_var.set("完了!")
                    else:
                        self.status_var.set("失敗")
                
                # メインスレッドで実行
                self.root.after(0, update_result)
                
                self.log_message(f"🎉 全処理完了: {text_file}")
            else:
                def set_failed_status():
                    self.log_message("❌ 文字おこしに失敗しました")
                    self.status_var.set("失敗")
                
                self.root.after(0, set_failed_status)
                
        except Exception as e:
            print(f"=== 例外発生: {e} ===")
            def handle_error():
                self.log_message(f"❌ エラー: {e}")
                self.status_var.set("エラー")
            
            self.root.after(0, handle_error)
        finally:
            print("=== finally ブロック ===")
            # 必ずメインスレッドでボタンを再有効化
            def restore_buttons():
                self.is_running = False
                self.video_button.config(state='normal')
            
            self.root.after(0, restore_buttons)
            print("=== スレッド終了 ===")

    def _on_whisper_model_change(self, event=None):
        """Whisperモデル変更時の説明更新"""
        model = self.whisper_model_var.get()
        
        model_info = {
            "tiny": "精度: 低 | 速度: 最高 | サイズ: 39MB",
            "base": "精度: 中 | 速度: 高 | サイズ: 74MB",
            "small": "精度: 中高 | 速度: 中 | サイズ: 244MB",
            "medium": "精度: 高 | 速度: 中低 | サイズ: 769MB",
            "large": "精度: 最高 | 速度: 低 | サイズ: 1550MB",
            "large-v2": "精度: 最高+ | 速度: 低 | サイズ: 1550MB",
            "large-v3": "精度: 最高++ | 速度: 最低 | サイズ: 1550MB"
        }
        
        info_text = model_info.get(model, "情報なし")
        self.model_info_label.config(text=info_text)

def main():
    root = tk.Tk()
    app = TwitterScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()