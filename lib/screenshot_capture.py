"""ツイートスクリーンショット撮影機能（効率化版）"""
import os
import time
import logging
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config.twitter_selectors import TWEET_CONTAINER, TIMELINE
from config.settings import (
    SCREENSHOT_ENABLE_PROMOTION_FILTER,
    SCREENSHOT_SCROLL_MULTIPLIER,
    SCREENSHOT_MAX_SCROLLS,
    SCREENSHOT_WAIT_TIME
)
from lib.utils import sanitize_filename
import urllib.parse

logger = logging.getLogger(__name__)

class ScreenshotCapture:
    def __init__(self, chrome_connector, formatter):
        self.chrome = chrome_connector
        self.driver = chrome_connector.driver
        self.formatter = formatter
        
    def capture_tweets_screenshots(self, tweets, query, capture_mode="smart_batch"):
        """
        効率的なツイートスクリーンショット撮影
        
        Args:
            tweets: ツイートデータのリスト
            query: 検索クエリ
            capture_mode: "smart_batch" | "individual" | "full_batch"
        """
        logger.info(f"スクリーンショット撮影開始: {len(tweets)}件 (モード: {capture_mode})")
        logger.info(f"設定: プロモーション除外={SCREENSHOT_ENABLE_PROMOTION_FILTER}, スクロール倍率={SCREENSHOT_SCROLL_MULTIPLIER}")
        
        try:
            # スクリーンショット保存用ディレクトリ作成
            screenshot_dir = self._create_screenshot_directory(query)
            
            if capture_mode == "smart_batch":
                logger.info("smart_batch モードで撮影開始")
                saved_files = self._capture_smart_batch(tweets, query, screenshot_dir)
            elif capture_mode == "individual":
                logger.info("individual モードで撮影開始")
                saved_files = self._capture_individual_tweets(tweets, query, screenshot_dir)
            elif capture_mode == "full_batch":
                logger.info("full_batch モードで撮影開始")
                saved_files = self._capture_full_page_batch(tweets, query, screenshot_dir)
            else:
                logger.info("デフォルトモード（smart_batch）で撮影開始")
                saved_files = self._capture_smart_batch(tweets, query, screenshot_dir)
            
            # 詳細な結果ログ
            tweet_screenshots = [f for f in saved_files if 'tweet_' in f]
            other_files = [f for f in saved_files if 'tweet_' not in f]
            
            logger.info(f"スクリーンショット撮影完了: {len(saved_files)}ファイル")
            logger.info(f"目標件数: {len(tweets)}件")
            logger.info(f"ツイートスクリーンショット: {len(tweet_screenshots)}件")
            logger.info(f"その他ファイル: {len(other_files)}件")
            
            if len(tweet_screenshots) < len(tweets):
                logger.warning(f"⚠️ 撮影件数が不足: 目標{len(tweets)}件に対して{len(tweet_screenshots)}件")
                logger.warning("原因: プロモーションツイート除外、スクロール不足、または要素取得失敗の可能性")
                logger.warning(f"設定確認: プロモーション除外={SCREENSHOT_ENABLE_PROMOTION_FILTER}")
            
            return saved_files
            
        except Exception as e:
            logger.error(f"スクリーンショット撮影エラー: {e}")
            return []
    
    def _capture_smart_batch(self, tweets, query, screenshot_dir):
        """賢い一括撮影：検索結果ページでツイート要素を個別にキャプチャ（プロモーション除外）"""
        saved_files = []
        
        try:
            # クエリの種類を判定
            if query.startswith('@'):
                # ユーザーツイートの場合はユーザーページにアクセス
                username = query.lstrip('@')
                user_url = f"https://x.com/{username}"
                logger.info(f"ユーザーページにアクセス: {user_url}")
                self.driver.get(user_url)
                time.sleep(4)  # ユーザーページの読み込みには時間が必要
                
                # ユーザーページでスクロールしてツイートを読み込み
                target_tweets = len(tweets)
                scroll_target = int(target_tweets * SCREENSHOT_SCROLL_MULTIPLIER)
                self._scroll_to_load_tweets_user_page(scroll_target)
                
            else:
                # 検索クエリの場合は検索結果ページにアクセス
                search_url = f"https://x.com/search?q={urllib.parse.quote_plus(query)}&src=typed_query&f=live"
                logger.info(f"検索結果ページにアクセス: {search_url}")
                self.driver.get(search_url)
                time.sleep(3)
                
                # 検索結果ページでスクロールしてツイートを読み込み
                target_tweets = len(tweets)
                scroll_target = int(target_tweets * SCREENSHOT_SCROLL_MULTIPLIER)
                self._scroll_to_load_tweets(scroll_target)
            
            # ページ上の全ツイート要素を取得
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, TWEET_CONTAINER)
            logger.info(f"ページ上のツイート要素数: {len(tweet_elements)}")
            
            # 設定に基づいてプロモーションツイートを除外
            if SCREENSHOT_ENABLE_PROMOTION_FILTER:
                filtered_elements = self._filter_promoted_tweets(tweet_elements)
                logger.info(f"プロモーション除外後: {len(filtered_elements)}件")
            else:
                filtered_elements = tweet_elements
                logger.info(f"プロモーション除外無効: {len(filtered_elements)}件")
            
            # 各ツイート要素を個別にスクリーンショット
            captured_count = 0
            for i, element in enumerate(filtered_elements):
                if captured_count >= target_tweets:
                    break  # 必要な件数に達したら終了
                    
                try:
                    # ツイート要素が画面内に見えるようにスクロール
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(SCREENSHOT_WAIT_TIME)
                    
                    # ツイート要素のスクリーンショット
                    filename = f"tweet_{captured_count+1:03d}_filtered.png"
                    filepath = os.path.join(screenshot_dir, filename)
                    
                    element.screenshot(filepath)
                    saved_files.append(filepath)
                    
                    captured_count += 1
                    logger.info(f"ツイート {captured_count} スクリーンショット保存: {filename}")
                    
                except Exception as e:
                    logger.warning(f"ツイート {i+1} スクリーンショット失敗: {e}")
                    continue
            
            # 全体ページのスクリーンショットも保存
            if query.startswith('@'):
                full_page_file = os.path.join(screenshot_dir, "user_page_full.png")
            else:
                full_page_file = os.path.join(screenshot_dir, "search_results_full_page.png")
            
            self.driver.save_screenshot(full_page_file)
            saved_files.append(full_page_file)
            
            logger.info(f"スクリーンショット撮影完了: {captured_count}件のツイートを撮影")
            
        except Exception as e:
            logger.error(f"賢い一括撮影エラー: {e}")
        
        return saved_files
    
    def _capture_full_page_batch(self, tweets, query, screenshot_dir):
        """フルページ一括撮影：検索結果ページを分割してキャプチャ"""
        saved_files = []
        
        try:
            # 検索結果ページに移動
            search_url = f"https://x.com/search?q={urllib.parse.quote_plus(query)}&src=typed_query&f=live"
            logger.info(f"検索結果ページにアクセス: {search_url}")
            self.driver.get(search_url)
            time.sleep(3)  # 5秒 → 3秒
            
            # ページを段階的にスクロールしながらスクリーンショット
            viewport_height = self.driver.execute_script("return window.innerHeight")
            scroll_position = 0
            screenshot_count = 0
            max_screenshots = 10
            
            while screenshot_count < max_screenshots:
                # 現在位置のスクリーンショット
                filename = f"search_page_{screenshot_count + 1:02d}.png"
                filepath = os.path.join(screenshot_dir, filename)
                
                self.driver.save_screenshot(filepath)
                saved_files.append(filepath)
                
                logger.info(f"ページスクリーンショット {screenshot_count + 1}: {filename}")
                
                # 下にスクロール
                scroll_position += viewport_height * 0.8  # 少し重複させる
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(2)
                
                # 新しいコンテンツが読み込まれたかチェック
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                if scroll_position >= current_height:
                    break
                
                screenshot_count += 1
            
        except Exception as e:
            logger.error(f"フルページ一括撮影エラー: {e}")
        
        return saved_files
    
    def _scroll_to_load_tweets(self, target_count):
        """指定数のツイートが読み込まれるまでスクロール（修正版）"""
        try:
            # 設定ファイルの値を使用してスクロール回数制限を調整
            max_scrolls = min(SCREENSHOT_MAX_SCROLLS, max(20, target_count // 2))  # 制限を強化
            scroll_count = 0
            last_tweet_count = 0
            no_change_count = 0
            
            logger.info(f"スクロール開始: 目標 {target_count}件, 最大スクロール {max_scrolls}回")
            
            while scroll_count < max_scrolls:
                # 現在のツイート数をチェック
                tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, TWEET_CONTAINER)
                current_count = len(tweet_elements)
                
                logger.info(f"スクロール {scroll_count + 1}: ツイート {current_count} 件読み込み済み")
                
                if current_count >= target_count:
                    logger.info(f"目標のツイート数 {target_count} に到達")
                    break
                
                # 新しいツイートが読み込まれなくなったらループを抜ける
                if current_count == last_tweet_count:
                    no_change_count += 1
                    if no_change_count >= 2:  # 3回 → 2回に短縮
                        logger.info("新しいツイートが読み込まれなくなりました")
                        break
                else:
                    no_change_count = 0
                
                last_tweet_count = current_count
                
                # 下にスクロール
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.0)  # 1.5秒 → 1.0秒（適切な待機時間）
                
                scroll_count += 1
                
            logger.info(f"スクロール完了: {scroll_count}回, 最終ツイート数: {last_tweet_count}件")
                
        except Exception as e:
            logger.warning(f"スクロール処理エラー: {e}")
    
    def _scroll_to_load_tweets_user_page(self, target_count):
        """ユーザーページで指定数のツイートが読み込まれるまでスクロール"""
        try:
            # 設定ファイルの値を使用してスクロール回数制限を調整
            max_scrolls = min(SCREENSHOT_MAX_SCROLLS, max(20, target_count // 2))
            scroll_count = 0
            last_tweet_count = 0
            no_change_count = 0
            
            logger.info(f"ユーザーページスクロール開始: 目標 {target_count}件, 最大スクロール {max_scrolls}回")
            
            while scroll_count < max_scrolls:
                # 現在のツイート数をチェック
                tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, TWEET_CONTAINER)
                current_count = len(tweet_elements)
                
                logger.info(f"ユーザーページスクロール {scroll_count + 1}: ツイート {current_count} 件読み込み済み")
                
                if current_count >= target_count:
                    logger.info(f"目標のツイート数 {target_count} に到達")
                    break
                
                # 新しいツイートが読み込まれなくなったらループを抜ける
                if current_count == last_tweet_count:
                    no_change_count += 1
                    if no_change_count >= 2:  # 2回連続で変化がなければ終了
                        logger.info("ユーザーページで新しいツイートが読み込まれなくなりました")
                        break
                else:
                    no_change_count = 0
                
                last_tweet_count = current_count
                
                # 下にスクロール
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.0)  # 適切な待機時間
                
                scroll_count += 1
                
            logger.info(f"ユーザーページスクロール完了: {scroll_count}回, 最終ツイート数: {last_tweet_count}件")
                
        except Exception as e:
            logger.warning(f"ユーザーページスクロール処理エラー: {e}")
    
    def _create_screenshot_directory(self, query):
        """スクリーンショット保存ディレクトリを作成"""
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
    
    def _is_promoted_tweet(self, tweet_element):
        """ツイートがプロモーション（広告）かどうかチェック（修正版）"""
        try:
            # より具体的なプロモーション検出
            promotion_indicators = [
                "プロモーション",
                "Promoted", 
                "広告",
                "Ad"
            ]
            
            # 要素全体のテキストを取得
            element_text = tweet_element.text
            
            # テキスト内にプロモーション表示があるかチェック
            for indicator in promotion_indicators:
                if indicator in element_text:
                    return True
            
            # より具体的なセレクタでチェック
            try:
                # プロモーション専用の要素を探す
                promotion_element = tweet_element.find_element(By.XPATH, 
                    ".//*[contains(text(), 'プロモーション') or contains(text(), 'Promoted')]")
                if promotion_element:
                    return True
            except:
                pass
                
            return False
            
        except Exception as e:
            logger.debug(f"プロモーション検出エラー: {e}")
            return False  # エラーの場合は通常ツイートとして扱う

    def _filter_promoted_tweets(self, tweet_elements):
        """プロモーションツイートをフィルタリング"""
        filtered_elements = []
        promoted_count = 0
        
        for i, element in enumerate(tweet_elements):
            try:
                if self._is_promoted_tweet(element):
                    promoted_count += 1
                    logger.info(f"ツイート {i+1}: プロモーション検出 - スキップ")
                    continue
                else:
                    filtered_elements.append(element)
            except Exception as e:
                logger.warning(f"ツイート {i+1} フィルタリングエラー: {e}")
                # エラーの場合は含める（安全側に倒す）
                filtered_elements.append(element)
        
        logger.info(f"プロモーション除外: {promoted_count}件をスキップ, {len(filtered_elements)}件を撮影対象")
        return filtered_elements


    def _capture_individual_tweets(self, tweets, query, screenshot_dir):
        """個別ツイートのスクリーンショットを撮影（プロモーション除外）"""
        saved_files = []
        
        # ユーザーページの場合は一括撮影に切り替え
        if query.startswith('@'):
            logger.info("ユーザーツイートのため、一括撮影モードに切り替え")
            return self._capture_smart_batch(tweets, query, screenshot_dir)
        
        for i, tweet in enumerate(tweets):
            try:
                tweet_url = tweet.get('url')
                if not tweet_url:
                    logger.warning(f"ツイート {i+1}: URLが見つかりません")
                    continue
                
                # ツイートページに移動
                logger.info(f"ツイート {i+1}/{len(tweets)}: {tweet_url}")
                self.driver.get(tweet_url)
                time.sleep(1.5)  # 2秒 → 1.5秒
                
                # ツイート要素を探す
                try:
                    tweet_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, TWEET_CONTAINER))
                    )
                    
                    # 設定に基づいてプロモーションチェック
                    if SCREENSHOT_ENABLE_PROMOTION_FILTER and self._is_promoted_tweet(tweet_element):
                        logger.info(f"ツイート {i+1}: プロモーション検出 - スキップ")
                        continue
                    
                    # スクリーンショット撮影
                    filename = f"tweet_{i+1:03d}_{sanitize_filename(tweet.get('username', 'unknown'))}.png"
                    filepath = os.path.join(screenshot_dir, filename)
                    
                    tweet_element.screenshot(filepath)
                    saved_files.append(filepath)
                    
                    logger.info(f"スクリーンショット保存: {filename}")
                    
                except Exception as e:
                    logger.warning(f"ツイート {i+1} スクリーンショット失敗: {e}")
                
                time.sleep(0.8)  # レート制限対策（時間を短縮）
                
            except Exception as e:
                logger.error(f"ツイート {i+1} 処理エラー: {e}")
                continue
        
        return saved_files
    
    def create_summary_file(self, tweets, saved_files, query, screenshot_dir):
        """スクリーンショットのサマリーファイルを作成"""
        try:
            summary_file = os.path.join(screenshot_dir, "screenshot_summary.txt")
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"検索クエリ: {query}\n")
                f.write(f"撮影日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"ツイート数: {len(tweets)}\n")
                f.write(f"スクリーンショット数: {len(saved_files)}\n")
                f.write("=" * 50 + "\n\n")
                
                f.write("📸 スクリーンショット一覧:\n")
                for i, filepath in enumerate(saved_files, 1):
                    filename = os.path.basename(filepath)
                    f.write(f"{i:3d}. {filename}\n")
                
                f.write("\n" + "=" * 50 + "\n")
                f.write("📋 対応ツイートデータ:\n")
                
                for i, tweet in enumerate(tweets, 1):
                    f.write(f"\n{i:3d}. {tweet.get('username', '')} - {tweet.get('datetime', '')}\n")
                    f.write(f"     URL: {tweet.get('url', '')}\n")
                    f.write(f"     本文: {tweet.get('text', '')[:100]}...\n")
                    f.write(f"     エンゲージメント: いいね {tweet.get('likes', 0)} | リポスト {tweet.get('reposts', 0)}\n")
            
            logger.info(f"サマリーファイル作成: {summary_file}")
            return summary_file
            
        except Exception as e:
            logger.error(f"サマリーファイル作成エラー: {e}")
            return None
        


    def capture_reply_screenshots(self, replies, query, capture_mode="smart_batch", tweet_url=None):
        """
        リプライ専用スクリーンショット撮影
        
        Args:
            replies: リプライデータのリスト
            query: 検索クエリ
            capture_mode: "smart_batch" | "individual" | "full_batch"
            tweet_url: 元ツイートのURL
        """
        logger.info(f"リプライスクリーンショット撮影開始: {len(replies)}件 (モード: {capture_mode})")
        
        try:
            # スクリーンショット保存用ディレクトリ作成
            screenshot_dir = self._create_screenshot_directory(query)
            
            if capture_mode == "smart_batch":
                saved_files = self._capture_replies_smart_batch(replies, query, screenshot_dir, tweet_url)
            elif capture_mode == "individual":
                saved_files = self._capture_individual_replies(replies, query, screenshot_dir)
            elif capture_mode == "full_batch":
                saved_files = self._capture_replies_full_page(replies, query, screenshot_dir, tweet_url)
            else:
                saved_files = self._capture_replies_smart_batch(replies, query, screenshot_dir, tweet_url)
            
            logger.info(f"リプライスクリーンショット撮影完了: {len(saved_files)}ファイル")
            return saved_files
            
        except Exception as e:
            logger.error(f"リプライスクリーンショット撮影エラー: {e}")
            return []

    def _capture_replies_smart_batch(self, replies, query, screenshot_dir, tweet_url):
        """リプライページでの効率的一括撮影"""
        saved_files = []
        
        try:
            # 元ツイートページに移動（リプライが表示される）
            logger.info(f"元ツイートページにアクセス: {tweet_url}")
            self.driver.get(tweet_url)
            time.sleep(5)
            
            # リプライセクションまでスクロール
            self._scroll_to_replies_section()
            
            # リプライを段階的に読み込み
            self._scroll_to_load_replies(len(replies))
            
            # ページ上のリプライ要素を取得
            reply_elements = self.driver.find_elements(By.CSS_SELECTOR, TWEET_CONTAINER)
            logger.info(f"ページ上のツイート要素数: {len(reply_elements)}")
            
            # メインツイートをスキップしてリプライのみ撮影
            reply_elements = reply_elements[1:]  # 最初の要素（メインツイート）をスキップ
            
            # プロモーション除外
            filtered_elements = self._filter_promoted_tweets(reply_elements)
            
            # 各リプライ要素を個別にスクリーンショット
            captured_count = 0
            for i, element in enumerate(filtered_elements):
                if captured_count >= len(replies):
                    break
                    
                try:
                    # リプライ要素が画面内に見えるようにスクロール
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(1)
                    
                    # リプライ要素のスクリーンショット
                    filename = f"reply_{captured_count+1:03d}_from_page.png"
                    filepath = os.path.join(screenshot_dir, filename)
                    
                    element.screenshot(filepath)
                    saved_files.append(filepath)
                    
                    captured_count += 1
                    logger.info(f"リプライ {captured_count} スクリーンショット保存: {filename}")
                    
                except Exception as e:
                    logger.warning(f"リプライ {i+1} スクリーンショット失敗: {e}")
                    continue
            
            # メインツイート + リプライの全体ページも保存
            full_page_file = os.path.join(screenshot_dir, "tweet_with_replies_full_page.png")
            self.driver.save_screenshot(full_page_file)
            saved_files.append(full_page_file)
            
            logger.info(f"リプライ効率的撮影完了: {captured_count}件のリプライを撮影")
            
        except Exception as e:
            logger.error(f"リプライ効率的撮影エラー: {e}")
        
        return saved_files

    def _capture_individual_replies(self, replies, query, screenshot_dir):
        """個別リプライのスクリーンショット撮影"""
        saved_files = []
        
        for i, reply in enumerate(replies):
            try:
                reply_url = reply.get('url')
                if not reply_url:
                    logger.warning(f"リプライ {i+1}: URLが見つかりません")
                    continue
                
                # リプライページに移動
                logger.info(f"リプライ {i+1}/{len(replies)}: {reply_url}")
                self.driver.get(reply_url)
                time.sleep(3)
                
                # リプライ要素のスクリーンショット
                try:
                    reply_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, TWEET_CONTAINER))
                    )
                    
                    filename = f"reply_{i+1:03d}_{sanitize_filename(reply.get('username', 'unknown'))}.png"
                    filepath = os.path.join(screenshot_dir, filename)
                    
                    reply_element.screenshot(filepath)
                    saved_files.append(filepath)
                    
                    logger.info(f"リプライスクリーンショット保存: {filename}")
                    
                except Exception as e:
                    logger.warning(f"リプライ {i+1} スクリーンショット失敗: {e}")
                    # フォールバック: ページ全体
                    filename = f"reply_{i+1:03d}_fullpage.png"
                    filepath = os.path.join(screenshot_dir, filename)
                    self.driver.save_screenshot(filepath)
                    saved_files.append(filepath)
                
                time.sleep(2)  # レート制限対策
                
            except Exception as e:
                logger.error(f"リプライ {i+1} 処理エラー: {e}")
                continue
        
        return saved_files

    def _capture_replies_full_page(self, replies, query, screenshot_dir, tweet_url):
        """リプライページの段階的フルページ撮影"""
        saved_files = []
        
        try:
            # 元ツイートページに移動
            logger.info(f"元ツイートページにアクセス: {tweet_url}")
            self.driver.get(tweet_url)
            time.sleep(5)
            
            # リプライセクションまでスクロール
            self._scroll_to_replies_section()
            
            # ページを段階的にスクロールしながらスクリーンショット
            viewport_height = self.driver.execute_script("return window.innerHeight")
            scroll_position = 0
            screenshot_count = 0
            max_screenshots = 15
            
            while screenshot_count < max_screenshots:
                # 現在位置のスクリーンショット
                filename = f"reply_page_{screenshot_count + 1:02d}.png"
                filepath = os.path.join(screenshot_dir, filename)
                
                self.driver.save_screenshot(filepath)
                saved_files.append(filepath)
                
                logger.info(f"リプライページスクリーンショット {screenshot_count + 1}: {filename}")
                
                # 下にスクロール
                scroll_position += viewport_height * 0.8
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(2)
                
                # 新しいリプライが読み込まれたかチェック
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                if scroll_position >= current_height:
                    break
                
                screenshot_count += 1
            
        except Exception as e:
            logger.error(f"リプライフルページ撮影エラー: {e}")
        
        return saved_files

    def _scroll_to_replies_section(self):
        """リプライセクションまでスクロール"""
        try:
            # メインツイートの下にスクロール
            main_tweet = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="tweet"]')
            self.driver.execute_script("arguments[0].scrollIntoView();", main_tweet)
            time.sleep(2)
            
            # さらに下にスクロールしてリプライを表示
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(1)
                
        except Exception as e:
            logger.warning(f"リプライセクションスクロールエラー: {e}")

    def _scroll_to_load_replies(self, target_count):
        """指定数のリプライが読み込まれるまでスクロール"""
        try:
            max_scrolls = 15
            scroll_count = 0
            last_reply_count = 0
            
            while scroll_count < max_scrolls:
                # 現在のリプライ数をチェック（メインツイートを除く）
                reply_elements = self.driver.find_elements(By.CSS_SELECTOR, TWEET_CONTAINER)
                current_count = max(0, len(reply_elements) - 1)  # メインツイートを除く
                
                logger.info(f"リプライ読み込みスクロール {scroll_count + 1}: リプライ {current_count} 件読み込み済み")
                
                if current_count >= target_count:
                    logger.info(f"目標のリプライ数 {target_count} に到達")
                    break
                
                # 新しいリプライが読み込まれなくなったらループを抜ける
                if current_count == last_reply_count:
                    logger.info("新しいリプライが読み込まれなくなりました")
                    break
                
                last_reply_count = current_count
                
                # 下にスクロール
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                scroll_count += 1
                
        except Exception as e:
            logger.warning(f"リプライ読み込みスクロールエラー: {e}")

    def capture_reply_elements_directly(self, reply_elements, replies_data, query, screenshot_dir):
        """要素を直接撮影（ページ再読み込み不要）"""
        logger.info(f"要素直接撮影開始: {len(reply_elements)}個")
        
        saved_files = []
        
        try:
            for i, element in enumerate(reply_elements):
                if i >= len(replies_data):
                    break
                
                try:
                    # 要素が画面内に見えるようにスクロール
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(1)
                    
                    # 要素の有効性チェック
                    if not element.is_displayed():
                        logger.warning(f"リプライ {i+1}: 要素が非表示")
                        continue
                    
                    # スクリーンショット撮影
                    reply_data = replies_data[i]
                    username = reply_data.get('username', 'unknown').replace('@', '')
                    filename = f"reply_{i+1:03d}_{username}.png"
                    filepath = os.path.join(screenshot_dir, filename)
                    
                    element.screenshot(filepath)
                    saved_files.append(filepath)
                    
                    logger.info(f"リプライ {i+1} スクリーンショット保存: {filename}")
                    
                except Exception as e:
                    logger.warning(f"リプライ {i+1} スクリーンショット失敗: {e}")
                    continue
            
            logger.info(f"要素直接撮影完了: {len(saved_files)}ファイル")
            return saved_files
            
        except Exception as e:
            logger.error(f"要素直接撮影エラー: {e}")
            return saved_files