#!/usr/bin/env python3
"""最終修正版のテスト"""

import logging
from lib.chrome_connector import ChromeConnector
from lib.youtube_scraper import YouTubeScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_final_logic():
    """最終修正版のテスト"""
    logger.info("=== 最終修正版テスト開始 ===")
    
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
        
        # 20件テスト（確実に終了するかテスト）
        logger.info("📊 最終修正版で20件コメント取得テスト...")
        comments = yt.extract_comments(20)
        
        logger.info(f"✅ コメント取得完了: {len(comments)}件")
        
        if len(comments) >= 10:  # 10件以上取得できれば成功
            logger.info("🎉 最終修正版テスト成功！確実に終了しました")
            
            # サンプル表示
            for i, c in enumerate(comments[:3], 1):
                author = c.get('author', '不明')
                text = c.get('text', '')[:50]
                logger.info(f"  {i}. {author}: {text}...")
                
            return True
        else:
            logger.warning(f"⚠️ 期待より少ない: {len(comments)}件")
            return False
            
    except Exception as e:
        logger.error(f"❌ テストエラー: {e}")
        return False

if __name__ == "__main__":
    success = test_final_logic()
    exit(0 if success else 1)
