"""
入力検証ユーティリティ
"""
import tkinter as tk
import re

class URLValidator:
    """URL検証とタイプ判定クラス"""
    
    @staticmethod
    def is_tweet_url(text):
        """ツイートURLかどうか判定"""
        if not text:
            return False
        return ('x.com' in text or 'twitter.com' in text) and '/status/' in text
    
    @staticmethod
    def is_youtube_url(text):
        """YouTubeURLかどうか判定"""
        if not text:
            return False
        youtube_patterns = [
            'youtube.com/watch',
            'youtu.be/',
            'm.youtube.com',
            'youtube.com/shorts',
            'youtube.com/embed'
        ]
        return any(pattern in text.lower() for pattern in youtube_patterns)
    
    @staticmethod
    def validate_query(query):
        """クエリの基本検証"""
        if not query or not query.strip():
            return False, "検索クエリまたはURLを入力してください"
        
        query = query.strip()
        
        # URL形式の場合は追加検証
        if query.startswith(('http://', 'https://')):
            if URLValidator.is_tweet_url(query) or URLValidator.is_youtube_url(query):
                return True, ""
            else:
                return False, "サポートされていないURLです（Twitter/YouTube URLのみ対応）"
        
        # 検索クエリの場合の基本チェック
        if len(query) < 2:
            return False, "検索クエリは2文字以上で入力してください"
        
        if len(query) > 500:
            return False, "検索クエリが長すぎます（500文字以下）"
        
        return True, ""
    
    @staticmethod
    def update_url_type_display(query_var, url_type_label):
        """URL種別表示を更新"""
        try:
            url_text = query_var.get().strip()
            
            if not url_text:
                url_type_label.config(text="種別: 自動判定", foreground="blue")
                return
            
            if URLValidator.is_youtube_url(url_text):
                url_type_label.config(text="種別: YouTube動画", foreground="red")
            elif URLValidator.is_tweet_url(url_text):
                url_type_label.config(text="種別: ツイート", foreground="green")
            else:
                url_type_label.config(text="種別: 検索クエリ", foreground="purple")
                
        except Exception:
            url_type_label.config(text="種別: 不明", foreground="gray")

class InputValidator:
    """入力値検証クラス"""
    
    @staticmethod
    def validate_count(count_value):
        """取得件数の検証"""
        try:
            count = int(count_value)
            if count < 1:
                return False, "取得件数は1以上で指定してください"
            if count > 100:
                return False, "取得件数は100以下で指定してください"
            return True, ""
        except (ValueError, TypeError):
            return False, "取得件数は数値で指定してください"
    
    @staticmethod
    def validate_whisper_model(model_name):
        """Whisperモデル名の検証"""
        valid_models = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
        if model_name not in valid_models:
            return False, f"無効なWhisperモデルです。有効な値: {', '.join(valid_models)}"
        return True, ""
    
    @staticmethod
    def validate_claude_url(url):
        """Claude URLの検証"""
        if not url:
            return True, ""  # 空の場合はOK（オプション）
        
        if not url.startswith('https://claude.ai/'):
            return False, "Claude URLは https://claude.ai/ で始まる必要があります"
        
        return True, ""