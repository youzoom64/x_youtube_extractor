"""出力フォーマット処理"""
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Formatter:
    def __init__(self, output_dir="output/query"):
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """出力ディレクトリを作成"""
        os.makedirs(self.output_dir, exist_ok=True)
   
    def save_with_analysis(self, tweets, analysis, query, format_type="txt"):
        """分析結果付きで保存"""
        filename = self._generate_filename(query, format_type, suffix="_analysis")
        filepath = os.path.join(self.output_dir, filename)
        
        if format_type.lower() == "json":
            return self._save_analysis_json(tweets, analysis, query, filepath)
        else:
            return self._save_analysis_txt(tweets, analysis, query, filepath)
    
    def _save_as_txt(self, tweets, query, filepath):
        """TXT形式で保存"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"検索クエリ: {query}\n")
                f.write(f"取得日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"取得件数: {len(tweets)}\n")
                f.write("=" * 50 + "\n\n")
                
                for tweet in tweets:
                    # 絵文字をテキストに変更
                    f.write(f"時刻: {tweet.get('datetime', '')}\n")
                    f.write(f"URL: {tweet.get('url', '')}\n")
                    f.write(f"{tweet.get('username', '')}\n")
                    f.write(f"{tweet.get('text', '')}\n")
                    
                    # エンゲージメント（絵文字なし）
                    replies = tweet.get('replies', 0)
                    reposts = tweet.get('reposts', 0)
                    likes = tweet.get('likes', 0)
                    views = tweet.get('views', 0)
                    
                    f.write(f"リプライ: {replies} | リポスト: {reposts} | いいね: {likes} | 表示: {views}\n\n")
            
            logger.info(f"TXTファイル保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"TXT保存エラー: {e}")
            return None
    
    def _save_as_json(self, tweets, query, filepath):
        """JSON形式で保存"""
        try:
            data = {
                "scrape_info": {
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "count": len(tweets)
                },
                "tweets": tweets
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"JSONファイル保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"JSON保存エラー: {e}")
            return None
    
    def _save_analysis_txt(self, tweets, analysis, query, filepath):
        """分析結果付きTXT保存"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"検索クエリ: {query}\n")
                f.write(f"取得日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"取得件数: {len(tweets)}\n")
                f.write("=" * 50 + "\n\n")
                
                # 分析結果
                f.write("【Claude分析結果】\n")
                f.write(f"{analysis}\n")
                f.write("=" * 50 + "\n\n")
                
                # ツイートデータ
                f.write("【取得データ】\n")
                for tweet in tweets:
                    f.write(f"時刻: {tweet.get('datetime', '')}\n")
                    f.write(f"URL: {tweet.get('url', '')}\n")
                    f.write(f"{tweet.get('username', '')}\n")
                    f.write(f"{tweet.get('text', '')}\n")
                    
                    replies = tweet.get('replies', 0)
                    reposts = tweet.get('reposts', 0)
                    likes = tweet.get('likes', 0)
                    views = tweet.get('views', 0)
                    
                    f.write(f"リプライ: {replies} | リポスト: {reposts} | いいね: {likes} | 表示: {views}\n\n")
            
            logger.info(f"分析結果付きTXTファイル保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"分析TXT保存エラー: {e}")
            return None
    
    def _save_analysis_json(self, tweets, analysis, query, filepath):
        """分析結果付きJSON保存"""
        try:
            data = {
                "scrape_info": {
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "count": len(tweets)
                },
                "analysis": analysis,
                "tweets": tweets
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"分析結果付きJSONファイル保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"分析JSON保存エラー: {e}")
            return None
    
    def _generate_filename(self, query, format_type, suffix=""):
        """ファイル名を生成（タイムスタンプ付き）"""
        from lib.utils import sanitize_filename
        import datetime
        
        # タイムスタンプを生成
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # クエリをサニタイズ
        safe_query = sanitize_filename(query)
        
        # 拡張子
        ext = "json" if format_type.lower() == "json" else "txt"
        
        return f"{timestamp}_{safe_query}{suffix}.{ext}"

    def _ensure_output_dir(self):
        """出力ディレクトリを作成（サブフォルダ付き）"""
        import datetime
        
        # 日付フォルダを作成
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.daily_dir = os.path.join(self.output_dir, today)
        
        os.makedirs(self.daily_dir, exist_ok=True)
        print(f"📁 出力ディレクトリ: {self.daily_dir}")

    def save_tweets(self, tweets, query, format_type="txt"):
        """ツイートを保存"""
        filename = self._generate_filename(query, format_type)
        filepath = os.path.join(self.daily_dir, filename)  # サブフォルダに保存
        
        if format_type.lower() == "json":
            return self._save_as_json(tweets, query, filepath)
        else:
            return self._save_as_txt(tweets, query, filepath)

    def save_with_analysis(self, tweets, analysis, query, format_type="txt"):
        """分析結果付きで保存"""
        filename = self._generate_filename(query, format_type, suffix="_analysis")
        filepath = os.path.join(self.daily_dir, filename)  # サブフォルダに保存
        
        if format_type.lower() == "json":
            return self._save_analysis_json(tweets, analysis, query, filepath)
        else:
            return self._save_analysis_txt(tweets, analysis, query, filepath)