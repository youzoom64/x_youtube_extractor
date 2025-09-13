"""Twitter取得 + スクリーンショット撮影ワークフロー（同時実行版）"""
import logging
import time
from lib.chrome_connector import ChromeConnector
from lib.twitter_scraper import TwitterScraper
from lib.twitter_parser import TwitterParser
from lib.formatter import Formatter
from lib.screenshot_capture import ScreenshotCapture
from lib.utils import setup_logging, validate_query
from config.settings import SCREENSHOT_MAX_SCROLLS, SCREENSHOT_SCROLL_MULTIPLIER
from datetime import datetime
import os
from urllib.parse import quote

logger = logging.getLogger(__name__)

class ScrapeWithScreenshotsWorkflow:
    def __init__(self):
        self.chrome = ChromeConnector()
        self.scraper = None
        self.parser = TwitterParser()
        self.formatter = Formatter()
        self.screenshot = None
    
    def execute(self, query_or_url, count=20, format_type="txt", sort_type_or_capture_mode="latest", capture_mode=None):
        """統合ハブ: URL判定で適切な処理に振り分け"""
        
        if self._is_tweet_url(query_or_url):
            # リプライ処理に振り分け
            logger.info("リプライURLを検出、リプライ専用処理に移行します")
            from workflows.scrape_replies_with_screenshots import ScrapeRepliesWithScreenshotsWorkflow
            reply_workflow = ScrapeRepliesWithScreenshotsWorkflow()
            capture_mode = sort_type_or_capture_mode  # 引数の読み替え
            return reply_workflow.execute(query_or_url, count, format_type, capture_mode)
        else:
            # 通常の検索処理
            logger.info(f"=== Twitter検索 + スクリーンショット同時実行開始 ===")
            sort_type = sort_type_or_capture_mode
            capture_mode = capture_mode or "individual"
            return self._execute_normal_mode(query_or_url, count, format_type, sort_type, capture_mode)

    def _execute_normal_mode(self, query, count, format_type, sort_type, capture_mode):
        """従来の通常処理"""
        try:
            # 入力チェック
            is_valid, error_msg = validate_query(query)
            if not is_valid:
                logger.error(f"入力エラー: {error_msg}")
                return None, None, None
            
            # Chrome接続
            if not self.chrome.connect():
                logger.error("Chrome接続に失敗しました")
                return None, None, None
            
            # 同時実行でツイート取得とスクリーンショット撮影
            tweets, screenshot_files = self._execute_simultaneously(query, count, sort_type, capture_mode)
            
            if not tweets:
                logger.error("ツイートが取得できませんでした")
                return None, None, None
            
            # テキストファイル保存
            txt_file = self.formatter.save_tweets(tweets, query, format_type)
            
            if txt_file:
                logger.info(f"=== 処理完了 ===")
                logger.info(f"テキストファイル: {txt_file}")
                logger.info(f"スクリーンショット: {len(screenshot_files)}件")
                return txt_file, screenshot_files, None
            else:
                logger.error("テキストファイル保存に失敗しました")
                return None, None, None
                
        except Exception as e:
            logger.error(f"処理エラー: {e}")
            return None, None, None
    
    def _execute_simultaneously(self, query, count, sort_type, capture_mode):
        """ツイート取得とスクリーンショットを同時実行"""
        if query.startswith('@'):
            return self._execute_user_simultaneous(query, count, capture_mode)
        else:
            return self._execute_search_simultaneous(query, count, sort_type, capture_mode)
    
    def _execute_user_simultaneous(self, query, count, capture_mode):
        """ユーザーページで同時実行"""
        username = query.lstrip('@')
        user_url = f"https://x.com/{username}"
        
        logger.info(f"ユーザーページ同時実行開始: {user_url}")
        
        # 1回だけページアクセス
        self.chrome.driver.get(user_url)
        time.sleep(3.0)  # ページ読み込み待機
        
        # 同時実行でツイート取得とスクリーンショット撮影
        tweets, screenshot_files = self._capture_tweets_and_screenshots_simultaneously(
            count, capture_mode, username, is_user_page=True
        )
        
        return tweets, screenshot_files
    
    def _execute_search_simultaneous(self, query, count, sort_type, capture_mode):
        """検索ページで同時実行"""
        search_url = f"https://x.com/search?q={quote(query)}&src=typed_query&f=live"
        
        logger.info(f"検索ページ同時実行開始: {search_url}")
        
        # 1回だけページアクセス
        self.chrome.driver.get(search_url)
        time.sleep(2.5)
        
        # 同時実行でツイート取得とスクリーンショット撮影
        tweets, screenshot_files = self._capture_tweets_and_screenshots_simultaneously(
            count, capture_mode, query, is_user_page=False
        )
        
        return tweets, screenshot_files
    
    def _capture_tweets_and_screenshots_simultaneously(self, target_count, capture_mode, query, is_user_page=False):
        """同時実行のメインメソッド"""
        logger.info(f"同時実行開始: 目標{target_count}件, モード{capture_mode}")
        
        tweets = []
        screenshot_files = []
        processed_count = 0
        scroll_count = 0
        # 設定値に基づいてスクロール回数を調整（より多く読み込めるように強化）
        calculated_scrolls = int(max(20, target_count * SCREENSHOT_SCROLL_MULTIPLIER))
        max_scrolls = min(SCREENSHOT_MAX_SCROLLS, calculated_scrolls)
        seen_links = set()
        
        # スクリーンショット保存先ディレクトリ作成
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_dir = f"output/query/{time.strftime('%Y-%m-%d')}/{timestamp}_{query}_screenshots"
        os.makedirs(output_dir, exist_ok=True)
        
        while processed_count < target_count and scroll_count < max_scrolls:
            scroll_count += 1
            
            # 現在のページからツイート要素を取得
            tweet_elements = self.chrome.driver.find_elements("css selector", 'article[data-testid="tweet"]')
            
            # 新しいツイートを処理（URLで重複判定）
            for element in tweet_elements:
                if processed_count >= target_count:
                    break
                    
                try:
                    # ツイート情報を取得
                    tweet_data = self._extract_tweet_data(element, processed_count + 1)
                    if tweet_data:
                        # 既に処理済みのツイートはスキップ（URL基準）
                        link = tweet_data.get("link")
                        if not link or link in seen_links:
                            continue
                        seen_links.add(link)
                        
                        tweets.append(tweet_data)
                        
                        # スクリーンショット撮影
                        if capture_mode == "individual":
                            logger.debug(f"個別モードでスクリーンショット撮影: ツイート{processed_count + 1}")
                            screenshot_file = self._capture_tweet_screenshot(element, processed_count + 1, output_dir)
                            if screenshot_file:
                                screenshot_files.append(screenshot_file)
                                logger.debug(f"スクリーンショット成功: {screenshot_file}")
                            else:
                                logger.warning(f"スクリーンショット失敗: ツイート{processed_count + 1}")
                        elif capture_mode == "smart_batch":
                            # smart_batchモードでも個別スクリーンショットを撮影
                            logger.debug(f"smart_batchモードでスクリーンショット撮影: ツイート{processed_count + 1}")
                            screenshot_file = self._capture_tweet_screenshot(element, processed_count + 1, output_dir)
                            if screenshot_file:
                                screenshot_files.append(screenshot_file)
                                logger.debug(f"スクリーンショット成功: {screenshot_file}")
                            else:
                                logger.warning(f"スクリーンショット失敗: ツイート{processed_count + 1}")
                        
                        processed_count += 1
                        logger.info(f"同時処理完了: {processed_count}/{target_count}")
                        
                except Exception as e:
                    logger.warning(f"ツイート {processed_count + 1} 処理失敗: {e}")
                    continue
            
            # スクロールして次のツイートを読み込み
            if processed_count < target_count:
                self._scroll_to_load_more()
                time.sleep(1.0)
        
        logger.info(f"同時実行完了: ツイート{len(tweets)}件, スクリーンショット{len(screenshot_files)}件")
        if len(screenshot_files) == 0:
            logger.warning("⚠️ スクリーンショットが0件です。原因を調査してください。")
            logger.info(f"キャプチャモード: {capture_mode}")
            logger.info(f"出力ディレクトリ: {output_dir}")
        return tweets, screenshot_files
    
    def _extract_tweet_data(self, element, index):
        """ツイート要素からデータを抽出（修正版）"""
        try:
            # テキスト（フォールバック付き）
            text = ""
            try:
                text_element = element.find_element("css selector", '[data-testid="tweetText"]')
                text = text_element.text if text_element else ""
            except:
                try:
                    text_element = element.find_element("css selector", '[lang] span')
                    text = text_element.text if text_element else ""
                except:
                    text = ""
            
            # リンク（例外処理付き）
            link = ""
            try:
                link_element = element.find_element("css selector", 'a[href*="/status/"]')
                link = link_element.get_attribute("href") if link_element else ""
            except:
                link = ""
            
            # ユーザー名（例外処理付き）
            username = ""
            try:
                username_element = element.find_element("css selector", 'div[data-testid="User-Name"] span')
                username = username_element.text if username_element else ""
            except:
                try:
                    username_element = element.find_element("css selector", 'a[href*="/"]')
                    username = username_element.text if username_element else ""
                except:
                    username = ""
            
            # エンゲージメント数を取得
            engagement = self._extract_engagement_numbers(element)
            
            # 基本的なツイートデータ構造
            tweet_data = {
                "index": index,
                "text": text,
                "link": link,
                "username": username,
                "timestamp": time.time(),
                "raw_element": element,
                **engagement  # エンゲージメント数を追加
            }
            
            return tweet_data
            
        except Exception as e:
            logger.warning(f"ツイートデータ抽出失敗: {e}")
            return None

    def _extract_engagement_numbers(self, element):
        """エンゲージメント数を抽出"""
        engagement = {
            'replies': 0,
            'reposts': 0,
            'likes': 0,
            'views': 0
        }
        
        try:
            # JavaScript で直接取得（確実）
            engagement_data = self.chrome.driver.execute_script("""
                var element = arguments[0];
                var result = {replies: 0, reposts: 0, likes: 0, views: 0};
                
                // aria-label から一括取得
                var labels = element.querySelectorAll('[aria-label]');
                for (var i = 0; i < labels.length; i++) {
                    var label = labels[i].getAttribute('aria-label');
                    if (!label) continue;
                    
                    // リプライ数
                    var replyMatch = label.match(/(\\d+(?:,\\d+)*(?:\\.\\d+)?[万KM]?)\\s*件の返信/);
                    if (replyMatch) result.replies = replyMatch[1];
                    
                    // リポスト数
                    var retweetMatch = label.match(/(\\d+(?:,\\d+)*(?:\\.\\d+)?[万KM]?)\\s*件のリポスト/);
                    if (retweetMatch) result.reposts = retweetMatch[1];
                    
                    // いいね数
                    var likeMatch = label.match(/(\\d+(?:,\\d+)*(?:\\.\\d+)?[万KM]?)\\s*件のいいね/);
                    if (likeMatch) result.likes = likeMatch[1];
                    
                    // 表示数
                    var viewMatch = label.match(/(\\d+(?:,\\d+)*(?:\\.\\d+)?[万KM]?)\\s*件の表示/);
                    if (viewMatch) result.views = viewMatch[1];
                }
                
                // span 内の数値も確認
                var spans = element.querySelectorAll('[data-testid="reply"] span, [data-testid="retweet"] span, [data-testid="like"] span');
                for (var j = 0; j < spans.length; j++) {
                    var text = spans[j].textContent.trim();
                    if (/^[\\d,\\.万KM]+$/.test(text)) {
                        var parent = spans[j].closest('[data-testid]');
                        if (parent) {
                            var testid = parent.getAttribute('data-testid');
                            if (testid === 'reply' && !result.replies) result.replies = text;
                            else if (testid === 'retweet' && !result.reposts) result.reposts = text;
                            else if (testid === 'like' && !result.likes) result.likes = text;
                        }
                    }
                }
                
                return result;
            """, element)
            
            # 数値変換
            for key, value in engagement_data.items():
                if value:
                    engagement[key] = self._parse_count_simple(str(value))
                    
        except Exception as e:
            logger.debug(f"エンゲージメント取得エラー: {e}")
        
        logger.debug(f"エンゲージメント取得結果: {engagement}")
        return engagement

    def _parse_count_simple(self, count_str):
        """数値文字列を数値に変換"""
        if not count_str:
            return 0
        
        try:
            count_str = count_str.replace(',', '').strip()
            
            if count_str.endswith('万'):
                return int(float(count_str[:-1]) * 10000)
            elif count_str.endswith('K'):
                return int(float(count_str[:-1]) * 1000)
            elif count_str.endswith('M'):
                return int(float(count_str[:-1]) * 1000000)
            else:
                return int(count_str)
        except:
            return 0
    
    def _capture_tweet_screenshot(self, element, index, output_dir):
        """個別ツイートのスクリーンショット撮影"""
        try:
            # ファイル名
            filename = f"tweet_{index:03d}.png"
            filepath = os.path.join(output_dir, filename)
            
            # スクリーンショット撮影
            element.screenshot(filepath)
            
            logger.info(f"スクリーンショット保存: {filename}")
            return filepath
            
        except Exception as e:
            logger.warning(f"スクリーンショット撮影失敗: {e}")
            return None
    
    def _scroll_to_load_more(self):
        """次のツイートを読み込むためにスクロール"""
        try:
            self.chrome.driver.execute_script("window.scrollBy(0, 1000);")
        except Exception as e:
            logger.warning(f"スクロール失敗: {e}")
    
    # 既存の個別メソッドは削除（同時実行に置き換え）
    def _scrape_tweets(self, query, count, sort_type):
        """このメソッドは使用しない（同時実行に置き換え）"""
        logger.warning("個別ツイート取得は非推奨です。同時実行を使用してください。")
        return None
    
    def _capture_screenshots(self, tweets, query, capture_mode):
        """このメソッドは使用しない（同時実行に置き換え）"""
        logger.warning("個別スクリーンショット撮影は非推奨です。同時実行を使用してください。")
        return [], None
    
    def _is_tweet_url(self, text):
        """ツイートURLかどうか判定"""
        try:
            return ('x.com' in text or 'twitter.com' in text) and '/status/' in text
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