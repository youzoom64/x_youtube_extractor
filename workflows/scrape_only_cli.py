"""CLI用Twitter取得ワークフロー"""
import logging
from lib.chrome_connector import ChromeConnector
from lib.twitter_scraper import TwitterScraper
from lib.twitter_parser import TwitterParser
from lib.formatter import Formatter
from lib.utils import setup_logging, validate_query

logger = logging.getLogger(__name__)

class ScrapeOnlyWorkflowCLI:
    def __init__(self):
        self.chrome = ChromeConnector()
        self.scraper = None
        self.parser = TwitterParser()
        self.formatter = Formatter()
    
    def execute(self, query, count=20, format_type="txt", sort_type="latest"):
        """Twitter取得のみを実行（CLI版）"""
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
            
            # ツイート取得（ソート指定）
            if query.startswith('@'):
                # ユーザーツイート取得（ソート指定なし）
                raw_tweets = self.scraper.get_user_tweets(query, count)
                logger.info("ユーザーツイート取得完了")
            else:
                # 検索ツイート取得（ソート指定あり）
                raw_tweets = self.scraper.search_tweets(query, count, sort_type)
                logger.info(f"検索ツイート取得完了（{sort_type}順）")
            
            if not raw_tweets:
                logger.warning("ツイートが取得できませんでした")
                return None
            
            # データ解析
            logger.info("ツイートデータ解析中...")
            parsed_tweets = self.parser.parse_tweets(raw_tweets)
            
            # ファイル保存
            logger.info("ファイル保存中...")
            filepath = self.formatter.save_tweets(parsed_tweets, query, format_type)
            
            if filepath:
                logger.info(f"=== 処理完了 ===")
                logger.info(f"保存先: {filepath}")
                logger.info(f"取得件数: {len(parsed_tweets)}")
                
                # CLI用の簡潔な結果表示
                print(f"✅ Twitter取得完了")
                print(f"📁 保存先: {filepath}")
                print(f"📊 取得件数: {len(parsed_tweets)}件")
                print(f"🔍 検索クエリ: {query}")
                print(f"📈 ソート順: {sort_type}")
                
                return filepath
            else:
                logger.error("ファイル保存に失敗しました")
                print("❌ ファイル保存に失敗しました")
                return None
                
        except Exception as e:
            logger.error(f"処理エラー: {e}")
            print(f"❌ エラーが発生しました: {e}")
            return None
        finally:
            # Chrome接続は保持（他の処理で使用可能）
            pass
    
    def get_stats(self, tweets):
        """取得したツイートの統計情報を表示"""
        if not tweets:
            return
        
        total_likes = sum(tweet.get('likes', 0) for tweet in tweets)
        total_reposts = sum(tweet.get('reposts', 0) for tweet in tweets)
        total_replies = sum(tweet.get('replies', 0) for tweet in tweets)
        
        avg_likes = total_likes // len(tweets) if tweets else 0
        avg_reposts = total_reposts // len(tweets) if tweets else 0
        avg_replies = total_replies // len(tweets) if tweets else 0
        
        print(f"📊 統計情報:")
        print(f"   平均いいね数: {avg_likes}")
        print(f"   平均リポスト数: {avg_reposts}")
        print(f"   平均リプライ数: {avg_replies}")
        print(f"   総エンゲージメント: {total_likes + total_reposts + total_replies}")
    
    def validate_sort_type(self, sort_type):
        """ソートタイプの妥当性をチェック"""
        valid_sorts = ["latest", "top"]
        if sort_type not in valid_sorts:
            logger.warning(f"無効なソートタイプ: {sort_type}, デフォルト(latest)を使用")
            return "latest"
        return sort_type
    
    def dry_run(self, query, count=5, sort_type="latest"):
        """ドライラン（テスト実行）"""
        logger.info(f"=== ドライラン実行 ===")
        print(f"🧪 テスト実行モード")
        print(f"🔍 クエリ: {query}")
        print(f"📊 件数: {count}")
        print(f"📈 ソート: {sort_type}")
        
        # 少数のツイートで実際に取得テスト
        result = self.execute(query, count, "txt", sort_type)
        
        if result:
            print(f"✅ ドライラン成功")
            print(f"📁 テストファイル: {result}")
        else:
            print(f"❌ ドライラン失敗")
        
        return result