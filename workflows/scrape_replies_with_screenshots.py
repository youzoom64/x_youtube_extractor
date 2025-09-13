"""リプライ取得 + スクリーンショット撮影ワークフロー"""
import logging
import os
from lib.chrome_connector import ChromeConnector
from lib.twitter_scraper import TwitterScraper
from lib.twitter_parser import TwitterParser
from lib.formatter import Formatter
from lib.screenshot_capture import ScreenshotCapture
from lib.utils import setup_logging, validate_query
from datetime import datetime

logger = logging.getLogger(__name__)

class ScrapeRepliesWithScreenshotsWorkflow:
    def __init__(self):
        self.chrome = ChromeConnector()
        self.scraper = None
        self.parser = TwitterParser()
        self.formatter = Formatter()
        self.screenshot = None
    
    # workflows/scrape_replies_with_screenshots.py の execute メソッドを修正
    def execute(self, tweet_url, count=20, format_type="txt", capture_mode="smart_batch"):
        """リアルタイム撮影版"""
        logger.info(f"=== リアルタイム撮影モード開始 ===")
        
        try:
            if not self._validate_tweet_url(tweet_url) or not self.chrome.connect():
                return None, None, None
            
            # リアルタイム撮影
            replies_data, screenshot_files, screenshot_dir = self._scrape_replies_with_elements(tweet_url, count)
            
            if not replies_data:
                return None, None, None
            
            # テキスト保存
            query = f"replies_{self._extract_tweet_id(tweet_url)}"
            txt_file = self.formatter.save_tweets(replies_data, query, format_type)
            
            # サマリー作成
            if screenshot_files and screenshot_dir:
                self.screenshot = ScreenshotCapture(self.chrome, self.formatter)
                summary_file = self.screenshot.create_summary_file(replies_data, screenshot_files, query, screenshot_dir)
            else:
                summary_file = None
            
            if txt_file and screenshot_files:
                logger.info(f"=== リアルタイム撮影完了 ===")
                return txt_file, screenshot_files, summary_file
            
            return None, None, None
            
        except Exception as e:
            logger.error(f"リアルタイム撮影エラー: {e}")
            return None, None, None
        
    # workflows/scrape_replies_with_screenshots.py の _scrape_replies_with_elements を修正
    def _scrape_replies_with_elements(self, tweet_url, count):
        """リプライデータとスクリーンショットを同時取得"""
        logger.info("--- リアルタイム撮影モード ---")
        
        try:
            # スクリーンショットディレクトリ事前作成
            query = f"replies_{self._extract_tweet_id(tweet_url)}"
            screenshot_dir = self._create_screenshot_directory(query)
            
            self.scraper = TwitterScraper(self.chrome)
            replies_data, screenshot_files = self.scraper.get_tweet_replies_with_elements(tweet_url, count, screenshot_dir)
            
            if not replies_data:
                logger.warning("リプライが取得できませんでした")
                return None, None, None
            
            parsed_replies = self.parser.parse_tweets(replies_data)
            logger.info(f"リアルタイム撮影完了: データ{len(parsed_replies)}件, 画像{len(screenshot_files)}枚")
            
            return parsed_replies, screenshot_files, screenshot_dir
            
        except Exception as e:
            logger.error(f"リアルタイム撮影エラー: {e}")
            return None, None, None
            
    def _create_screenshot_directory(self, query):
        """スクリーンショット保存ディレクトリを作成"""
        from lib.utils import sanitize_filename
        from datetime import datetime
        
        # formatterと同じ命名規則を使用
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = sanitize_filename(query)
        
        # 日付フォルダ
        today = datetime.now().strftime("%Y-%m-%d")
        base_dir = os.path.join("output", "query", today)
        
        # スクリーンショット専用サブフォルダ
        screenshot_dir = os.path.join(base_dir, f"{timestamp}_{safe_query}_screenshots")
        
        os.makedirs(screenshot_dir, exist_ok=True)
        logger.info(f"スクリーンショットディレクトリ作成: {screenshot_dir}")
        
        return screenshot_dir
        
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
    
    def _scrape_replies(self, tweet_url, count):
        """リプライ取得"""
        logger.info("--- リプライ取得中 ---")
        
        try:
            self.scraper = TwitterScraper(self.chrome)
            raw_replies = self.scraper.get_tweet_replies(tweet_url, count)
            
            if not raw_replies:
                logger.warning("リプライが取得できませんでした")
                return None
            
            # データ解析
            parsed_replies = self.parser.parse_tweets(raw_replies)
            logger.info(f"リプライ取得完了: {len(parsed_replies)}件")
            
            return parsed_replies
            
        except Exception as e:
            logger.error(f"リプライ取得エラー: {e}")
            return None
    
    def _capture_screenshots(self, replies, query, capture_mode, tweet_url):
        """スクリーンショット撮影（リプライ特化版）"""
        logger.info("--- リプライスクリーンショット撮影中 ---")
        
        try:
            self.screenshot = ScreenshotCapture(self.chrome, self.formatter)
            
            # リプライページでのスクリーンショット撮影
            screenshot_files = self.screenshot.capture_reply_screenshots(replies, query, capture_mode, tweet_url)
            
            # サマリーファイル作成
            if screenshot_files:
                screenshot_dir = os.path.dirname(screenshot_files[0])
                summary_file = self.screenshot.create_summary_file(replies, screenshot_files, query, screenshot_dir)
            else:
                summary_file = None
            
            return screenshot_files, summary_file
            
        except Exception as e:
            logger.error(f"スクリーンショット撮影エラー: {e}")
            return [], None
        
    def _capture_screenshots_directly(self, reply_elements, replies_data, query):
        """取得済み要素を直接撮影"""
        logger.info("--- 直接スクリーンショット撮影中 ---")
        
        try:
            # スクリーンショットディレクトリ作成
            screenshot_dir = self._create_screenshot_directory(query)
            
            self.screenshot = ScreenshotCapture(self.chrome, self.formatter)
            
            # 要素を直接撮影
            screenshot_files = self.screenshot.capture_reply_elements_directly(
                reply_elements, replies_data, query, screenshot_dir
            )
            
            # サマリーファイル作成
            if screenshot_files:
                summary_file = self.screenshot.create_summary_file(
                    replies_data, screenshot_files, query, screenshot_dir
                )
            else:
                summary_file = None
            
            return screenshot_files, summary_file
            
        except Exception as e:
            logger.error(f"直接スクリーンショット撮影エラー: {e}")
            return [], None