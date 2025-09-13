"""Twitter取得 + Claude分析のワークフロー"""
import logging
from lib.chrome_connector import ChromeConnector
from lib.twitter_scraper import TwitterScraper
from lib.twitter_parser import TwitterParser
from lib.claude_automation import ClaudeAutomation
from lib.formatter import Formatter
from lib.utils import setup_logging, validate_query
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class ScrapeAndAnalyzeWorkflow:
    def __init__(self):
        self.chrome = ChromeConnector()
        self.scraper = None
        self.parser = TwitterParser()
        self.claude = None
        self.formatter = Formatter()
    
    def execute(self, query, count=20, format_type="txt", analysis_prompt=None):
        """Twitter取得 + Claude分析を実行"""
        logger.info(f"=== Twitter取得 + Claude分析開始 ===")
        logger.info(f"クエリ: {query}")
        logger.info(f"件数: {count}")
        logger.info(f"フォーマット: {format_type}")
        
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
            
            # Twitter取得
            tweets = self._scrape_tweets(query, count)
            if not tweets:
                return None
            
            # Claude分析
            analysis = self._analyze_with_claude(tweets, analysis_prompt)
            
            # 結果保存
            if analysis:
                filepath = self.formatter.save_with_analysis(tweets, analysis, query, format_type)
            else:
                # 分析失敗時は通常保存
                filepath = self.formatter.save_tweets(tweets, query, format_type)
            
            if filepath:
                logger.info(f"=== 処理完了 ===")
                logger.info(f"保存先: {filepath}")
                logger.info(f"取得件数: {len(tweets)}")
                return filepath
            else:
                logger.error("ファイル保存に失敗しました")
                return None
                
        except Exception as e:
            logger.error(f"処理エラー: {e}")
            return None
    
    def _scrape_tweets(self, query, count):
        """ツイート取得"""
        logger.info("--- ツイート取得中 ---")
        
        try:
            self.scraper = TwitterScraper(self.chrome)
            
            if query.startswith('@'):
                raw_tweets = self.scraper.get_user_tweets(query, count)
            else:
                raw_tweets = self.scraper.search_tweets(query, count)
            
            if not raw_tweets:
                logger.warning("ツイートが取得できませんでした")
                return None
            
            # データ解析
            parsed_tweets = self.parser.parse_tweets(raw_tweets)
            logger.info(f"ツイート取得完了: {len(parsed_tweets)}件")
            
            return parsed_tweets
            
        except Exception as e:
            logger.error(f"ツイート取得エラー: {e}")
            return None
    
    def _analyze_with_claude(self, tweets, custom_prompt=None, chat_url=None):
        """Claude分析（ファイルアップロード版）"""
        logger.info("--- Claude分析中 ---")
        
        try:
            # まず通常ファイルを保存
            temp_filepath = self.formatter.save_tweets(tweets, f"{self.query}_temp", self.format_type)
            if not temp_filepath:
                logger.error("ファイル保存に失敗しました")
                return None
            
            logger.info(f"分析用ファイル作成: {temp_filepath}")
            
            # Claude自動操作でファイルアップロード分析
            self.claude = ClaudeAutomation(self.chrome)
            
            # 新しいタブでClaude開く
            self.chrome.create_new_tab("https://claude.ai")
            
            # ファイルアップロード + 分析
            analysis = self.claude.upload_and_analyze_file(temp_filepath, custom_prompt, chat_url=chat_url)
            
            if analysis:
                logger.info("Claude分析完了")
                return analysis
            else:
                logger.warning("Claude分析に失敗しました")
                return None
                
        except Exception as e:
            logger.error(f"Claude分析エラー: {e}")
            return None
