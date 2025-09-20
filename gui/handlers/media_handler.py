"""
メディア処理ハンドラー
"""
import threading
import os
from tkinter import messagebox
from ..utils.validators import URLValidator
from ..utils.ui_helpers import UIHelpers
from lib.database_manager import DatabaseManager
from config.settings import USE_DATABASE, DATABASE_PATH

class MediaHandler:
    def __init__(self, main_app):
        self.main_app = main_app
    
    def process_media(self):
        """統合メディア処理実行"""
        if self.main_app.is_running:
            return
        
        url_text = self.main_app.settings_frame.query_var.get().strip()
        if not url_text:
            self.main_app.log_message("❌ 動画URLを入力してください")
            return
        
        # URL検証
        if not (URLValidator.is_tweet_url(url_text) or URLValidator.is_youtube_url(url_text)):
            self.main_app.log_message("❌ 有効なツイートURL または YouTubeURL を入力してください")
            return
        
        # UI状態更新
        self._set_running_state(True)
        
        # 非同期で段階的に実行
        self.main_app.root.after(100, self._start_media_processing, url_text)

    def _start_media_processing(self, url_text):
        """メディア処理開始（非同期実行）"""
        try:
            # 設定取得
            settings = self._get_media_settings(url_text)
            
            # 初期設定
            self._setup_environment()
            
            self.main_app.log_message("メディア処理開始...")
            self.main_app.log_message(f"Whisperモデル: {settings['whisper_model']}")
            
            # プラットフォーム判定とログ出力
            if URLValidator.is_youtube_url(url_text):
                self.main_app.log_message("🎥 YouTube動画を処理中...")
                self._update_status_progress("YouTube動画ダウンロード中...", 10)
            else:
                self.main_app.log_message("🐦 ツイート動画を処理中...")
                self._update_status_progress("ツイート動画ダウンロード中...", 10)
            
            # ワークフロー実行
            result = self._execute_media_workflow(settings)
            
            # 結果処理
            self._handle_media_result(result, url_text)
            
        except Exception as e:
            self._handle_error(f"メディア処理エラー: {e}")
        finally:
            self._set_running_state(False)

    def _get_media_settings(self, url_text):
        """メディア処理設定取得"""
        media_data = self.main_app.media_frame.get_settings()
        settings_data = self.main_app.settings_frame
        
        return {
            'url_text': url_text,
            'translate': media_data['translate'],
            'use_timestamps': media_data['use_timestamps'],
            'whisper_model': media_data['whisper_model'],
            'audio_quality': media_data['audio_quality'],
            'download_video': media_data['download_video'],
            'force_whisper': media_data['force_whisper'],
            'claude_chat_url': media_data['claude_chat_url'],
            'comment_count': int(settings_data.count_var.get())
        }

    def _setup_environment(self):
        """環境設定"""
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        from lib.utils import setup_logging, create_directories
        setup_logging("INFO")
        create_directories()

    def _execute_media_workflow(self, settings):
        """メディアワークフロー実行"""
        try:
            from workflows.universal_media_transcription import UniversalMediaTranscriptionWorkflow
            workflow = UniversalMediaTranscriptionWorkflow()
            
            self._update_status_progress("文字おこし処理中...", 30)
            self.main_app.log_message("🎤 Whisper文字おこし開始...")
            
            # 統合ワークフロー実行
            video_path, text_file, transcription_text, translation = workflow.execute_with_callback(
                settings['url_text'], 
                settings['translate'], 
                "en", 
                settings['whisper_model'], 
                settings['audio_quality'], 
                settings['use_timestamps'],
                progress_callback=None, 
                comment_count=settings['comment_count'], 
                download_video=settings['download_video'],
                force_whisper=settings['force_whisper']
            )
            
            self._update_status_progress("", 100)
            
            return {
                'success': bool(transcription_text and text_file),
                'video_path': video_path,
                'text_file': text_file,
                'transcription_text': transcription_text,
                'translation': translation,
                'url_text': settings['url_text']
            }
            
        except Exception as e:
            self.main_app.log_message(f"ワークフロー実行エラー: {e}")
            return {'success': False, 'error': str(e)}

    def _handle_media_result(self, result, url_text):
        """メディア処理結果処理"""
        if result['success']:
            self._handle_media_success(result)
        else:
            self._handle_media_failure(result.get('error', '不明なエラー'))

    def _handle_media_success(self, result):
        """メディア処理成功処理"""
        text_file = result['text_file']
        video_path = result['video_path']
        transcription_text = result['transcription_text']
        translation = result.get('translation')
        url_text = result['url_text']
        
        # 統計情報ログ出力
        self._log_transcription_stats(transcription_text, translation)
        
        # コメントファイル検出
        comments_file_path = self._detect_comments_file(text_file, url_text)
        
        # DB保存
        if USE_DATABASE:
            try:
                db = DatabaseManager(DATABASE_PATH)
                
                # プラットフォーム判定
                platform = "youtube" if URLValidator.is_youtube_url(url_text) else "twitter"
                
                # メディア処理設定取得
                settings = self._get_current_media_settings()
                
                # メディア処理結果をDB保存
                media_id = db.save_media_processing(
                    url=url_text,
                    platform=platform,
                    video_file_path=video_path,
                    transcription_file_path=text_file,
                    transcription_text=transcription_text,
                    translation_text=translation,
                    whisper_model=settings.get('whisper_model'),
                    use_timestamps=settings.get('use_timestamps'),
                    audio_quality=settings.get('audio_quality'),
                    video_info=None,  # 後で動画情報も保存可能
                    comments_file_path=comments_file_path
                )
                
                self.main_app.log_message(f"DB保存完了: メディアID={media_id}")
                
            except Exception as e:
                self.main_app.log_message(f"DB保存エラー: {e}")
        
        # 結果設定（既存のコード）
        self.main_app.results_frame.set_result(
            text_file,
            video_file_path=video_path,
            comments_file_path=comments_file_path
        )
        
        # 完了ログとメッセージ（既存のコード）
        platform = "YouTube" if URLValidator.is_youtube_url(url_text) else "Twitter"
        self.main_app.log_message(f"全処理完了: {text_file}")
        self._update_status_progress("完了!", 100)
        
        if comments_file_path:
            self.main_app.log_message("コメント分析ボタンが有効になりました")

    def _get_current_media_settings(self):
        """現在のメディア設定を取得"""
        try:
            return self.main_app.media_frame.get_settings()
        except:
            return {
                'whisper_model': 'base',
                'use_timestamps': True,
                'audio_quality': 'best'
            }


    def _handle_media_failure(self, error_detail):
        """メディア処理失敗処理"""
        self.main_app.log_message("❌ 文字おこしに失敗しました")
        if error_detail:
            self.main_app.log_message(f"詳細: {error_detail}")
        self._update_status_progress("失敗", 0)

    def _log_transcription_stats(self, transcription_text, translation):
        """文字おこし統計ログ出力"""
        self.main_app.log_message("=" * 40)
        self.main_app.log_message("✅ 文字おこし完了！")
        
        # 統計情報をログに表示
        lines = transcription_text.split('\n')
        text_lines = [line for line in lines if line.strip()]
        
        self.main_app.log_message(f"📊 統計情報:")
        self.main_app.log_message(f"   - 総行数: {len(text_lines)}")
        self.main_app.log_message(f"   - 文字数: {len(transcription_text)}")
        
        # 最初と最後の数行をプレビュー
        self.main_app.log_message("🔍 文字おこし内容プレビュー:")
        for i, line in enumerate(text_lines[:3]):
            if line.strip():
                self.main_app.log_message(f"   {line.strip()}")
        
        if len(text_lines) > 6:
            self.main_app.log_message("   ...")
            for line in text_lines[-3:]:
                if line.strip():
                    self.main_app.log_message(f"   {line.strip()}")
        
        # 翻訳結果（ある場合）
        if translation:
            self.main_app.log_message("🌐 翻訳結果:")
            trans_lines = translation.split('\n')[:3]
            for line in trans_lines:
                if line.strip():
                    self.main_app.log_message(f"   🔤 {line.strip()}")

    def _detect_comments_file(self, text_file, url_text):
        """コメントファイル検出"""
        if URLValidator.is_youtube_url(url_text) and text_file:
            output_dir = os.path.dirname(text_file)
            comments_path = os.path.join(output_dir, "youtube_comments.jsonl")
            if os.path.exists(comments_path):
                self.main_app.log_message(f"📝 コメントファイル検出: {os.path.basename(comments_path)}")
                return comments_path
        return None

    def _handle_error(self, error_message):
        """エラー処理"""
        self.main_app.log_message(f"❌ {error_message}")
        self._update_status_progress("エラー", 0)

    def _set_running_state(self, running):
        """実行状態設定"""
        self.main_app.is_running = running
        
        # ボタン状態更新
        execution_buttons = self.main_app.execution_frame.get_all_buttons()
        if running:
            UIHelpers.disable_buttons_during_execution(execution_buttons)
        else:
            UIHelpers.enable_buttons_after_execution(execution_buttons)

    def _update_status_progress(self, status, progress):
        """ステータスとプログレス更新"""
        if status:
            UIHelpers.safe_label_update(self.main_app.execution_frame.status_label, status)
        UIHelpers.safe_progress_update(self.main_app.execution_frame.progress_var, progress)