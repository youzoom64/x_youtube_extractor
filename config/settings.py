"""設定ファイル"""
import os

# Chrome接続設定
CHROME_DEBUG_PORT = 9222
CHROME_HOST = "localhost"
CONNECTION_TIMEOUT = 3  # 5秒 → 3秒

# スクレイピング設定（適切な値に調整）
DEFAULT_TWEET_COUNT = 20
SCROLL_DELAY = 0.8  # 0.3秒 → 0.8秒（適切な待機時間）
REQUEST_DELAY = 0.5  # 0.2秒 → 0.5秒（適切な待機時間）
MAX_RETRIES = 2
PAGE_LOAD_TIMEOUT = 8  # 12秒 → 8秒（高速化）

# 高速化設定
ENABLE_CONNECTION_REUSE = True  # Chrome接続の再利用を有効化
FAST_MODE = True  # 高速モードを有効化
MINIMUM_WAIT_TIME = 0.8  # 最小待機時間（0.5秒 → 0.8秒）
CHROME_CONNECTION_TIMEOUT = 1  # Chrome接続タイムアウト（1秒）
IMPLICIT_WAIT = 1  # 暗黙的待機時間（1秒）

# スクリーンショット設定
SCREENSHOT_ENABLE_PROMOTION_FILTER = False  # プロモーション除外を無効化
SCREENSHOT_SCROLL_MULTIPLIER = 2.0  # 目標件数の何倍までスクロールするか
SCREENSHOT_MAX_SCROLLS = 30  # 最大スクロール回数（50 → 30に制限）
SCREENSHOT_WAIT_TIME = 0.5  # 要素間の待機時間（0.3秒 → 0.5秒）

# ファイル設定
MAX_FILENAME_LENGTH = 100
OUTPUT_DIR = "output"
QUERY_DIR = "query"
LOG_DIR = "logs"

# ログ設定
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# データベース設定
USE_DATABASE = True
DATABASE_PATH = "data/scraper.db"
