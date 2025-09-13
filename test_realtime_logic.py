#!/usr/bin/env python3
"""リアルタイム取得ロジックのテスト"""

import logging
from lib.chrome_connector import ChromeConnector
from lib.youtube_scraper import YouTubeScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_realtime_logic():
    """リアルタイム取得ロジックのテスト"""
    logger.info("=== リアルタイム取得ロジックテスト開始 ===")
    
    try:
        chrome = ChromeConnector()
        if not chrome.connect():
            logger.error("Chrome接続失敗")
            return False
        
        logger.info("✅ Chrome接続成功")
        
        yt = YouTubeScraper(chrome)
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        if not yt.navigate(test_url):
            logger.error("YouTube動画ページ読み込み失敗")
            return False
        
        logger.info("✅ YouTube動画ページ読み込み成功")
        
        # 30件テスト（リアルタイム取得の効率性をテスト）
        logger.info("📊 リアルタイム取得で30件コメント取得テスト...")
        
        import time
        start_time = time.time()
        comments = yt.extract_comments(30)
        end_time = time.time()
        
        elapsed = end_time - start_time
        logger.info(f"✅ コメント取得完了: {len(comments)}件 (所要時間: {elapsed:.1f}秒)")
        
        if len(comments) >= 20:  # 20件以上取得できれば成功
            logger.info("🎉 リアルタイム取得テスト成功！")
            logger.info(f"🚀 取得効率: {len(comments)/elapsed:.1f}件/秒")
            
            # サンプル表示
            for i, c in enumerate(comments[:3], 1):
                author = c.get('author', '不明')
                text = c.get('text', '')[:50]
                likes = c.get('likes', 0)
                logger.info(f"  {i}. {author} (👍{likes}): {text}...")
                
            return True
        else:
            logger.warning(f"⚠️ 期待より少ない: {len(comments)}件")
            return False
            
    except Exception as e:
        logger.error(f"❌ テストエラー: {e}")
        return False

if __name__ == "__main__":
    success = test_realtime_logic()
    exit(0 if success else 1)
