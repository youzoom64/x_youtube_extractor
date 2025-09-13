"""Twitter スクレイピング処理"""
import time
import logging
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config.settings import SCROLL_DELAY, REQUEST_DELAY, MAX_RETRIES, PAGE_LOAD_TIMEOUT
from config.twitter_selectors import *

logger = logging.getLogger(__name__)

class TwitterScraper:
    def __init__(self, chrome_connector):
        self.chrome = chrome_connector
        self.driver = chrome_connector.driver
        # 高速化用の短縮待機時間
        self.fast_wait = WebDriverWait(self.driver, 5)
        self.quick_wait = WebDriverWait(self.driver, 2)
        
    def search_tweets(self, query, count=20, sort_type="latest"):
            """高速化ツイート検索（修正版）"""
            logger.info(f"高速検索開始: {query}")
            
            try:
                # 直接検索URLにアクセス（ナビゲーション省略）
                import urllib.parse
                encoded_query = urllib.parse.quote_plus(query)
                search_url = f"https://x.com/search?q={encoded_query}&src=typed_query"
                if sort_type == "latest":
                    search_url += "&f=live"
                
                logger.info(f"直接URL: {search_url}")
                self.driver.get(search_url)
                
                # 適切な待機時間
                time.sleep(2.5)  # 1秒 → 2.5秒（検索結果の読み込みには時間が必要）
                
                # ツイート収集（高速化版）
                tweets = self._collect_tweets_fast(count)
                logger.info(f"高速取得完了: {len(tweets)}件")
                return tweets
                
            except Exception as e:
                logger.error(f"高速検索エラー: {e}")
                return []

    def _switch_to_latest(self):
        """最新順に切り替え"""
        try:
            print("🔄 最新順に切り替え中...")
            
            # 「最新」タブを探してクリック
            latest_selectors = [
                'a[href*="f=live"]',  # 最新順のURL
                'span:contains("最新")',
                'div[data-testid="latest"]',
                'a[role="tab"]:contains("最新")'
            ]
            
            latest_button = None
            
            # XPathで「最新」テキストを探す
            try:
                latest_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '最新')]")
                for elem in latest_elements:
                    if elem.is_displayed():
                        # クリック可能な親要素を探す
                        parent = elem.find_element(By.XPATH, "./ancestor::a | ./ancestor::div[@role='tab'] | ./ancestor::button")
                        if parent:
                            latest_button = parent
                            print("✅ XPathで最新ボタン発見")
                            break
            except Exception as e:
                print(f"XPath検索エラー: {e}")
            
            # CSSセレクタでも試す
            if not latest_button:
                for selector in latest_selectors:
                    try:
                        if ':contains(' in selector:
                            continue  # スキップ
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in elements:
                            if elem.is_displayed():
                                latest_button = elem
                                print(f"✅ CSSセレクタで最新ボタン発見: {selector}")
                                break
                        if latest_button:
                            break
                    except:
                        continue
            
            if latest_button:
                latest_button.click()
                print("🖱️ 最新ボタンをクリックしました")
                time.sleep(1.5)  # 3秒 → 1.5秒
                return True
            else:
                print("❌ 最新ボタンが見つかりません")
                
                # 代替方法：URLを直接変更
                try:
                    current_url = self.driver.current_url
                    if 'search?q=' in current_url and 'f=live' not in current_url:
                        if '&' in current_url:
                            new_url = current_url + '&f=live'
                        else:
                            new_url = current_url + '&f=live'
                        
                        print(f"🔄 URLを直接変更: {new_url}")
                        self.driver.get(new_url)
                        time.sleep(2.5)  # 5秒 → 2.5秒
                        return True
                except Exception as e:
                    print(f"URL変更エラー: {e}")
                
                return False
                
        except Exception as e:
            print(f"❌ 最新順切り替えエラー: {e}")
            return False
        
    def get_user_tweets(self, username, count=20):
        """特定ユーザーのツイートを取得（修正版）"""
        # @を除去
        username = username.lstrip('@')
        user_url = f"https://x.com/{username}"
        
        logger.info(f"ユーザーツイート取得開始: @{username}")
        
        try:
            self.driver.get(user_url)
            time.sleep(4)  # 3秒 → 4秒（ユーザーページの読み込みには時間が必要）
            
            # ユーザーページの場合は通常の収集方法を使用
            tweets = self._collect_tweets_safe(count)
            logger.info(f"取得完了: {len(tweets)}件")
            return tweets
            
        except Exception as e:
            logger.error(f"ユーザーツイート取得エラー: {e}")
            return []
    
    def _collect_tweets_safe(self, target_count):
        """安全なツイート収集（ユーザーページ用）"""
        tweets = []
        last_height = 0
        no_new_tweets_count = 0
        max_scrolls = min(15, max(8, target_count // 2))  # スクロール回数制限
        
        logger.info(f"安全収集開始: 目標{target_count}件, 最大スクロール{max_scrolls}回")
        
        while len(tweets) < target_count and no_new_tweets_count < 3:
            try:
                # 現在表示されているツイートを取得
                tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, TWEET_CONTAINER)
                
                new_tweets_found = False
                for element in tweet_elements[-10:]:  # 最新10件をチェック
                    tweet_data = self._extract_tweet_data(element)
                    if tweet_data and tweet_data not in tweets:
                        tweets.append(tweet_data)
                        new_tweets_found = True
                        
                        if len(tweets) >= target_count:
                            break
                
                if not new_tweets_found:
                    no_new_tweets_count += 1
                else:
                    no_new_tweets_count = 0
                
                # スクロール
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.0)  # 適切な待機時間
                
                # 高さをチェック（無限スクロール対策）
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                if current_height == last_height:
                    no_new_tweets_count += 1
                last_height = current_height
                
            except Exception as e:
                logger.error(f"ツイート収集エラー: {e}")
                break
        
        logger.info(f"安全収集完了: {len(tweets)}件取得")
        return tweets[:target_count]
    
    def _navigate_to_twitter(self):
        """Twitterにアクセス"""
        try:
            current_url = self.driver.current_url
            if 'x.com' not in current_url and 'twitter.com' not in current_url:
                self.driver.get("https://x.com")
                time.sleep(5)
            return True
        except Exception as e:
            logger.error(f"Twitter アクセスエラー: {e}")
            return False
    
    def _perform_search(self, query):
        """検索を実行"""
        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                # 検索ボックスを探す
                search_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, SEARCH_BOX))
                )
                
                # 検索実行
                search_box.clear()
                search_box.send_keys(query)
                search_box.send_keys(Keys.ENTER)
                
                time.sleep(5)
                logger.info(f"検索実行: {query}")
                return True
                
            except Exception as e:
                retry_count += 1
                logger.warning(f"検索失敗 ({retry_count}/{MAX_RETRIES}): {e}")
                time.sleep(REQUEST_DELAY)
        
        return False
    
    def _collect_tweets(self, target_count):
        """ツイートを収集"""
        tweets = []
        last_height = 0
        no_new_tweets_count = 0
        
        while len(tweets) < target_count and no_new_tweets_count < 5:
            try:
                # 現在表示されているツイートを取得
                tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, TWEET_CONTAINER)
                
                new_tweets_found = False
                for element in tweet_elements[-10:]:  # 最新10件をチェック
                    tweet_data = self._extract_tweet_data(element)
                    if tweet_data and tweet_data not in tweets:
                        tweets.append(tweet_data)
                        new_tweets_found = True
                        
                        if len(tweets) >= target_count:
                            break
                
                if not new_tweets_found:
                    no_new_tweets_count += 1
                else:
                    no_new_tweets_count = 0
                
                # スクロール
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCROLL_DELAY)  # 0.5秒（既に短縮済み）
                
                # 高さをチェック（無限スクロール対策）
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                if current_height == last_height:
                    no_new_tweets_count += 1
                last_height = current_height
                
            except Exception as e:
                logger.error(f"ツイート収集エラー: {e}")
                break
        
        return tweets[:target_count]

    def _collect_tweets_fast(self, target_count):
        """高速化ツイート収集（修正版）"""
        tweets = []
        scroll_count = 0
        max_scrolls = min(20, max(10, target_count // 3))  # スクロール回数制限を適切に設定
        last_tweet_count = 0
        no_change_count = 0
        
        logger.info(f"高速収集開始: 目標{target_count}件, 最大スクロール{max_scrolls}回")
        
        while len(tweets) < target_count and scroll_count < max_scrolls:
            try:
                # 現在表示されている要素のみ取得
                tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, TWEET_CONTAINER)
                current_count = len(tweet_elements)
                
                logger.info(f"スクロール {scroll_count + 1}: 要素{current_count}個, ツイート{len(tweets)}件")
                
                # 新しいツイートが読み込まれなくなったらループを抜ける
                if current_count == last_tweet_count:
                    no_change_count += 1
                    if no_change_count >= 3:  # 3回連続で変化がなければ終了
                        logger.info("新しいツイートが読み込まれなくなりました")
                        break
                else:
                    no_change_count = 0
                
                last_tweet_count = current_count
                
                # バッチ処理で高速データ抽出
                new_tweets = self._extract_tweets_batch(tweet_elements[-10:])
                
                for tweet in new_tweets:
                    if tweet and tweet not in tweets:
                        tweets.append(tweet)
                        if len(tweets) >= target_count:
                            break
                
                if len(tweets) >= target_count:
                    break
                
                # 高速スクロール（待機時間を適切に設定）
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(0.8)  # 0.3秒 → 0.8秒（適切な待機時間）
                
                scroll_count += 1
                
            except Exception as e:
                logger.debug(f"スクロール {scroll_count} エラー: {e}")
                break
        
        logger.info(f"高速収集完了: {len(tweets)}件取得, {scroll_count}回スクロール")
        return tweets[:target_count]
    
    def _extract_tweets_batch(self, elements):
        """バッチ処理でデータ抽出（高速化）"""
        tweets = []
        
        for element in elements:
            try:
                # JavaScriptで一括データ取得
                tweet_data = self.driver.execute_script("""
                    var element = arguments[0];
                    try {
                        var textElement = element.querySelector('[data-testid="tweetText"]');
                        var timeElement = element.querySelector('time');
                        var usernameElement = element.querySelector('[data-testid="User-Name"] a');
                        var linkElement = element.querySelector('[data-testid="tweet"] a[href*="/status/"]');
                        
                        return {
                            text: textElement ? textElement.innerText : '',
                            datetime: timeElement ? timeElement.getAttribute('datetime') : '',
                            username: usernameElement ? usernameElement.innerText : '',
                            url: linkElement ? linkElement.href : '',
                            likes: 0,
                            reposts: 0,
                            replies: 0,
                            views: 0
                        };
                    } catch(e) {
                        return null;
                    }
                """, element)
                
                if tweet_data and tweet_data.get('text'):
                    tweets.append(tweet_data)
                    
            except Exception as e:
                logger.debug(f"要素抽出エラー: {e}")
                continue
        
        return tweets



    def _extract_tweet_data(self, element):
        """個別ツイートからデータを抽出（強化された例外処理）"""
        try:
            # 事前チェック: 有効なツイート要素かどうか
            if not element or not element.is_displayed():
                return None
            
            # 軽量プロモーションチェック
            if 'promoted' in element.get_attribute('outerHTML').lower():
                return None
            # ツイート本文（軽量版）
            text = ""
            try:
                text = self.driver.execute_script("""
                    var element = arguments[0];
                    var textElement = element.querySelector('[data-testid="tweetText"]') || 
                                    element.querySelector('[lang] span');
                    if (!textElement) return '';
                    return textElement.textContent || textElement.innerText || '';
                """, element)
            except:
                # 最小限のフォールバック
                try:
                    text_elem = element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                    text = text_elem.text if text_elem else ""
                except:
                    try:
                        text_elem = element.find_element(By.CSS_SELECTOR, '[lang] span')
                        text = text_elem.text if text_elem else ""
                    except:
                        text = ""
            
            # 投稿時間（例外処理付き）
            datetime_str = ""
            try:
                time_elem = element.find_element(By.CSS_SELECTOR, TWEET_TIME)
                datetime_str = time_elem.get_attribute('datetime') if time_elem else ""
            except:
                logger.debug("時間要素が見つかりません")
            
            # ユーザー名（軽量版）
            username = ""
            try:
                username_elem = element.find_element(By.CSS_SELECTOR, USERNAME)
                username = username_elem.text if username_elem else ""
            except:
                username = ""
            
            # ツイートURL（軽量版）
            url = ""
            try:
                link_elem = element.find_element(By.CSS_SELECTOR, TWEET_LINK)
                url = link_elem.get_attribute('href') if link_elem else ""
            except:
                url = ""
            
            # エンゲージメント数
            engagement = self._extract_engagement(element)
            
            return {
                'text': text.strip(),
                'datetime': datetime_str,
                'username': username,
                'url': url,
                **engagement
            }
            
        except Exception as e:
            logger.debug(f"ツイートデータ抽出エラー: {e}")
            return None
        
    def _extract_engagement(self, element):
        """エンゲージメント数を抽出（シンプル版）"""
        engagement = {
            'replies': 0,
            'reposts': 0,
            'likes': 0,
            'views': 0
        }
        
        try:
            # リプライ数
            reply_elems = element.find_elements(By.CSS_SELECTOR, '[data-testid="reply"] span')
            for elem in reply_elems:
                text = elem.text.strip()
                if text and self._is_number_like(text):
                    engagement['replies'] = self._parse_count(text)
                    logger.debug(f"リプライ数取得: {text} -> {engagement['replies']}")
                    break
            
            # リポスト数
            repost_elems = element.find_elements(By.CSS_SELECTOR, '[data-testid="retweet"] span')
            for elem in repost_elems:
                text = elem.text.strip()
                if text and self._is_number_like(text):
                    engagement['reposts'] = self._parse_count(text)
                    logger.debug(f"リポスト数取得: {text} -> {engagement['reposts']}")
                    break
            
            # いいね数
            like_elems = element.find_elements(By.CSS_SELECTOR, '[data-testid="like"] span')
            for elem in like_elems:
                text = elem.text.strip()
                if text and self._is_number_like(text):
                    engagement['likes'] = self._parse_count(text)
                    logger.debug(f"いいね数取得: {text} -> {engagement['likes']}")
                    break
            
            # 表示数 - JavaScriptで確実に取得
            try:
                views_text = self.driver.execute_script("""
                    var element = arguments[0];
                    var labels = element.querySelectorAll('[aria-label]');
                    for (var i = 0; i < labels.length; i++) {
                        var label = labels[i].getAttribute('aria-label');
                        if (label && label.includes('件の表示')) {
                            var match = label.match(/(\\d[\\d,]*(?:\\.\\d+)?[万KM]?)\\s*件の表示/);
                            return match ? match[1] : '';
                        }
                    }
                    return '';
                """, element)
                
                if views_text:
                    engagement['views'] = self._parse_count(views_text)
                    logger.debug(f"表示数取得: {views_text} -> {engagement['views']}")
                    
            except Exception as e:
                logger.debug(f"表示数取得エラー: {e}")
                
        except Exception as e:
            logger.debug(f"エンゲージメント抽出エラー: {e}")
        
        logger.debug(f"最終エンゲージメント: {engagement}")
        return engagement

    def _is_number_like(self, text):
        """数値っぽい文字列かチェック"""
        if not text:
            return False
        # 数字、カンマ、ピリオド、K、M、万のみ含む文字列
        import re
        return bool(re.match(r'^[\d,.\sKM万]+$', text))
    
    def _parse_count(self, count_str):
        """カウント文字列を数値に変換"""
        if not count_str:
            return 0
        
        try:
            # 「1.2K」「3.4M」などの形式に対応
            count_str = count_str.replace(',', '').strip()
            
            if count_str.endswith('K'):
                return int(float(count_str[:-1]) * 1000)
            elif count_str.endswith('M'):
                return int(float(count_str[:-1]) * 1000000)
            elif count_str.endswith('万'):
                return int(float(count_str[:-1]) * 10000)
            else:
                return int(count_str)
        except:
            return 0
        
    def get_tweet_replies(self, tweet_url, count=20, sort_type="latest"):
        """特定ツイートのリプライを取得"""
        logger.info(f"リプライ取得開始: {tweet_url}")
        
        try:
            # ツイートページにアクセス
            self.driver.get(tweet_url)
            time.sleep(5)
            
            # リプライセクションまでスクロール
            self._scroll_to_replies_section()
            
            # リプライを収集
            replies = self._collect_replies(count)
            logger.info(f"リプライ取得完了: {len(replies)}件")
            return replies
            
        except Exception as e:
            logger.error(f"リプライ取得エラー: {e}")
            return []

    def get_tweet_replies_with_elements(self, tweet_url, count=20, screenshot_dir=None):
        """リプライ取得と同時にスクリーンショット撮影"""
        logger.info(f"リアルタイム撮影モード開始: {tweet_url}")
        
        try:
            self.driver.get(tweet_url)
            time.sleep(5)
            self._scroll_to_replies_section()
            
            replies_data = []
            screenshot_files = []
            
            last_height = 0
            no_new_replies_count = 0
            max_scrolls = 20
            scroll_count = 0
            
            while len(replies_data) < count and scroll_count < max_scrolls and no_new_replies_count < 5:
                current_elements = self.driver.find_elements(By.CSS_SELECTOR, TWEET_CONTAINER)
                new_replies_found = False
                
                for element in current_elements:
                    # if len(replies_data) == 0 and current_elements.index(element) == 0:
                    #     continue
                    
                    if self._is_reply_tweet(element):
                        reply_data = self._extract_tweet_data(element)
                        
                        if reply_data and reply_data not in replies_data:
                            replies_data.append(reply_data)
                            
                            # ★即座にスクリーンショット撮影
                            if screenshot_dir:
                                try:
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                    time.sleep(0.5)
                                    
                                    username = reply_data.get('username', 'unknown').replace('@', '')
                                    filename = f"reply_{len(replies_data):03d}_{username}.png"
                                    filepath = os.path.join(screenshot_dir, filename)
                                    
                                    element.screenshot(filepath)
                                    screenshot_files.append(filepath)
                                    logger.info(f"リプライ {len(replies_data)} 即時撮影: {filename}")
                                    
                                except Exception as e:
                                    logger.warning(f"リプライ {len(replies_data)} 即時撮影失敗: {e}")
                            
                            new_replies_found = True
                            if len(replies_data) >= count:
                                break
                
                if not new_replies_found:
                    no_new_replies_count += 1
                else:
                    no_new_replies_count = 0
                
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCROLL_DELAY)
                scroll_count += 1
            
            logger.info(f"リアルタイム撮影完了: データ{len(replies_data)}件, 画像{len(screenshot_files)}枚")
            return replies_data, screenshot_files
            
        except Exception as e:
            logger.error(f"リアルタイム撮影エラー: {e}")
            return [], []

    def _scroll_to_replies_section(self):
        """リプライセクションまでスクロール"""
        try:
            # メインツイートを探してスクロール
            main_tweet = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="tweet"]')
            self.driver.execute_script("arguments[0].scrollIntoView();", main_tweet)
            time.sleep(2)
            
            # リプライ表示のため追加スクロール
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(1)
                
        except Exception as e:
            logger.warning(f"リプライセクションスクロールエラー: {e}")

    def _collect_replies(self, target_count):
        """リプライを収集"""
        replies = []
        last_height = 0
        no_new_replies_count = 0
        
        while len(replies) < target_count and no_new_replies_count < 5:
            try:
                # 現在表示されているツイート要素を取得
                tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, TWEET_CONTAINER)
                
                new_replies_found = False
                for element in tweet_elements:
                    # メインツイートをスキップ（最初の要素は通常メインツイート）
                    if len(replies) == 0 and tweet_elements.index(element) == 0:
                        continue
                    
                    # リプライかどうかチェック
                    if self._is_reply_tweet(element):
                        reply_data = self._extract_tweet_data(element)
                        if reply_data and reply_data not in replies:
                            replies.append(reply_data)
                            new_replies_found = True
                            
                            if len(replies) >= target_count:
                                break
                
                if not new_replies_found:
                    no_new_replies_count += 1
                else:
                    no_new_replies_count = 0
                
                # スクロール
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCROLL_DELAY)
                
                # 高さをチェック（無限スクロール対策）
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                if current_height == last_height:
                    no_new_replies_count += 1
                last_height = current_height
                
            except Exception as e:
                logger.error(f"リプライ収集エラー: {e}")
                break
        
        return replies[:target_count]

    def _is_reply_tweet(self, element):
        """ツイートがリプライかどうか判定"""
        try:
            # リプライの特徴を探す
            reply_indicators = [
                '[data-testid="reply"]',  # リプライアイコン
                'svg[aria-label*="返信"]',
                'svg[aria-label*="Reply"]',
            ]
            
            for indicator in reply_indicators:
                if element.find_elements(By.CSS_SELECTOR, indicator):
                    return True
            
            # テキスト内に「@」から始まる返信があるかチェック
            element_text = element.text
            if element_text.strip().startswith('@'):
                return True
                
            return True  # デフォルトでリプライとして扱う（メインツイート以外）
            
        except Exception as e:
            logger.debug(f"リプライ判定エラー: {e}")
            return True