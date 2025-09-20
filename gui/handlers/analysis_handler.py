"""
Claude/ChatGPT分析処理ハンドラー
"""
import threading
import os
from datetime import datetime
from tkinter import messagebox
from ..utils.ui_helpers import DialogHelpers, UIHelpers

class AnalysisHandler:
    def __init__(self, main_app):
        self.main_app = main_app
    
    def analyze_with_claude(self, file_path):
        """AIでファイル分析（Claude/ChatGPT選択対応）"""
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("エラー", "分析するファイルが見つかりません")
            return
        
        # AI サービス取得
        ai_service = getattr(self.main_app.media_frame, 'ai_service_var', None)
        if ai_service:
            service_name = ai_service.get()
        else:
            service_name = "claude"  # デフォルト
        
        # 分析プロンプト入力ダイアログ
        default_prompt = self._get_default_analysis_prompt()
        prompt = DialogHelpers.create_prompt_dialog(
            self.main_app.root,
            f"{service_name.upper()}分析プロンプト",
            default_prompt
        )
        
        if prompt is None or prompt == "":
            return  # キャンセル時は何もしない
        
        # 分析ボタン無効化
        UIHelpers.safe_button_state(self.main_app.results_frame.analyze_button, 'disabled')
        
        # 別スレッドで分析実行
        thread = threading.Thread(
            target=self._ai_analysis_thread,
            args=(file_path, prompt, service_name),
            daemon=True
        )
        thread.start()

    def analyze_comments(self, comments_file_path):
        """YouTubeコメント分析実行（AI選択対応）"""
        if not comments_file_path or not os.path.exists(comments_file_path):
            messagebox.showerror("エラー", "分析するコメントファイルが見つかりません")
            return
        
        # AI サービス取得
        ai_service = getattr(self.main_app.media_frame, 'ai_service_var', None)
        if ai_service:
            service_name = ai_service.get()
        else:
            service_name = "claude"  # デフォルト
        
        # ボタンを無効化
        UIHelpers.safe_button_state(self.main_app.results_frame.comment_analysis_button, 'disabled')
        
        # 別スレッドでコメント分析を実行
        thread = threading.Thread(
            target=self._comment_analysis_thread,
            args=(comments_file_path, service_name),
            daemon=True
        )
        thread.start()

    def _ai_analysis_thread(self, file_path, prompt, service_name):
        """AI分析スレッド（Claude/ChatGPT対応）"""
        try:
            self._setup_ai_environment()
            
            self.main_app.log_message(f"{service_name.upper()} ファイルアップロード分析開始...")
            self._update_status(f"{service_name.upper()}でファイル分析中...")
            
            # AI分析実行
            if service_name == "chatgpt":
                result, chat_url = self._execute_chatgpt_analysis(file_path, prompt)
            else:
                result, chat_url = self._execute_claude_analysis(file_path, prompt)
            
            if result:
                self._handle_ai_analysis_success(result, chat_url, file_path, service_name)
            else:
                self._handle_ai_analysis_failure(service_name)
                
        except Exception as e:
            self._handle_ai_analysis_error(e, service_name)
        finally:
            # ボタンを再有効化
            UIHelpers.safe_button_state(self.main_app.results_frame.analyze_button, 'normal')

    def _comment_analysis_thread(self, comments_file_path, service_name):
        """コメント分析スレッド（AI選択対応）"""
        try:
            self._setup_ai_environment()
            
            self.main_app.log_message(f"YouTube{service_name.upper()}コメント分析開始...")
            self._update_status(f"{service_name.upper()}でコメント分析中...")
            
            # AI分析実行
            if service_name == "chatgpt":
                result, chat_url = self._execute_chatgpt_comment_analysis(comments_file_path)
            else:
                result, chat_url = self._execute_claude_comment_analysis(comments_file_path)
            
            # 結果検証
            if self._validate_comment_analysis_result(result):
                self._handle_comment_analysis_success(result, chat_url, comments_file_path, service_name)
            else:
                self._handle_comment_analysis_failure(result, service_name)
                
        except Exception as e:
            self._handle_comment_analysis_error(e, service_name)
        finally:
            # ボタンを再有効化
            UIHelpers.safe_button_state(self.main_app.results_frame.comment_analysis_button, 'normal')

    def _setup_ai_environment(self):
        """AI環境設定"""
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    def _execute_claude_analysis(self, file_path, prompt):
        """Claude分析実行"""
        from lib.claude_automation import ClaudeAutomation
        from lib.chrome_connector import ChromeConnector
        
        # Chrome接続してClaude自動操作
        chrome = ChromeConnector()
        if not chrome.connect():
            self.main_app.log_message("❌ Chrome接続に失敗しました")
            return None, None
        
        claude = ClaudeAutomation(chrome)
        
        # 入力されたAI URLを使用（互換性維持）
        ai_chat_url = self._get_ai_chat_url()
        result, chat_url = claude.upload_and_analyze_file(
            file_path, 
            prompt, 
            chat_url=(ai_chat_url if ai_chat_url else None)
        )
        
        return result, chat_url

    def _execute_chatgpt_analysis(self, file_path, prompt):
        """ChatGPT分析実行"""
        from lib.chatgpt_automation import ChatGPTAutomation
        from lib.chrome_connector import ChromeConnector
        
        # Chrome接続してChatGPT自動操作
        chrome = ChromeConnector()
        if not chrome.connect():
            self.main_app.log_message("❌ Chrome接続に失敗しました")
            return None, None
        
        chatgpt = ChatGPTAutomation(chrome)
        
        # 入力されたAI URLを使用
        ai_chat_url = self._get_ai_chat_url()
        result, chat_url = chatgpt.upload_and_analyze_file(
            file_path, 
            prompt, 
            chat_url=(ai_chat_url if ai_chat_url else None)
        )
        
        return result, chat_url

    def _execute_claude_comment_analysis(self, comments_file_path):
        """Claudeコメント分析実行"""
        from lib.claude_automation import ClaudeAutomation
        from lib.chrome_connector import ChromeConnector
        
        # Chrome接続してClaude自動操作
        chrome = ChromeConnector()
        if not chrome.connect():
            self.main_app.log_message("❌ Chrome接続に失敗しました")
            return None, None
        
        claude = ClaudeAutomation(chrome)
        
        # 入力されたAI URLを使用
        ai_chat_url = self._get_ai_chat_url()
        
        self.main_app.log_message("🔄 Claude分析処理を実行中...")
        result, chat_url = claude.analyze_comments(
            comments_file_path, 
            chat_url=(ai_chat_url if ai_chat_url else None)
        )
        
        return result, chat_url

    def _execute_chatgpt_comment_analysis(self, comments_file_path):
        """ChatGPTコメント分析実行"""
        from lib.chatgpt_automation import ChatGPTAutomation
        from lib.chrome_connector import ChromeConnector
        
        # Chrome接続してChatGPT自動操作
        chrome = ChromeConnector()
        if not chrome.connect():
            self.main_app.log_message("❌ Chrome接続に失敗しました")
            return None, None
        
        chatgpt = ChatGPTAutomation(chrome)
        
        # 入力されたAI URLを使用
        ai_chat_url = self._get_ai_chat_url()
        
        self.main_app.log_message("🔄 ChatGPT分析処理を実行中...")
        result, chat_url = chatgpt.analyze_comments(
            comments_file_path, 
            chat_url=(ai_chat_url if ai_chat_url else None)
        )
        
        return result, chat_url

    def _get_ai_chat_url(self):
        """AI チャットURLを取得（新旧両対応）"""
        # 新しいAI URL変数を優先
        if hasattr(self.main_app.media_frame, 'ai_chat_url_var'):
            return self.main_app.media_frame.ai_chat_url_var.get().strip()
        # 互換性のため古いClaude URL変数も確認
        elif hasattr(self.main_app.media_frame, 'claude_chat_url_var'):
            return self.main_app.media_frame.claude_chat_url_var.get().strip()
        else:
            return None

    def _validate_comment_analysis_result(self, result):
        """コメント分析結果検証"""
        # デバッグ情報をログ出力
        self.main_app.log_message(f"🔍 分析結果検証: result={'有' if result else '無'}")
        if result:
            self.main_app.log_message(f"🔍 結果の長さ: {len(result.strip())} 文字")
            self.main_app.log_message(f"🔍 結果の先頭: {result.strip()[:200]}...")
        
        # 結果の詳細チェック（偽の成功を防ぐ）
        return result and len(result.strip()) > 50 and "分析" in result

    def _handle_ai_analysis_success(self, result, chat_url, file_path, service_name):
        """AI分析成功処理"""
        self.main_app.log_message(f"✅ {service_name.upper()}分析完了")
        self._update_status(f"{service_name.upper()}分析完了")
        
        # 分析結果を保存
        try:
            analysis_file = self._save_analysis_result(result, chat_url, file_path, f"{service_name}_analysis")
            self.main_app.log_message(f"{service_name.upper()}分析結果保存: {analysis_file}")
        except Exception as e:
            self.main_app.log_message(f"{service_name.upper()}分析結果保存エラー: {e}")
        
        # AI URLを自動入力
        self._set_ai_url(chat_url)
        
        # 完了メッセージ
        self.main_app.root.after(0, lambda: messagebox.showinfo(
            "完了", 
            f"{service_name.upper()}分析が完了しました\n{service_name.upper()} URLも自動設定されました"
        ))

    def _handle_comment_analysis_success(self, result, chat_url, comments_file_path, service_name):
        """コメント分析成功処理"""
        self.main_app.log_message(f"✅ {service_name.upper()}コメント分析完了")
        self._update_status(f"{service_name.upper()}コメント分析完了")
        
        # コメント分析結果を保存
        try:
            analysis_file = self._save_analysis_result(result, chat_url, comments_file_path, f"youtube_comments_{service_name}_analysis")
            self.main_app.log_message(f"{service_name.upper()}コメント分析結果保存: {analysis_file}")
        except Exception as e:
            self.main_app.log_message(f"{service_name.upper()}コメント分析結果保存エラー: {e}")
        
        # AI URLを自動入力
        self._set_ai_url(chat_url)
        
        # UI更新を安全に実行（メインスレッドで実行）
        self.main_app.root.after(0, lambda: messagebox.showinfo(
            "完了", 
            f"YouTube{service_name.upper()}コメント分析が完了しました\n{service_name.upper()} URLも自動設定されました"
        ))

    def _handle_ai_analysis_failure(self, service_name):
        """AI分析失敗処理"""
        self.main_app.log_message(f"❌ {service_name.upper()}分析失敗")
        self._update_status(f"{service_name.upper()}分析失敗")
        self.main_app.root.after(0, lambda: messagebox.showerror("エラー", f"{service_name.upper()}分析に失敗しました"))

    def _handle_comment_analysis_failure(self, result, service_name):
        """コメント分析失敗処理"""
        self.main_app.log_message(f"❌ {service_name.upper()}コメント分析失敗（結果が無効または不完全）")
        self._update_status(f"{service_name.upper()}コメント分析失敗")
        
        # デバッグ情報をログに出力
        if result:
            self.main_app.log_message(f"📝 取得した結果: {result[:100]}...")
        else:
            self.main_app.log_message("📝 結果がNullまたは空文字")
        
        self.main_app.root.after(0, lambda: messagebox.showerror(
            "エラー", 
            f"{service_name.upper()}コメント分析に失敗しました\n（結果が無効または不完全）"
        ))

    def _handle_ai_analysis_error(self, e, service_name):
        """AI分析エラー処理"""
        self.main_app.log_message(f"❌ {service_name.upper()}分析エラー: {e}")
        self._update_status("エラー")
        self.main_app.root.after(0, lambda: messagebox.showerror("エラー", f"{service_name.upper()}分析エラー: {e}"))

    def _handle_comment_analysis_error(self, e, service_name):
        """コメント分析エラー処理"""
        self.main_app.log_message(f"❌ {service_name.upper()}コメント分析エラー: {e}")
        self._update_status("エラー")
        self.main_app.root.after(0, lambda: messagebox.showerror("エラー", f"{service_name.upper()}コメント分析エラー: {e}"))

    def _save_analysis_result(self, result, chat_url, source_file_path, analysis_type):
        """分析結果保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_dir = os.path.dirname(source_file_path)
        
        # ファイル名を分析タイプに応じて生成
        if "claude_analysis" in analysis_type:
            base_name = os.path.splitext(os.path.basename(source_file_path))[0]
            analysis_file = os.path.join(base_dir, f"{timestamp}_{base_name}_claude_analysis.txt")
        elif "chatgpt_analysis" in analysis_type:
            base_name = os.path.splitext(os.path.basename(source_file_path))[0]
            analysis_file = os.path.join(base_dir, f"{timestamp}_{base_name}_chatgpt_analysis.txt")
        else:
            analysis_file = os.path.join(base_dir, f"{timestamp}_{analysis_type}.txt")
        
        with open(analysis_file, 'w', encoding='utf-8') as f:
            # ヘッダー情報
            if "youtube_comments" in analysis_type:
                f.write(f"コメントファイル: {source_file_path}\n")
            else:
                f.write(f"元ファイル: {source_file_path}\n")
            
            if chat_url:
                service_name = "ChatGPT" if "chatgpt" in analysis_type else "Claude"
                f.write(f"{service_name} URL: {chat_url}\n")
            
            f.write(f"分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            # 分析結果本文
            service_name = "ChatGPT" if "chatgpt" in analysis_type else "Claude"
            comment_prefix = "コメント" if "youtube_comments" in analysis_type else ""
            f.write(f"【{service_name}{comment_prefix}分析結果】\n")
            f.write(result)
        
        return analysis_file

    def _set_ai_url(self, chat_url):
        """AI URLを自動設定"""
        if chat_url and hasattr(self.main_app.media_frame, 'ai_chat_url_var'):
            self.main_app.media_frame.ai_chat_url_var.set(chat_url)
            self.main_app.log_message(f"🔗 AI URL自動設定: {chat_url}")
        elif chat_url and hasattr(self.main_app.media_frame, 'claude_chat_url_var'):
            # 互換性維持
            self.main_app.media_frame.claude_chat_url_var.set(chat_url)
            self.main_app.log_message(f"🔗 AI URL自動設定: {chat_url}")

    def _update_status(self, status):
        """ステータス更新"""
        UIHelpers.safe_label_update(self.main_app.execution_frame.status_label, status)

    def _get_default_analysis_prompt(self):
        """デフォルト分析プロンプトを取得"""
        return """この内容を分析してください。

【分析してほしい内容】
1. 全体的な傾向と特徴
2. 主要なポイント・キーワード
3. エンゲージメントの高い内容の特徴
4. 要約（3-5行程度）

【出力形式】
- 簡潔で分かりやすく
- 具体的な数値や例を含めて
- 実用的な洞察を提供"""