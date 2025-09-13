"""ツイートリプライ取得ワークフロー"""
import logging
from lib.chrome_connector import ChromeConnector
from lib.twitter_scraper import TwitterScraper
from lib.twitter_parser import TwitterParser
from lib.formatter import Formatter
from lib.utils import setup_logging, validate_query

logger = logging.getLogger(__name__)

class ScrapeRepliesWorkflow:
    def __init__(self):
        self.chrome = ChromeConnector()
        self.scraper = None
        self.parser = TwitterParser()
        self.formatter = Formatter()
    
    def execute(self, tweet_url, count=20, format_type="txt"):
        """リプライ取得を実行"""
        logger.info(f"=== リプライ取得開始 ===")
        logger.info(f"対象ツイート: {tweet_url}")
        logger.info(f"件数: {count}")
        
        try:
            # URL検証
            if not self._validate_tweet_url(tweet_url):
                logger.error("無効なツイートURLです")
                return None
            
            # Chrome接続
            if not self.chrome.connect():
                logger.error("Chrome接続に失敗しました")
                return None
            
            # リプライ取得
            replies = self._scrape_replies(tweet_url, count)
            if not replies:
                return None
            
            # ファイル保存
            query = f"replies_{self._extract_tweet_id(tweet_url)}"
            filepath = self.formatter.save_tweets(replies, query, format_type)
            
            if filepath:
                logger.info(f"=== 処理完了 ===")
                logger.info(f"保存先: {filepath}")
                logger.info(f"リプライ件数: {len(replies)}")
                return filepath
            else:
                logger.error("ファイル保存に失敗しました")
                return None
                
        except Exception as e:
            logger.error(f"処理エラー: {e}")
            return None
    
    def _validate_tweet_url(self, url):
        """ツイートURLの検証"""
        try:
            # X.com または twitter.com のURLで /status/ を含むかチェック
            return ('x.com' in url or 'twitter.com' in url) and '/status/' in url
        except:
            return False
    
    def _extract_tweet_id(self, url):
        """URLからツイートIDを抽出"""
        try:
            # /status/の後の数字部分を抽出
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