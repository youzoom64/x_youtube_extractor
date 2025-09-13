"""動画文字おこしワークフロー"""
import logging
from lib.chrome_connector import ChromeConnector
from lib.video_processor import VideoProcessor
from lib.utils import setup_logging

logger = logging.getLogger(__name__)

class VideoTranscriptionWorkflow:
    def __init__(self):
        self.chrome = ChromeConnector()
        self.video_processor = VideoProcessor()
    
    def execute(self, tweet_url, translate=False, target_language="en", whisper_model="base"):
        """動画文字おこしを実行（既存互換性維持）"""
        logger.info(f"=== 動画文字おこし開始 ===")
        logger.info(f"対象ツイート: {tweet_url}")
        logger.info(f"翻訳: {'有効' if translate else '無効'}")
        logger.info(f"Whisperモデル: {whisper_model}")
        
        try:
            # URL検証
            if not self._validate_tweet_url(tweet_url):
                logger.error("無効なツイートURLです")
                return None, None, None, None
            
            # 出力ディレクトリ設定
            query = f"video_{self._extract_tweet_id(tweet_url)}"
            output_dir = self.video_processor.setup_output_directory(query)
            
            # Whisperモデル初期化
            if not self.video_processor.initialize_whisper(whisper_model):
                logger.error("Whisperモデル初期化に失敗しました")
                return None, None, None, None
            
            # 動画ダウンロード
            video_path = self.video_processor.download_video_from_tweet(tweet_url)
            if not video_path:
                logger.error("動画ダウンロードに失敗しました")
                return None, None, None, None
            
            # 文字おこし（デフォルトでタイムスタンプ有効）
            transcription_text, segments_data = self.video_processor.transcribe_video(
                video_path, language="ja", use_timestamps=True
            )
            
            if not transcription_text:
                logger.error("文字おこしに失敗しました")
                return video_path, None, None, None
            
            # 翻訳（オプション）
            translation = None
            if translate and transcription_text:
                # タイムスタンプ付きテキストから純粋なテキストを抽出
                clean_text = self._extract_clean_text(transcription_text)
                translation = self.video_processor.translate_text(clean_text, target_language)
            
            # 結果保存（互換性維持：use_timestamps=True, video_info=None）
            text_file = self.video_processor.save_transcription(
                video_path, transcription_text, segments_data, tweet_url, 
                translation, use_timestamps=True, video_info=None
            )
            
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
    
    def _validate_tweet_url(self, url):
        """ツイートURLの検証"""
        try:
            return ('x.com' in url or 'twitter.com' in url) and '/status/' in url
        except:
            return False
    
    def _extract_tweet_id(self, url):
        """URLからツイートIDを抽出"""
        try:
            import re
            match = re.search(r'/status/(\d+)', url)
            return match.group(1) if match else "unknown"
        except:
            return "unknown"
    
    def _extract_clean_text(self, text_with_timestamps):
        """タイムスタンプ付きテキストから純粋なテキストを抽出"""
        import re
        # [mm:ss-mm:ss] パターンを除去
        clean_text = re.sub(r'\[\d{2}:\d{2}-\d{2}:\d{2}\]\s*', '', text_with_timestamps)
        return clean_text.strip()