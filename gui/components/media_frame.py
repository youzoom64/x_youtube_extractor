"""
動画・音声設定フレーム
"""
import tkinter as tk
from tkinter import ttk
from ..utils.ui_helpers import UIHelpers

class MediaFrame:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.create_frame()
        
    def create_frame(self):
        """動画・音声設定フレーム作成"""
        
        # 動画・音声設定フレーム
        self.frame = ttk.LabelFrame(self.parent, text="🎥 動画・音声処理", padding="10")
        self.frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 動画処理オプション（第1行）
        self.create_media_options_row1()
        
        # Whisperモデル選択（第2行）
        self.create_whisper_model_selection()
        
        # Claudeチャット URL
        self.create_claude_url_input()
        
        # グリッド設定
        self.frame.columnconfigure(1, weight=1)
    
    def create_media_options_row1(self):
        """動画処理オプション第1行作成"""
        media_options_frame1 = ttk.Frame(self.frame)
        media_options_frame1.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        self.translate_var = tk.BooleanVar(value=False)
        self.translate_checkbox = ttk.Checkbutton(
            media_options_frame1, 
            text="🌐 英語翻訳", 
            variable=self.translate_var
        )
        self.translate_checkbox.grid(row=0, column=0, sticky=tk.W)

        self.timestamp_var = tk.BooleanVar(value=True)
        self.timestamp_checkbox = ttk.Checkbutton(
            media_options_frame1, 
            text="⏰ タイムスタンプ付与", 
            variable=self.timestamp_var
        )
        self.timestamp_checkbox.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))

        self.download_video_var = tk.BooleanVar(value=True)
        self.download_video_checkbox = ttk.Checkbutton(
            media_options_frame1, 
            text="📥 動画ダウンロード", 
            variable=self.download_video_var
        )
        self.download_video_checkbox.grid(row=0, column=2, sticky=tk.W, padx=(20, 0))

        self.force_whisper_var = tk.BooleanVar(value=False)
        self.force_whisper_checkbox = ttk.Checkbutton(
            media_options_frame1, 
            text="🎵 Whisper強制実行", 
            variable=self.force_whisper_var
        )
        self.force_whisper_checkbox.grid(row=0, column=3, sticky=tk.W, padx=(20, 0))
    
    def create_whisper_model_selection(self):
        """Whisperモデル選択作成"""
        media_options_frame2 = ttk.Frame(self.frame)
        media_options_frame2.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(media_options_frame2, text="Whisperモデル:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.whisper_model_var = tk.StringVar(value="base")
        whisper_combo = ttk.Combobox(
            media_options_frame2, 
            textvariable=self.whisper_model_var, 
            values=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"], 
            width=12, 
            state="readonly"
        )
        whisper_combo.grid(row=0, column=1, sticky=tk.W)

        # モデル説明ラベル
        self.model_info_label = ttk.Label(
            media_options_frame2, 
            text="精度: 中 | 速度: 高", 
            foreground="blue"
        )
        self.model_info_label.grid(row=0, column=2, sticky=tk.W, padx=(10, 0))

        # Whisperモデル変更時の説明更新
        whisper_combo.bind('<<ComboboxSelected>>', self._on_whisper_model_change)

        # 音声品質設定
        ttk.Label(media_options_frame2, text="音声品質:").grid(row=0, column=3, sticky=tk.W, padx=(20, 10))
        self.audio_quality_var = tk.StringVar(value="best")
        quality_combo = ttk.Combobox(
            media_options_frame2, 
            textvariable=self.audio_quality_var,
            values=["best", "good", "medium"], 
            width=8, 
            state="readonly"
        )
        quality_combo.grid(row=0, column=4, sticky=tk.W)
    
    def create_claude_url_input(self):
        """AI分析設定作成"""
        # AI選択フレーム
        ai_selection_frame = ttk.Frame(self.frame)
        ai_selection_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # AI選択ラベルとラジオボタン
        ttk.Label(ai_selection_frame, text="AI分析:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.ai_service_var = tk.StringVar(value="claude")
        ai_frame = ttk.Frame(ai_selection_frame)
        ai_frame.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # Claude/ChatGPT選択ラジオボタン
        ttk.Radiobutton(ai_frame, text="🤖 Claude", variable=self.ai_service_var, value="claude", 
                    command=self._on_ai_service_change).grid(row=0, column=0, padx=(0, 15))
        ttk.Radiobutton(ai_frame, text="💬 ChatGPT", variable=self.ai_service_var, value="chatgpt", 
                    command=self._on_ai_service_change).grid(row=0, column=1, padx=(0, 15))
        
        # AI URL入力（動的ラベル）
        self.ai_url_label = ttk.Label(ai_selection_frame, text="Claude チャットURL (任意):")
        self.ai_url_label.grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        self.ai_chat_url_var = tk.StringVar()
        self.ai_chat_url_entry = ttk.Entry(ai_selection_frame, textvariable=self.ai_chat_url_var, width=70)
        self.ai_chat_url_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 旧変数との互換性維持（既存コードが動作するように）
        self.claude_chat_url_var = self.ai_chat_url_var

    def _on_whisper_model_change(self, event=None):
        """Whisperモデル変更時の説明更新"""
        model = self.whisper_model_var.get()
        info_text = UIHelpers.create_model_info_text(model)
        self.model_info_label.config(text=info_text)
    
    def _on_ai_service_change(self):
        """AI サービス変更時の処理"""
        service = self.ai_service_var.get()
        if service == "claude":
            self.ai_url_label.config(text="Claude チャットURL (任意):")
            self.ai_chat_url_entry.config(foreground="blue")
        elif service == "chatgpt":
            self.ai_url_label.config(text="ChatGPT チャットURL (任意):")
            self.ai_chat_url_entry.config(foreground="green")
        
        # ログ出力（main_appが利用可能な場合）
        try:
            service_name = "Claude" if service == "claude" else "ChatGPT"
            self.main_app.log_message(f"🔄 AI分析サービス変更: {service_name}")
        except:
            pass  # main_appが未初期化の場合は無視

    def get_settings(self):
        """動画・音声設定を取得"""
        return {
            'translate': self.translate_var.get(),
            'use_timestamps': self.timestamp_var.get(),
            'download_video': self.download_video_var.get(),
            'force_whisper': self.force_whisper_var.get(),
            'whisper_model': self.whisper_model_var.get(),
            'audio_quality': self.audio_quality_var.get(),
            'ai_service': getattr(self, 'ai_service_var', tk.StringVar(value="claude")).get(),  # 追加
            'ai_chat_url': getattr(self, 'ai_chat_url_var', tk.StringVar()).get().strip(),  # 追加
            'claude_chat_url': getattr(self, 'ai_chat_url_var', tk.StringVar()).get().strip()  # 互換性維持
        }