"""Twitter データ解析・整形"""
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TwitterParser:
    def __init__(self):
        pass
    
    def parse_tweets(self, raw_tweets):
        """生のツイートデータを解析・整形"""
        parsed_tweets = []
        
        for tweet in raw_tweets:
            parsed = self._parse_single_tweet(tweet)
            if parsed:
                parsed_tweets.append(parsed)
        
        logger.info(f"ツイート解析完了: {len(parsed_tweets)}件")
        return parsed_tweets
    
    def _parse_single_tweet(self, tweet):
        """個別ツイートの解析"""
        try:
            return {
                'datetime': self._format_datetime(tweet.get('datetime', '')),
                'url': tweet.get('url', ''),
                'username': self._clean_username(tweet.get('username', '')),
                'text': self._clean_text(tweet.get('text', '')),
                'replies': tweet.get('replies', 0),
                'reposts': tweet.get('reposts', 0),
                'likes': tweet.get('likes', 0),
                'views': tweet.get('views', 0),
                'quoted_tweet': self._extract_quoted_tweet(tweet.get('text', ''))
            }
        except Exception as e:
            logger.error(f"ツイート解析エラー: {e}")
            return None
    
    def _format_datetime(self, datetime_str):
        """日時フォーマットを統一"""
        if not datetime_str:
            return ""
        
        try:
            # ISO形式から日本語表示形式に変換
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return datetime_str
    
    def _clean_username(self, username):
        """ユーザー名をクリーンアップ"""
        if not username:
            return ""
        
        # @マークを追加
        if not username.startswith('@'):
            username = '@' + username
        
        return username
    
    def _clean_text(self, text):
        """ツイート本文をクリーンアップ"""
        if not text:
            return ""
        
        # 余分な空白を除去
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def _extract_quoted_tweet(self, text):
        """引用ツイートを検出"""
        # "引用" などの文字列がある場合は引用ツイートとして処理
        if '引用' in text or 'RT @' in text:
            return True
        return None
    
    def sort_by_engagement(self, tweets, metric='likes'):
        """エンゲージメントでソート"""
        return sorted(tweets, key=lambda x: x.get(metric, 0), reverse=True)
    
    def filter_by_date(self, tweets, start_date=None, end_date=None):
        """日付でフィルター"""
        filtered = []
        
        for tweet in tweets:
            tweet_date = tweet.get('datetime', '')
            # 日付フィルター処理を実装
            filtered.append(tweet)
        
        return filtered
