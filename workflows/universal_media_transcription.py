"""統合メディア処理ワークフロー（Twitter + YouTube対応）"""
import logging
import os
import subprocess
from lib.chrome_connector import ChromeConnector
from lib.video_processor import VideoProcessor
from lib.utils import setup_logging

logger = logging.getLogger(__name__)

class UniversalMediaTranscriptionWorkflow:
    def __init__(self):
        self.chrome = ChromeConnector()
        self.video_processor = VideoProcessor()
    
    def execute(self, media_url, translate=False, target_language="en", whisper_model="base", 
                audio_quality="best", use_timestamps=True, comment_count: int | None = None,
                download_video=True, force_whisper=False):
        """統合メディア処理を実行"""
        logger.info(f"=== 統合メディア処理開始 ===")
        logger.info(f"対象URL: {media_url}")
        logger.info(f"翻訳: {'有効' if translate else '無効'}")
        logger.info(f"Whisperモデル: {whisper_model}")
        logger.info(f"タイムスタンプ: {'有効' if use_timestamps else '無効'}")
        logger.info(f"動画ダウンロード: {'有効（Whisper文字おこし）' if download_video else '無効（DOM字幕優先）'}")
        
        try:
            # URL種別判定
            if self._is_youtube_url(media_url):
                media_type = "youtube"
                query = f"youtube_{self._extract_youtube_id(media_url)}"
            elif self._is_tweet_url(media_url):
                media_type = "twitter"
                query = f"tweet_video_{self._extract_tweet_id(media_url)}"
            else:
                logger.error("サポートされていないURL形式です")
                return None, None, None, None
            
            # 出力ディレクトリ設定
            output_dir = self.video_processor.setup_output_directory(query)

            # 先にYouTube DOM字幕/コメント取得を試みる（ダウンロード前）
            from lib.youtube_scraper import YouTubeScraper
            dom_text = None
            comments = []
            if media_type == "youtube":
                if self.chrome.connect():
                    logger.info("YouTubeページを開いてDOM字幕/コメントを先行取得します")
                    yt = YouTubeScraper(self.chrome)
                    if yt.navigate(media_url):
                        dom_text = yt.extract_dom_subtitles()
                        if comment_count and comment_count > 0:
                            comments = yt.extract_comments(comment_count)
                else:
                    logger.warning("Chrome接続に失敗（DOM字幕/コメント取得はスキップ）")

            # Whisperモデル初期化（DOMが無ければ後で使用）
            whisper_ready = self.video_processor.initialize_whisper(whisper_model)
            if not whisper_ready:
                logger.warning("Whisper初期化に失敗（DOM字幕に期待）")

            # 文字おこし処理の分岐（新ロジック）
            transcription_text = None
            segments_data = None
            video_path = None
            
            # DOM字幕が利用可能かチェック
            has_dom_subtitles = dom_text and len(dom_text) > 50
            
            # 動画ダウンロード処理
            if download_video:
                logger.info("動画ダウンロードが有効のため動画を取得します")
                # 動画ダウンロード（プラットフォーム別）
                if media_type == "youtube":
                    video_path = self._download_youtube_video(media_url, audio_quality)
                else:
                    video_path = self.video_processor.download_video_from_tweet(media_url)

                if not video_path:
                    logger.error("動画ダウンロードに失敗しました")
                    # DOM字幕があればフォールバック
                    if has_dom_subtitles:
                        logger.info("動画ダウンロード失敗のため、DOM字幕を使用します")
                        transcription_text = dom_text
                        segments_data = None
                    else:
                        return None, None, None, None
                else:
                    # 文字おこし方法の選択
                    if force_whisper or not has_dom_subtitles:
                        logger.info("Whisperで文字おこしを実行します")
                        # 動画情報取得
                        video_info = self.video_processor.get_video_info(media_url)
                        transcription_text, segments_data = self.video_processor.transcribe_video(
                            video_path, language="ja", use_timestamps=use_timestamps
                        )
                    else:
                        logger.info("DOM字幕が利用可能のため、DOM字幕を使用します（Whisperスキップ）")
                        transcription_text = dom_text
                        segments_data = None
            else:
                # 動画ダウンロードなし
                if has_dom_subtitles:
                    logger.info("動画ダウンロード無効、DOM字幕を使用します")
                    transcription_text = dom_text
                    segments_data = None
                else:
                    logger.warning("動画ダウンロードが無効でDOM字幕も利用できないため処理を終了します")
                    return None, None, None, None
            
            if not transcription_text:
                logger.error("文字おこしに失敗しました")
                return video_path, None, None, None
            
            # 翻訳（オプション）
            translation = None
            if translate and transcription_text:
                # タイムスタンプ情報を除去してから翻訳
                clean_text = self._remove_timestamps_for_translation(transcription_text)
                translation = self.video_processor.translate_text(clean_text, target_language)
            
            # 動画情報取得（DOMのみで完結した場合でも可能なら取得）
            video_info = self.video_processor.get_video_info(media_url)

            # 結果保存（拡張版）
            text_file = self.video_processor.save_transcription(
                video_path if 'video_path' in locals() else '',
                transcription_text,
                segments_data,
                media_url,
                translation,
                use_timestamps,
                video_info
            )

            # 追加: コメント保存（jsonl）
            if media_type == "youtube" and comments:
                try:
                    import os, json
                    comments_path = os.path.join(self.video_processor.output_dir, "youtube_comments.jsonl")
                    with open(comments_path, 'w', encoding='utf-8') as f:
                        for item in comments:
                            f.write(json.dumps(item, ensure_ascii=False) + "\n")
                    logger.info(f"コメント保存: {comments_path} ({len(comments)})")
                except Exception as e:
                    logger.warning(f"コメント保存エラー: {e}")
            
            if text_file:
                logger.info(f"=== 処理完了 ===")
                logger.info(f"動画: {video_path}")
                logger.info(f"文字おこし: {text_file}")
                logger.info(f"文字数: {len(transcription_text)}")
                return video_path, text_file, transcription_text, translation
            else:
                logger.error("結果保存に失敗しました")
                return video_path, None, transcription_text, translation
                
        except Exception as e:
            logger.error(f"処理エラー: {e}")
            return None, None, None, None
    
    def execute_with_callback(self, url, translate=False, target_language="en", 
                            whisper_model="base", audio_quality="best", 
                            use_timestamps=True, progress_callback=None, comment_count: int | None = None,
                            download_video=True, force_whisper=False):
        """統合メディア処理（コールバック付き）"""
        video_path = None
        text_file = None
        transcription_text = None
        translation = None
        
        try:
            logger.info("=== コールバック付きメディア処理開始 ===")
            logger.info(f"対象URL: {url}")
            logger.info(f"翻訳: {'有効' if translate else '無効'}")
            logger.info(f"Whisperモデル: {whisper_model}")
            logger.info(f"タイムスタンプ: {'有効' if use_timestamps else '無効'}")
            
            # Chrome接続
            from lib.chrome_connector import ChromeConnector
            self.chrome = ChromeConnector()
            
            # 動画処理器初期化
            from lib.video_processor import VideoProcessor
            processor = VideoProcessor()
            processor.setup_output_directory(url)
            processor.initialize_whisper(whisper_model)
            
            # YouTube vs Twitter判定（DOM字幕を先に試行するため、YouTubeはここでDLしない）
            is_youtube = ('youtube.com' in url or 'youtu.be' in url)
            video_path = None
            if not is_youtube:
                logger.info("Twitter動画ダウンロード開始: " + url)
                video_path = processor.download_video_from_tweet(url)
                if not video_path:
                    logger.error("動画ダウンロードに失敗しました")
                    return None, None, None, None
                logger.info(f"動画ダウンロード完了: {video_path}")
            
            # YouTube DOM字幕/コメントの先行取得（DL前に実施）
            from lib.youtube_scraper import YouTubeScraper
            import threading
            import time
            
            dom_text = None
            comments = []
            video_info = None
            
            if is_youtube:
                # 動画情報取得を並行処理で開始
                def get_video_info_async():
                    nonlocal video_info
                    try:
                        video_info = processor.get_video_info(url)
                        if video_info:
                            logger.info(f"動画情報: {video_info}")
                    except Exception as e:
                        logger.warning(f"動画情報取得エラー: {e}")
                
                # 並行処理で動画情報取得開始
                info_thread = threading.Thread(target=get_video_info_async, daemon=True)
                info_thread.start()
                
                # DOM字幕/コメント取得を並行実行
                if self.chrome.connect():
                    logger.info("YouTubeページを開いてDOM字幕/コメントを先行取得します")
                    logger.info(f"コメント取得設定: comment_count={comment_count}")
                    yt = YouTubeScraper(self.chrome)
                    if yt.navigate(url):
                        dom_text = yt.extract_dom_subtitles()
                        logger.info(f"DOM字幕結果: {'取得成功' if dom_text and len(dom_text) > 50 else '取得失敗またはデータ不足'}")
                        if comment_count and comment_count > 0:
                            logger.info(f"コメント取得開始: 最大{comment_count}件")
                            comments = yt.extract_comments(comment_count)
                            logger.info(f"コメント取得完了: {len(comments)}件")
                        else:
                            logger.info("コメント取得はスキップ（comment_count=0または未設定）")
                    else:
                        logger.warning("YouTubeページナビゲーションに失敗")
                else:
                    logger.warning("Chrome接続に失敗（DOM字幕/コメント取得はスキップ）")
                
                # 動画情報取得完了を待機
                info_thread.join(timeout=30)  # 最大30秒待機
                if not video_info:
                    logger.warning("動画情報取得がタイムアウトしました")

            # 文字おこし処理の分岐（賢い判定）
            has_dom_subtitles = dom_text and len(dom_text) > 50
            
            if download_video:
                logger.info("動画ダウンロードが有効のため動画を取得します")
                # 必要に応じて動画をDL
                if is_youtube:
                    logger.info("YouTube動画ダウンロード開始: " + url)
                    video_path = processor.download_youtube_video(url)
                # ここまでで video_path が未設定ならエラー
                if not video_path:
                    logger.error("動画ダウンロードに失敗しました")
                    # DOM字幕があればフォールバック
                    if has_dom_subtitles:
                        logger.info("動画ダウンロード失敗のため、DOM字幕を使用します")
                        transcription_text = dom_text
                        segments_data = None
                    else:
                        return None, None, None, None
                else:
                    # 文字おこし方法の選択
                    if force_whisper or not has_dom_subtitles:
                        logger.info("Whisperで文字おこしを実行します")
                        logger.info(f"文字おこし開始: {video_path}")
                        transcription_text, segments_data = processor.transcribe_video(
                            video_path, 
                            language="ja", 
                            use_timestamps=use_timestamps,
                            progress_callback=progress_callback
                        )
                    else:
                        logger.info("DOM字幕が利用可能のため、DOM字幕を使用します（動画は保存済み）")
                        transcription_text = dom_text
                        segments_data = None
            else:
                # 動画ダウンロードなし
                if has_dom_subtitles:
                    logger.info("動画ダウンロード無効、DOM字幕を使用します")
                    transcription_text = dom_text
                    segments_data = None
                else:
                    logger.warning("動画ダウンロードが無効でDOM字幕も利用できないため処理を終了します")
                    return None, None, None, None
            
            if not transcription_text:
                logger.error("文字おこしに失敗しました")
                return video_path, None, None, None
            
            # 翻訳（必要な場合）
            if translate and transcription_text:
                logger.info("翻訳開始...")
                translation = processor.translate_text(transcription_text, target_language)
                logger.info("翻訳完了")
            
            # 結果保存（DOM字幕のみの場合はvideo_pathが空文字列）
            text_file = processor.save_transcription_advanced(
                video_path=video_path if video_path else '',
                transcription_text=transcription_text,
                segments_data=segments_data,
                video_url=url,
                translation=translation,
                video_info=video_info,
                use_timestamps=use_timestamps
            )

            # コメント保存
            if comments:
                try:
                    import os, json
                    comments_path = os.path.join(processor.output_dir, "youtube_comments.jsonl")
                    with open(comments_path, 'w', encoding='utf-8') as f:
                        for item in comments:
                            f.write(json.dumps(item, ensure_ascii=False) + "\n")
                    logger.info(f"コメント保存: {comments_path} ({len(comments)})")
                except Exception as e:
                    logger.warning(f"コメント保存エラー: {e}")
            
            logger.info("=== 処理完了 ===")
            logger.info(f"動画: {video_path}")
            logger.info(f"文字おこし: {text_file}")
            logger.info(f"文字数: {len(transcription_text)}")
            
            return video_path, text_file, transcription_text, translation
            
        except Exception as e:
            logger.error(f"動画処理エラー: {e}")
            return None, None, None, None
        finally:
            # Chromeを閉じない（GUIクラッシュ防止）
            # if hasattr(self, 'chrome') and self.chrome:
            #     self.chrome.close()
            pass
    
    def _is_youtube_url(self, url):
        """YouTubeURLかどうか判定"""
        youtube_patterns = [
            'youtube.com/watch',
            'youtu.be/',
            'm.youtube.com',
            'youtube.com/shorts',
            'youtube.com/embed'
        ]
        return any(pattern in url.lower() for pattern in youtube_patterns)
    
    def _is_tweet_url(self, url):
        """ツイートURLかどうか判定"""
        try:
            return ('x.com' in url or 'twitter.com' in url) and '/status/' in url
        except:
            return False
    
    def _extract_youtube_id(self, url):
        """YouTubeURLからIDを抽出"""
        try:
            import re
            # 様々なYouTubeURL形式に対応
            patterns = [
                r'youtube\.com/watch\?v=([^&\n]+)',
                r'youtu\.be/([^?\n]+)',
                r'youtube\.com/embed/([^?\n]+)',
                r'youtube\.com/shorts/([^?\n]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            return "unknown"
        except:
            return "unknown"
    
    def _extract_tweet_id(self, url):
        """ツイートURLからIDを抽出"""
        try:
            import re
            match = re.search(r'/status/(\d+)', url)
            return match.group(1) if match else "unknown"
        except:
            return "unknown"
    
    def _remove_timestamps_for_translation(self, text_with_timestamps):
        """翻訳用にタイムスタンプを除去"""
        import re
        # [mm:ss-mm:ss] パターンを除去
        clean_text = re.sub(r'\[\d{2}:\d{2}-\d{2}:\d{2}\]\s*', '', text_with_timestamps)
        return clean_text.strip()
   
    def _download_youtube_video(self, youtube_url, audio_quality="best"):
        """YouTubeから動画をダウンロード（フォールバック付き）"""
        try:
            logger.info(f"YouTube動画ダウンロード開始: {youtube_url}")
            
            # 品質別フォーマット優先順位
            quality_formats = {
                "best": [
                    "best[height<=720]/best[height<=480]/best",
                    "best[ext=mp4]/mp4/best",
                    "bestvideo+bestaudio/best"
                ],
                "good": [
                    "best[height<=720]/best[height<=480]/best",
                    "best[ext=mp4]/mp4/best"
                ],
                "medium": [
                    "best[height<=480]/best",
                    "worst[ext=mp4]/worst"
                ]
            }
            
            format_options = quality_formats.get(audio_quality, quality_formats["best"])
            video_path = os.path.join(self.video_processor.output_dir, "youtube_video.%(ext)s")
            
            for i, format_option in enumerate(format_options):
                logger.info(f"フォーマット試行 {i+1}/{len(format_options)}: {format_option}")
                
                cmd = [
                    "yt-dlp",
                    "--format", format_option,
                    "--output", video_path,
                    "--no-playlist",
                    "--merge-output-format", "mp4",
                    youtube_url
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    for file in os.listdir(self.video_processor.output_dir):
                        if file.startswith("youtube_video."):
                            actual_path = os.path.join(self.video_processor.output_dir, file)
                            logger.info(f"YouTube動画ダウンロード完了: {actual_path}")
                            return actual_path
                    
                    logger.warning(f"フォーマット{i+1}でダウンロード成功したがファイルが見つかりません")
                else:
                    logger.warning(f"フォーマット{i+1}失敗: {result.stderr.strip()[:100]}...")
                    continue
            
            logger.error("全てのフォーマットでYouTube動画ダウンロードに失敗しました")
            return None
                
        except Exception as e:
            logger.error(f"YouTube動画ダウンロードエラー: {e}")
            return None