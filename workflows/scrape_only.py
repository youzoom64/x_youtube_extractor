"""Twitter取得のみのワークフロー"""
import logging
from lib.chrome_connector import ChromeConnector
from lib.twitter_scraper import TwitterScraper
from lib.twitter_parser import TwitterParser
from lib.formatter import Formatter
from lib.utils import setup_logging, validate_query

logger = logging.getLogger(__name__)

class ScrapeOnlyWorkflow:
    def __init__(self):
        self.chrome = ChromeConnector()
        self.scraper = None
        self.parser = TwitterParser()
        self.formatter = Formatter()
    
    def execute(self, query, count=20, format_type="txt", sort_type="latest"):
        """Twitter取得のみを実行"""
        logger.info(f"=== Twitter取得開始 ===")
        logger.info(f"クエリ: {query}")
        logger.info(f"件数: {count}")
        logger.info(f"フォーマット: {format_type}")
        logger.info(f"ソート: {sort_type}")
        
        try:
            # 入力チェック
            is_valid, error_msg = validate_query(query)
            if not is_valid:
                logger.error(f"入力エラー: {error_msg}")
                return None
            
            # Chrome接続
            if not self.chrome.connect():
                logger.error("Chrome接続に失敗しました")
                return None
            
            self.scraper = TwitterScraper(self.chrome)
            
            # ツイート取得
            if query.startswith('@'):
                raw_tweets = self.scraper.get_user_tweets(query, count)
            else:
                raw_tweets = self.scraper.search_tweets(query, count, sort_type)  # sort_type追加
            
            if not raw_tweets:
                logger.warning("ツイートが取得できませんでした")
                return None
            
            # データ解析
            parsed_tweets = self.parser.parse_tweets(raw_tweets)
            
            # ファイル保存
            filepath = self.formatter.save_tweets(parsed_tweets, query, format_type)
            
            if filepath:
                logger.info(f"=== 処理完了 ===")
                logger.info(f"保存先: {filepath}")
                logger.info(f"取得件数: {len(parsed_tweets)}")
                return filepath
            else:
                logger.error("ファイル保存に失敗しました")
                return None
                
        except Exception as e:
            logger.error(f"処理エラー: {e}")
            return None