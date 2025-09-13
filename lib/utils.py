"""ユーティリティ関数"""
import re
import os
import logging
from datetime import datetime
from config.settings import MAX_FILENAME_LENGTH

logger = logging.getLogger(__name__)

def sanitize_filename(filename):
    """ファイル名をサニタイズ"""
    # 使用不可文字を置換
    invalid_chars = r'[<>:"/\\|?*]'
    filename = re.sub(invalid_chars, '_', filename)
    
    # スペースをアンダースコアに
    filename = filename.replace(' ', '_')
    
    # 連続するアンダースコアを一つに
    filename = re.sub(r'_+', '_', filename)
    
    ## 先頭末尾のアンダースコアを除去
    filename = filename.strip('_')
    
    # 長さ制限（拡張子分を考慮して4文字短く）
    max_length = MAX_FILENAME_LENGTH - 4
    if len(filename) > max_length:
        filename = filename[:max_length-3] + "..."
    
    return filename

def setup_logging(log_level="INFO"):
    """ログ設定"""
    from config.settings import LOG_DIR, LOG_FORMAT
    
    # ログディレクトリ作成
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # ログファイル名（日付付き）
    log_filename = os.path.join(LOG_DIR, f"scraper_{datetime.now().strftime('%Y%m%d')}.log")
    
    # ログ設定
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def format_count(count):
    """数値を読みやすい形式にフォーマット"""
    if count >= 1000000:
        return f"{count/1000000:.1f}M"
    elif count >= 1000:
        return f"{count/1000:.1f}K"
    else:
        return str(count)

def validate_query(query):
    """クエリの妥当性をチェック"""
    if not query or not query.strip():
        return False, "クエリが空です"
    
    if len(query) > 500:
        return False, "クエリが長すぎます（500文字以内）"
    
    return True, ""

def create_directories():
    """必要なディレクトリを作成"""
    from config.settings import OUTPUT_DIR, QUERY_DIR, LOG_DIR
    
    dirs = [
        OUTPUT_DIR,
        os.path.join(OUTPUT_DIR, QUERY_DIR),
        LOG_DIR
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        logger.debug(f"ディレクトリ作成: {dir_path}")

def retry_on_failure(func, max_retries=3, delay=1):
    """失敗時のリトライデコレータ"""
    import time
    
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"リトライ {attempt + 1}/{max_retries}: {e}")
                time.sleep(delay)
        return None
    
    return wrapper
