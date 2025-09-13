"""ファイル→Claude分析ワークフロー"""
import logging
import os
from datetime import datetime  # ← これを使う
from lib.chrome_connector import ChromeConnector
from lib.claude_automation import ClaudeAutomation
from lib.formatter import Formatter

logger = logging.getLogger(__name__)

class FileToClaude:
    def __init__(self):
        self.chrome = ChromeConnector()
        self.claude = None
        self.formatter = Formatter()
    
    def execute(self, file_path, analysis_prompt=None, chat_url=None):
        """ファイルをClaudeで分析"""
        logger.info(f"=== ファイル→Claude分析開始 ===")
        logger.info(f"ファイル: {file_path}")
        
        try:
            # ファイル存在確認
            if not os.path.exists(file_path):
                logger.error(f"ファイルが見つかりません: {file_path}")
                return None
            
            # Chrome接続（既存の接続を使用）
            if not self.chrome.connect():
                logger.error("Chrome接続に失敗しました")
                return None
            
            # Claude自動操作
            self.claude = ClaudeAutomation(self.chrome)
            
            print("🔄 既存のClaudeタブでファイルアップロード分析を実行...")
            
            # 直接ファイルアップロード＋分析を実行（指定チャットへナビゲート対応）
            analysis, current_url = self.claude.upload_and_analyze_file(file_path, analysis_prompt, chat_url=chat_url)
            
            if analysis:
                # 分析結果を保存（タイムスタンプ付き）
                # import datetime  ← この行を削除
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # 元ファイル名からタイムスタンプと拡張子を取得
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # 新しいファイル名
                analysis_file = os.path.join(
                    os.path.dirname(file_path), 
                    f"{timestamp}_{base_name}_claude_analysis.txt"
                )
                
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    f.write(f"元ファイル: {file_path}\n")
                    if current_url:
                        f.write(f"Claude URL: {current_url}\n")
                    f.write(f"分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write("【Claude分析結果】\n")
                    f.write(analysis)
                
                logger.info(f"分析完了: {analysis_file}")
                return analysis_file
            else:
                logger.error("Claude分析に失敗しました")
                return None
                
        except Exception as e:
            logger.error(f"処理エラー: {e}")
            return None