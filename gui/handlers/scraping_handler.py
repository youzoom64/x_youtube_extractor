"""
スクレイピング処理ハンドラー
"""
import threading
import os
from tkinter import messagebox
from ..utils.validators import URLValidator
from ..utils.ui_helpers import UIHelpers
from lib.database_manager import DatabaseManager
from config.settings import USE_DATABASE, DATABASE_PATH

class ScrapingHandler:
    def __init__(self, main_app):
        self.main_app = main_app
    
    def run_scraping(self):
        """スクレイピング実行"""
        if self.main_app.is_running:
            return
        
        query = self.main_app.settings_frame.query_var.get().strip()
        if not query:
            messagebox.showerror("エラー", "検索クエリを入力してください")
            return
        
        # ツイートURLの場合はリプライ取得を提案
        if URLValidator.is_tweet_url(query):
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
        is_valid, error_msg = URLValidator.validate_query(query)
        if not is_valid:
            messagebox.showerror("エラー", error_msg)
            return
        
        # UI状態更新
        self._set_running_state(True)
        
        # 別スレッドで実行
        thread = threading.Thread(target=self._run_scraping_thread, daemon=True)
        thread.start()

    def get_replies(self):
        """リプライ取得実行"""
        if self.main_app.is_running:
            return
        
        tweet_url = self.main_app.settings_frame.query_var.get().strip()
        if not tweet_url:
            messagebox.showerror("エラー", "ツイートURLを入力してください")
            return
        
        # URL検証
        if not URLValidator.is_tweet_url(tweet_url):
            messagebox.showerror("エラー", "有効なツイートURLを入力してください\n例: https://x.com/username/status/1234567890")
            return
        
        # UI状態更新
        self._set_running_state(True)
        
        # 別スレッドで実行
        thread = threading.Thread(target=self._get_replies_thread, daemon=True)
        thread.start()

    def _run_scraping_thread(self):
        """スクレイピング実行スレッド"""
        try:
            # 設定取得
            settings = self._get_scraping_settings()
            
            # 初期設定
            self._setup_environment()
            
            self.main_app.log_message("処理開始...")
            self._update_status_progress("Chrome接続中...", 10)
            
            # ワークフロー実行
            if settings['screenshot_enabled']:
                result = self._execute_with_screenshots(settings)
            else:
                result = self._execute_normal_scraping(settings)
            
            self._handle_scraping_result(result, settings['screenshot_enabled'])
                
        except Exception as e:
            self._handle_error(f"エラー: {e}")
        finally:
            self._set_running_state(False)

    def _get_replies_thread(self):
        """リプライ取得スレッド"""
        try:
            # 設定取得
            settings = self._get_reply_settings()
            
            # 初期設定
            self._setup_environment()
            
            self.main_app.log_message("リプライ取得開始...")
            self._update_status_progress("Chrome接続中...", 10)
            
            # ワークフロー実行
            if settings['screenshot_enabled']:
                result = self._execute_replies_with_screenshots(settings)
            else:
                result = self._execute_normal_replies(settings)
            
            self._handle_replies_result(result, settings['screenshot_enabled'])
                
        except Exception as e:
            self._handle_error(f"リプライ取得エラー: {e}")
        finally:
            self._set_running_state(False)

    def _get_scraping_settings(self):
        """スクレイピング設定取得"""
        settings_data = self.main_app.settings_frame
        screenshot_data = self.main_app.screenshot_frame.get_settings()
        
        return {
            'query': settings_data.query_var.get().strip(),
            'count': int(settings_data.count_var.get()),
            'format_type': settings_data.format_var.get(),
            'sort_type': settings_data.sort_var.get(),
            'screenshot_enabled': screenshot_data['screenshot_enabled'],
            'capture_mode': screenshot_data['capture_mode'],
            'exclude_promoted': screenshot_data['exclude_promoted']
        }

    def _get_reply_settings(self):
        """リプライ取得設定取得"""
        settings_data = self.main_app.settings_frame
        screenshot_data = self.main_app.screenshot_frame.get_settings()
        
        return {
            'tweet_url': settings_data.query_var.get().strip(),
            'count': int(settings_data.count_var.get()),
            'format_type': settings_data.format_var.get(),
            'screenshot_enabled': screenshot_data['screenshot_enabled'],
            'capture_mode': screenshot_data['capture_mode'],
            'exclude_promoted': screenshot_data['exclude_promoted']
        }

    def _setup_environment(self):
        """環境設定"""
        # 遅延インポートで循環インポートを回避
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        from lib.utils import setup_logging, create_directories
        setup_logging("INFO")
        create_directories()

    def _execute_with_screenshots(self, settings):
        """スクリーンショット付きスクレイピング実行"""
        try:
            from workflows.scrape_with_screenshots import ScrapeWithScreenshotsWorkflow
            self.main_app.log_message("スクリーンショット撮影モードで実行")
            workflow = ScrapeWithScreenshotsWorkflow()
            self._update_status_progress("ツイート取得＋スクリーンショット撮影中...", 30)
            
            txt_file, screenshot_files, summary_file = workflow.execute(
                settings['query'], 
                settings['count'], 
                settings['format_type'], 
                settings['sort_type'], 
                settings['capture_mode']
            )
            
            self._update_status_progress("", 100)
            
            return {
                'success': bool(txt_file and screenshot_files),
                'txt_file': txt_file,
                'screenshot_files': screenshot_files,
                'summary_file': summary_file,
                'type': 'screenshot'
            }
        except Exception as e:
            self.main_app.log_message(f"スクリーンショット撮影エラー: {e}")
            return {'success': False, 'error': str(e)}

    def _execute_normal_scraping(self, settings):
        """通常のスクレイピング実行"""
        try:
            from workflows.scrape_only import ScrapeOnlyWorkflow
            self.main_app.log_message("通常モードで実行")
            workflow = ScrapeOnlyWorkflow()
            self._update_status_progress("ツイート取得中...", 50)
            
            result_file = workflow.execute(
                settings['query'], 
                settings['count'], 
                settings['format_type'], 
                settings['sort_type']
            )
            
            self._update_status_progress("", 100)
            
            return {
                'success': bool(result_file),
                'result_file': result_file,
                'type': 'normal'
            }
        except Exception as e:
            self.main_app.log_message(f"スクレイピングエラー: {e}")
            return {'success': False, 'error': str(e)}

    def _execute_replies_with_screenshots(self, settings):
        """スクリーンショット付きリプライ取得実行"""
        try:
            from workflows.scrape_with_screenshots import ScrapeWithScreenshotsWorkflow
            self.main_app.log_message("リプライ + スクリーンショット撮影モードで実行（統合版）")
            workflow = ScrapeWithScreenshotsWorkflow()
            self._update_status_progress("リプライ取得＋スクリーンショット撮影中...", 30)
            
            txt_file, screenshot_files, summary_file = workflow.execute(
                settings['tweet_url'], 
                settings['count'], 
                settings['format_type'], 
                settings['capture_mode']
            )
            
            self._update_status_progress("", 100)
            
            return {
                'success': bool(txt_file and screenshot_files),
                'txt_file': txt_file,
                'screenshot_files': screenshot_files,
                'summary_file': summary_file,
                'type': 'replies_screenshot'
            }
        except Exception as e:
            self.main_app.log_message(f"リプライ+スクリーンショットエラー: {e}")
            return {'success': False, 'error': str(e)}

    def _execute_normal_replies(self, settings):
        """通常のリプライ取得実行"""
        try:
            from workflows.scrape_replies import ScrapeRepliesWorkflow
            workflow = ScrapeRepliesWorkflow()
            self._update_status_progress("リプライ取得中...", 30)
            
            result_file = workflow.execute(
                settings['tweet_url'], 
                settings['count'], 
                settings['format_type']
            )
            
            self._update_status_progress("", 100)
            
            return {
                'success': bool(result_file),
                'result_file': result_file,
                'type': 'replies_normal'
            }
        except Exception as e:
            self.main_app.log_message(f"リプライ取得エラー: {e}")
            return {'success': False, 'error': str(e)}

    def _handle_scraping_result(self, result, screenshot_enabled):
        """スクレイピング結果処理"""
        if result['success']:
            if screenshot_enabled:
                self._handle_screenshot_success(result, "処理完了")
            else:
                self._handle_normal_success(result, "処理完了")
        else:
            self._handle_failure("処理に失敗しました", result.get('error', ''))

    def _handle_replies_result(self, result, screenshot_enabled):
        """リプライ取得結果処理"""
        if result['success']:
            if screenshot_enabled:
                self._handle_screenshot_success(result, "リプライ取得完了", is_reply=True)
            else:
                self._handle_normal_success(result, "リプライ取得完了", is_reply=True)
        else:
            self._handle_failure("リプライ取得に失敗しました", result.get('error', ''))

    def _handle_screenshot_success(self, result, message, is_reply=False):
        """スクリーンショット付き成功処理"""
        txt_file = result['txt_file']
        screenshot_files = result['screenshot_files']
        summary_file = result.get('summary_file')
        
        # DB保存
        if USE_DATABASE:
            try:
                db = DatabaseManager(DATABASE_PATH)
                query = self._get_current_query()
                source_type = "reply" if is_reply else "search"
                count = self._get_current_count()
                format_type = self._get_current_format()
                sort_type = self._get_current_sort() if not is_reply else None
                
                # 検索履歴をDB保存
                search_id = db.save_search(
                    query=query,
                    source_type=source_type,
                    count_requested=count,
                    format_type=format_type,
                    sort_type=sort_type,
                    result_file_path=txt_file
                )
                
                # スクリーンショット情報をDB保存
                capture_mode = self._get_current_capture_mode()
                db.save_screenshots(search_id, screenshot_files, capture_mode)
                
                self.main_app.log_message(f"DB保存完了: 検索ID={search_id}")
                
            except Exception as e:
                self.main_app.log_message(f"DB保存エラー: {e}")
        
        # 結果設定（既存のコード）
        self.main_app.results_frame.set_result(
            txt_file,
            screenshot_files=screenshot_files,
            summary_file=summary_file
        )
        
        # ログ出力とメッセージ（既存のコード）
        prefix = "リプライ" if is_reply else ""
        self.main_app.log_message(f"処理完了: {prefix}{message}: {txt_file}")
        self.main_app.log_message(f"スクリーンショット: {len(screenshot_files)}枚")
        self._update_status_progress("完了!", 100)

    def _handle_normal_success(self, result, message, is_reply=False):
        """通常成功処理"""
        result_file = result['result_file']
        
        # DB保存
        if USE_DATABASE:
            try:
                db = DatabaseManager(DATABASE_PATH)
                query = self._get_current_query()
                source_type = "reply" if is_reply else "search"
                count = self._get_current_count()
                format_type = self._get_current_format()
                sort_type = self._get_current_sort() if not is_reply else None
                
                # 検索履歴をDB保存
                search_id = db.save_search(
                    query=query,
                    source_type=source_type,
                    count_requested=count,
                    format_type=format_type,
                    sort_type=sort_type,
                    result_file_path=result_file
                )
                
                self.main_app.log_message(f"DB保存完了: 検索ID={search_id}")
                
            except Exception as e:
                self.main_app.log_message(f"DB保存エラー: {e}")
        
        # 結果設定（既存のコード）
        self.main_app.results_frame.set_result(result_file)
        
        # ログ出力とメッセージ（既存のコード）
        prefix = "リプライ" if is_reply else ""
        self.main_app.log_message(f"処理完了: {prefix}{message}: {result_file}")
        self._update_status_progress("完了!", 100)

    def _handle_failure(self, message, error_detail=""):
        """失敗処理"""
        self.main_app.log_message(f"❌ {message}")
        if error_detail:
            self.main_app.log_message(f"詳細: {error_detail}")
        self._update_status_progress("失敗", 0)
        messagebox.showerror("エラー", message)

    def _handle_error(self, error_message):
        """エラー処理"""
        self.main_app.log_message(f"❌ {error_message}")
        self._update_status_progress("エラー", 0)
        messagebox.showerror("エラー", f"エラーが発生しました: {error_message}")

    def _set_running_state(self, running):
        """実行状態設定"""
        self.main_app.is_running = running
        
        # ボタン状態更新
        execution_buttons = self.main_app.execution_frame.get_all_buttons()
        if running:
            UIHelpers.disable_buttons_during_execution(execution_buttons)
            self.main_app.log_text.delete(1.0, 'end')
        else:
            UIHelpers.enable_buttons_after_execution(execution_buttons)

    def _update_status_progress(self, status, progress):
        """ステータスとプログレス更新"""
        if status:
            UIHelpers.safe_label_update(self.main_app.execution_frame.status_label, status)
        UIHelpers.safe_progress_update(self.main_app.execution_frame.progress_var, progress)

    def _get_current_query(self):
        """現在のクエリを取得"""
        return self.main_app.settings_frame.query_var.get().strip()

    def _get_current_count(self):
        """現在の件数を取得"""
        return int(self.main_app.settings_frame.count_var.get())

    def _get_current_format(self):
        """現在の形式を取得"""
        return self.main_app.settings_frame.format_var.get()

    def _get_current_sort(self):
        """現在のソート順を取得"""
        return self.main_app.settings_frame.sort_var.get()

    def _get_current_capture_mode(self):
        """現在の撮影モードを取得"""
        return self.main_app.screenshot_frame.capture_mode_var.get()