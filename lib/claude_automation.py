"""Claude Web版自動操作"""
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config.claude_selectors import *

logger = logging.getLogger(__name__)

class ClaudeAutomation:
    def __init__(self, chrome_connector):
        self.chrome = chrome_connector
        self.driver = chrome_connector.driver
        self.fast_wait = WebDriverWait(self.driver, 10)
        
    def analyze_tweets(self, tweets, prompt_template=None):
        """ツイートデータをClaudeで分析"""
        logger.info("Claude分析開始")
        
        try:
            # Claudeページに移動
            if not self._navigate_to_claude():
                return None
            
            # プロンプト作成
            prompt = self._create_analysis_prompt(tweets, prompt_template)
            
            # メッセージ送信
            response = self._send_message(prompt)
            
            logger.info("Claude分析完了")
            return response
            
        except Exception as e:
            logger.error(f"Claude分析エラー: {e}")
            return None
    
    def _navigate_to_claude(self):
        """Claudeページに移動（シンプル版）"""
        try:
            print("🌐 Claude.aiへのナビゲーション開始...")
            
            current_url = self.driver.current_url
            if 'claude.ai' not in current_url:
                self.driver.get("https://claude.ai")
            
            time.sleep(1.2)  # 待機最適化（短縮）
            
            print(f"📍 現在のURL: {self.driver.current_url}")
            print(f"📄 ページタイトル: {self.driver.title}")
            print("✅ Claude.aiアクセス完了（ログイン状態は手動確認済み前提）")
            
            return True
            
        except Exception as e:
            print(f"❌ Claude.aiアクセスエラー: {e}")
            return False
    
    def _create_analysis_prompt(self, tweets, template=None):
        """分析用プロンプトを作成"""
        if template:
            return template.format(tweets=tweets)
        
        # デフォルトプロンプト
        prompt = "以下のツイートデータを分析してください。\n\n"
        prompt += "【分析内容】\n"
        prompt += "1. 全体的な傾向\n"
        prompt += "2. エンゲージメントの高いツイートの特徴\n"
        prompt += "3. 主要なトピック\n\n"
        prompt += "【データ】\n"
        
        for i, tweet in enumerate(tweets[:10], 1):  # 最初の10件のみ
            prompt += f"{i}. {tweet.get('text', '')}\n"
            prompt += f"   いいね: {tweet.get('likes', 0)}, リポスト: {tweet.get('reposts', 0)}\n\n"
        
        return prompt
 
    def _send_message(self, message):
        """Claudeにメッセージを送信（柔軟なセレクタ対応）"""
        try:
            print(f"💬 メッセージ送信開始: {message[:50]}...")
            print(f"🌐 現在のURL: {self.driver.current_url}")
            
            # 1. テキスト入力エリアを探す
            print("🔍 テキスト入力エリアを探しています...")
            
            text_input_selectors = [
                'div[contenteditable="true"]',
                'textarea',
                'div[data-testid="chat-input"]',
                'div[role="textbox"]',
                'div[aria-label*="メッセージ"]',
                'input[type="text"]'
            ]
            
            text_input = None
            for selector in text_input_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            text_input = element
                            print(f"✅ テキスト入力エリア発見: {selector}")
                            break
                    if text_input:
                        break
                except Exception as e:
                    print(f"❌ セレクタ '{selector}' でエラー: {e}")
                    continue
            
            if not text_input:
                print("❌ テキスト入力エリアが見つかりません")
                print("🔍 手動確認: Claudeのチャット画面が表示されていますか？")
                return None
            
            # 2. メッセージを高速・確実に入力（改良版）
            print("⌨️ メッセージを高速入力中...")
            try:
                self._fast_fill_text(text_input, message)
                print("✅ メッセージ入力完了")
                time.sleep(0.2)
            except Exception as e:
                print(f"❌ メッセージ入力エラー: {e}")
                return None
            
            # 3. 送信ボタンを探す
            print("🔍 送信ボタンを探しています...")
            
            send_button_selectors = [
                'button[type="submit"]',
                'button[aria-label*="送信"]',
                'button[aria-label*="Send"]',
                'button[data-testid="send-button"]',
                'button:has(svg)',
                'button[disabled="false"]:last-of-type'
            ]
            
            send_button = None
            for selector in send_button_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            send_button = button
                            print(f"✅ 送信ボタン発見: {selector}")
                            break
                    if send_button:
                        break
                except:
                    continue
            
            # 送信ボタンが見つからない場合、Enterキーで送信を試す
            if not send_button:
                print("🔄 送信ボタンが見つからないため、Enterキーで送信を試します...")
                try:
                    from selenium.webdriver.common.keys import Keys
                    text_input.send_keys(Keys.RETURN)
                    print("✅ Enterキーで送信しました")
                    # Enterキー送信後、送信ボタンを再取得
                    time.sleep(1)
                    for selector in send_button_selectors:
                        try:
                            buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for button in buttons:
                                if button.is_displayed():
                                    send_button = button
                                    break
                            if send_button:
                                break
                        except:
                            continue
                except Exception as e:
                    print(f"❌ Enterキー送信エラー: {e}")
                    return None
            else:
                # 送信ボタンをクリック
                try:
                    send_button.click()
                    print("✅ 送信ボタンをクリックしました")
                except Exception as e:
                    print(f"❌ 送信ボタンクリックエラー: {e}")
                    return None
            
            # 4. 送信ボタン監視でレスポンス完了を待機
            print("⏳ 送信ボタン監視でレスポンス完了を待機...")
            response = self._wait_for_response_with_button_monitoring(send_button)
            
            if response:
                print("✅ レスポンス取得完了")
                return response
            else:
                print("❌ レスポンス取得失敗")
                return None
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ メッセージ送信全体エラー: {error_msg}")
            
            # タイムアウトエラーの詳細をログに記録
            if "timeout" in error_msg.lower():
                logger.error(f"タイムアウトエラー詳細: {error_msg}")
                logger.error(f"現在のURL: {self.driver.current_url if self.driver else 'unknown'}")
                logger.error("対策: タイムアウト時間を延長し、再試行メカニズムを実装済み")
            else:
                logger.error(f"メッセージ送信エラー: {error_msg}")
            return None

    def _fast_fill_text(self, element, text):
        """contenteditable/textarea へ改行を保持して即座に貼り付ける"""
        try:
            tag = (element.tag_name or '').lower()
            is_contenteditable = element.get_attribute('contenteditable') in ['true', 'plaintext-only']
            if is_contenteditable:
                escaped = text.replace("\\", "\\\\").replace("`", "\\`")
                # 改行は <br> に変換して貼り付け
                js = (
                    "var el=arguments[0];"
                    "el.innerHTML='';"
                    "var html=arguments[1].split('\\n').map(x=>x.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')).join('<br>');"
                    "el.innerHTML=html;"
                    "var ev=new Event('input',{bubbles:true});el.dispatchEvent(ev);"
                )
                self.driver.execute_script(js, element, text)
            elif tag == 'textarea' or tag == 'input':
                # value を直接設定して input イベントを発火
                js = (
                    "var el=arguments[0]; el.value=arguments[1];"
                    "var ev=new Event('input',{bubbles:true}); el.dispatchEvent(ev);"
                )
                self.driver.execute_script(js, element, text)
            else:
                # フォールバック: 通常の send_keys
                element.clear()
                element.send_keys(text)
        except Exception as e:
            # 最後のフォールバック
            element.clear()
            element.send_keys(text)

    def _wait_for_response_with_button_monitoring(self, send_button):
        """ボタンのaria-label変化を監視してレスポンス完了を待機"""
        try:
            print("⏳ ボタン状態変化を監視中...")
            
            max_wait_time = 180  # 120秒 → 180秒に延長
            start_time = time.time()
            
            # ボタンが「応答を停止」になるまで待機（応答生成開始）
            while time.time() - start_time < 15:  # 10秒 → 15秒に延長
                try:
                    # 停止ボタンを探す
                    stop_button = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="応答を停止"]')
                    if stop_button:
                        print("✅ 応答生成開始を確認（停止ボタン出現）")
                        break
                except:
                    pass
                time.sleep(1)  # 0.5秒 → 1秒に延長
            
            # ボタンが「メッセージを送信」に戻るまで待機（応答生成完了）
            print("⏳ 応答生成完了を待機中...")
            completion_start = time.time()
            
            while time.time() - completion_start < max_wait_time:
                try:
                    # 送信ボタンが戻ってきたかチェック
                    send_button = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="メッセージを送信"]')
                    if send_button:
                        print("✅ 応答生成完了を確認（送信ボタン復活）")
                        break
                except:
                    pass
                time.sleep(2)  # 1秒 → 2秒に延長（安定性向上）
            
            # 少し待ってから最新の応答を取得
            time.sleep(2)
            print("🔍 最新応答を取得中...")
            
            # 最新の応答を取得
            response_selectors = [
                'div[data-message-author="assistant"]',
                'div[data-is-streaming="false"]',
                'div[role="article"]',
                'div[data-testid="conversation-turn"]'
            ]
            
            for selector in response_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        latest_element = elements[-1]  # 最新の応答
                        response_text = latest_element.text.strip()
                        if response_text and len(response_text) > 10:
                            print(f"✅ 最新応答取得: {response_text[:100]}...")
                            return response_text
                except Exception as e:
                    continue
            
            print("❌ 最新応答の取得に失敗")
            return None
            
        except Exception as e:
            print(f"❌ ボタン監視エラー: {e}")
            return self._wait_for_response()

    def _wait_for_response(self, timeout=60):
        """Claudeのレスポンスを待機（従来版）"""
        try:
            print("⏳ レスポンス待機開始...")
            
            # 複数の方法でレスポンスを探す
            response_selectors = [
                'div[data-is-streaming="false"]',
                'div[data-message-author="assistant"]',
                'div[role="article"]',
                'div[data-testid="conversation-turn"]',
                'div:contains("Claude")',
                'p, div'  # 最後の手段
            ]
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                for selector in response_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        # 最新の要素を取得
                        for element in reversed(elements[-5:]):  # 最新5個をチェック
                            text = element.text.strip()
                            if text and len(text) > 10:  # 十分な長さのテキスト
                                print(f"✅ レスポンス発見: {text[:100]}...")
                                return text
                                
                    except:
                        continue
                
                time.sleep(2)
            
            print("❌ レスポンス待機タイムアウト")
            return None
            
        except Exception as e:
            print(f"❌ レスポンス待機エラー: {e}")
            return None
    
    def upload_file(self, file_path):
        """ファイルをアップロード（エクスプローラーを開かない版）"""
        try:
            print(f"📤 ファイルアップロード開始: {file_path}")
            
            # ファイル存在確認
            import os
            if not os.path.exists(file_path):
                print(f"❌ ファイルが存在しません: {file_path}")
                return False
            
            print(f"✅ ファイル存在確認OK")
            
            # Step 1: + ボタンをクリック
            print("🔍 + ボタンを探してクリック...")
            plus_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="input-menu-plus"]')
            plus_button.click()
            time.sleep(2)
            
            # Step 2: 既存のファイル入力要素を直接探す（クリックしない）
            print("🔍 既存のファイル入力要素を探しています...")
            
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
            print(f"   ページ内のファイル入力要素: {len(file_inputs)} 個")
            
            if not file_inputs:
                print("❌ ファイル入力要素が見つかりません")
                return False
            
            file_input = file_inputs[0]  # 最初の要素を使用
            print("✅ ファイル入力要素を発見")
            
            # Step 3: ファイルパスを直接送信（エクスプローラーダイアログを開かない）
            print("🔍 ファイルパスを直接送信...")
            
            abs_path = os.path.abspath(file_path)
            print(f"📄 送信するファイルパス: {abs_path}")
            
            # 非表示の要素でも操作できるようにする
            self.driver.execute_script("""
                arguments[0].style.display = 'block';
                arguments[0].style.visibility = 'visible';
                arguments[0].style.opacity = '1';
                arguments[0].style.position = 'absolute';
                arguments[0].style.top = '-9999px';
            """, file_input)
            
            # 直接ファイルパスを設定
            file_input.send_keys(abs_path)
            print("📤 ファイルパスを直接送信しました")
            
            time.sleep(2)
            print("✅ ファイルアップロード処理完了")
            
            logger.info(f"ファイルアップロード完了: {file_path}")
            return True

        except Exception as e:
            print(f"❌ ファイルアップロード全体エラー: {e}")
            logger.error(f"ファイルアップロードエラー: {e}")
            return False

    def upload_and_analyze_file(self, file_path, analysis_prompt=None, chat_url=None):
        """ファイルをアップロードしてClaude分析"""
        logger.info(f"ファイルアップロード分析開始: {file_path}")
        
        try:
            # Claudeページに移動
            if chat_url:
                if not self.navigate_to_specific_chat(chat_url):
                    return None, None
            elif not self._navigate_to_claude():
                return None, None
            
            # ファイルアップロード
            if not self.upload_file(file_path):
                return None, None
            
            # 分析プロンプト送信
            prompt = analysis_prompt or "このファイルの内容を分析してください。主要なポイントと傾向をまとめてください。"
            
            response = self._send_message(prompt)
            
            # 現在のClaude URLを取得
            current_url = self.driver.current_url
            logger.info(f"Claude分析完了、URL: {current_url}")
            
            return response, current_url
            
        except Exception as e:
            logger.error(f"ファイルアップロード分析エラー: {e}")
            return None, None
        

    def navigate_to_specific_chat(self, chat_url=None):
        """指定されたClaudeチャットルームに移動"""
        try:
            if chat_url:
                url = chat_url.strip()
                # プロトコル補完
                if not url.startswith('http://') and not url.startswith('https://'):
                    url = 'https://' + url
                # Claudeドメインでなければデフォルトへ
                if 'claude.ai' not in url:
                    logger.info("ClaudeドメインではないURLのため、デフォルトに移動")
                    self.driver.get("https://claude.ai")
                else:
                    logger.info(f"指定されたClaudeチャットに移動: {url}")
                    try:
                        self.driver.get(url)
                    except Exception:
                        # 新しいタブでフォールバック
                        self.driver.execute_script("window.open(arguments[0], '_blank');", url)
                        self.driver.switch_to.window(self.driver.window_handles[-1])
            else:
                logger.info("デフォルトのClaude.aiに移動")
                self.driver.get("https://claude.ai")
            
            time.sleep(1.2)
            return True
            
        except Exception as e:
            logger.error(f"Claudeナビゲーションエラー: {e}")
            return False

    def analyze_transcription(self, transcription_text, analysis_prompt=None, chat_url=None):
        """文字おこしテキストをClaude分析"""
        logger.info("文字おこしのClaude分析開始")
        
        try:
            # 指定されたチャットルームに移動
            if not self.navigate_to_specific_chat(chat_url):
                return None
            
            # 分析プロンプト作成
            if not analysis_prompt:
                analysis_prompt = self._create_transcription_analysis_prompt(transcription_text)
            else:
                analysis_prompt = analysis_prompt.format(transcription=transcription_text)
            
            # メッセージ送信
            response = self._send_message(analysis_prompt)
            
            logger.info("文字おこし分析完了")
            return response
            
        except Exception as e:
            logger.error(f"文字おこし分析エラー: {e}")
            return None

    def _create_transcription_analysis_prompt(self, transcription_text):
        """文字おこし分析用プロンプトを作成"""
        prompt = (
            "この内容を分析してください。\n\n"
            "    【分析してほしい内容】\n"
            "    1. 全体的な傾向と特徴\n"
            "    2. 主要なポイント・キーワード\n"
            "    3. エンゲージメントの高い内容の特徴\n"
            "    4. 要約（3-5行程度）\n\n"
            "    【出力形式】\n"
            "    - 簡潔で分かりやすく\n"
            "    - 具体的な数値や例を含めて\n"
            "    - 実用的な洞察を提供\n\n"
            "    【対象テキスト】\n"
        )
        return prompt + transcription_text

    def _send_message_with_retry(self, message, max_retries=2):
        """タイムアウト対策付きメッセージ送信"""
        for retry_count in range(max_retries + 1):
            try:
                if retry_count > 0:
                    logger.info(f"メッセージ送信再試行: {retry_count}/{max_retries}")
                    time.sleep(3)  # 再試行前に待機
                
                response = self._send_message(message)
                if response:
                    return response
                else:
                    logger.warning(f"メッセージ送信応答取得失敗 (試行 {retry_count + 1})")
                    
            except Exception as e:
                logger.error(f"メッセージ送信エラー (試行 {retry_count + 1}): {e}")
                
                # タイムアウトエラーの場合は Chrome の状態をチェック
                if "timeout" in str(e).lower():
                    logger.info("タイムアウトエラー検出、Chrome接続状態をチェック")
                    try:
                        # 現在のページを確認してリフレッシュを試行
                        current_url = self.driver.current_url
                        if "claude.ai" not in current_url:
                            logger.info("Claudeページから離脱、再ナビゲーション")
                            self._navigate_to_claude()
                        else:
                            logger.info("ページリフレッシュを実行")
                            self.driver.refresh()
                            time.sleep(3)
                    except:
                        logger.warning("Chrome状態チェック失敗")
        
        logger.error("メッセージ送信: 全ての再試行が失敗しました")
        return None

    def analyze_comments(self, comments_jsonl_path, chat_url=None, max_retries=2):
        """YouTubeコメントを分析（再試行機能付き）"""
        logger.info(f"コメント分析開始: {comments_jsonl_path}")
        
        for retry_count in range(max_retries + 1):
            try:
                if retry_count > 0:
                    logger.info(f"コメント分析再試行: {retry_count}/{max_retries}")
                    time.sleep(5)  # 再試行前に待機
                
                # コメントファイル読み込み
                import json
                comments = []
                with open(comments_jsonl_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            comments.append(json.loads(line))
                
                if not comments:
                    logger.warning("コメントが見つかりません")
                    return None, None
                
                # Claudeページに移動
                if chat_url:
                    if not self.navigate_to_specific_chat(chat_url):
                        return None, None
                elif not self._navigate_to_claude():
                    return None, None
                
                # コメント分析プロンプト作成
                prompt = self._create_comments_analysis_prompt(comments)
                
                # メッセージ送信（タイムアウト対策）
                response = self._send_message_with_retry(prompt, max_retries=1)
                
                if response:
                    # 現在のClaude URLを取得
                    current_url = self.driver.current_url
                    logger.info(f"コメント分析完了、URL: {current_url}")
                    return response, current_url
                else:
                    logger.warning(f"コメント分析応答取得失敗 (試行 {retry_count + 1})")
                    if retry_count < max_retries:
                        continue
                    
            except Exception as e:
                logger.error(f"コメント分析エラー (試行 {retry_count + 1}): {e}")
                if retry_count < max_retries:
                    continue
                return None, None
        
        logger.error("コメント分析: 全ての再試行が失敗しました")
        return None, None

    def _create_comments_analysis_prompt(self, comments):
        """コメント分析用プロンプトを作成"""
        prompt = (
            "以下のYouTubeコメントを分析してください。\n\n"
            "    【分析してほしい内容】\n"
            "    1. コメント全体の感情や傾向\n"
            "    2. 頻出するキーワードやテーマ\n"
            "    3. 高評価コメントの特徴\n"
            "    4. 視聴者の関心事や要望\n"
            "    5. 要約（3-5行程度）\n\n"
            "    【出力形式】\n"
            "    - 簡潔で分かりやすく\n"
            "    - 具体的な数値や例を含めて\n"
            "    - 実用的な洞察を提供\n\n"
            "    【コメントデータ】\n"
        )
        
        # コメントを整形して追加
        for i, comment in enumerate(comments, 1):
            author = comment.get('author', '')
            text = comment.get('text', '')
            likes = comment.get('likes', 0)
            published = comment.get('published', '')
            
            prompt += f"{i}. {author} ({published}) - いいね:{likes}\n"
            prompt += f"   「{text}」\n\n"
        
        return prompt