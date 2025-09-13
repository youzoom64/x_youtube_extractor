"""最適化版Chrome接続管理"""
import json
import requests
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config.settings import CHROME_DEBUG_PORT, CHROME_HOST, CONNECTION_TIMEOUT

logger = logging.getLogger(__name__)

class ChromeConnector:
    def __init__(self):
        self.driver = None
        self.debug_url = f"http://{CHROME_HOST}:{CHROME_DEBUG_PORT}"
        self._is_connected = False
        
    def connect(self):
        """高速化されたChrome接続（接続済みの場合は再利用）"""
        try:
            # 既に接続済みの場合はスキップ
            if self._is_connected and self.driver:
                try:
                    # 接続状態を簡単にチェック
                    self.driver.current_url
                    logger.info("既存のChrome接続を再利用")
                    return True
                except:
                    # 接続が切れている場合は再接続
                    logger.info("既存の接続が切れているため再接続")
                    self._is_connected = False
                    self.driver = None
            
            # デバッグポートチェック（タイムアウト短縮）
            response = requests.get(f"{self.debug_url}/json", timeout=1)  # 2秒 → 1秒
            tabs = response.json()
            
            if not tabs:
                raise ConnectionError("デバッグモードChromeにタブが見つかりません")
            
            # 高速化Chrome オプション設定
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", f"{CHROME_HOST}:{CHROME_DEBUG_PORT}")
            
            # ★ 速度最適化オプション追加
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            # ページ描画に必要な要素は有効化（YouTube DOM抽出のため）
            # chrome_options.add_argument("--disable-images")
            # chrome_options.add_argument("--disable-javascript")
            # chrome_options.add_argument("--disable-css")
            
            # ページ読み込み戦略を高速化
            chrome_options.add_argument("--page-load-strategy=eager")
            
            # WebDriverで接続（タイムアウト調整）
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # タイムアウト設定を調整（安定性重視）
            self.driver.implicitly_wait(3)  # 1秒 → 3秒（安定性向上）
            
            # ページ読み込みタイムアウトを調整
            self.driver.set_page_load_timeout(15)  # 8秒 → 15秒（安定性向上）
            
            # スクリプトタイムアウトを設定（重要：WebDriverのタイムアウト対策）
            self.driver.set_script_timeout(30)  # 30秒のスクリプトタイムアウト
            
            self._is_connected = True
            logger.info(f"高速Chrome接続完了 (Port: {CHROME_DEBUG_PORT})")
            return True
            
        except Exception as e:
            logger.error(f"Chrome接続エラー: {e}")
            self._is_connected = False
            return False
    
    def is_connected(self):
        """接続状態をチェック"""
        try:
            if self.driver:
                self.driver.current_url
                return True
        except:
            pass
        return False
    
    def close(self):
        """接続を閉じる"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            self._is_connected = False