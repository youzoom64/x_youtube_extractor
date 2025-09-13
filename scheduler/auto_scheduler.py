"""自動スケジューラー"""
import schedule
import time
import logging
import os
import sys
from datetime import datetime, timedelta
import threading

# プロジェクトルートを追加（修正版）
current_dir = os.path.dirname(os.path.abspath(__file__))  # scheduler/
project_root = os.path.dirname(current_dir)  # プロジェクトルート
sys.path.insert(0, project_root)

print(f"プロジェクトルート: {project_root}")  # デバッグ用

from workflows.scrape_only_cli import ScrapeOnlyWorkflowCLI
from workflows.file_to_claude_cli import FileToClaudeCLI
from lib.utils import setup_logging, create_directories

logger = logging.getLogger(__name__)

class AutoScheduler:
    def __init__(self, config_file="scheduler_config.json"):
        self.config_file = config_file
        self.running = False
        self.load_config()
        
    def load_config(self):
        """設定を読み込み"""
        import json
        
        # デフォルト設定
        default_config = {
            "schedules": [
                {
                    "name": "朝のニュース分析",
                    "query": "ニュース OR 時事",
                    "time": "08:00",
                    "count": 30,
                    "format": "txt",
                    "claude_analysis": True,
                    "analysis_prompt": "最新のニュースから重要なトピックを3つ選んで要約してください",
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                },
                {
                    "name": "技術トレンド",
                    "query": "#AI OR #Python OR #JavaScript",
                    "time": "12:00",
                    "count": 20,
                    "format": "json",
                    "claude_analysis": True,
                    "analysis_prompt": "技術トレンドを分析して、注目すべき技術を教えてください",
                    "days": ["daily"]
                }
            ]
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = default_config
                self.save_config()
                
        except Exception as e:
            logger.error(f"設定読み込みエラー: {e}")
            self.config = default_config
    
    def save_config(self):
        """設定を保存"""
        import json
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"設定保存エラー: {e}")
    
    def execute_job(self, job_config):
        """ジョブを実行（CLI版）"""
        try:
            job_name = job_config.get("name", "無名ジョブ")
            query = job_config.get("query")
            count = job_config.get("count", 20)
            format_type = job_config.get("format", "txt")
            sort_type = job_config.get("sort_type", "latest")  # デフォルトは最新順
            claude_analysis = job_config.get("claude_analysis", False)
            analysis_prompt = job_config.get("analysis_prompt")
            
            logger.info(f"=== 自動ジョブ実行: {job_name} ===")
            logger.info(f"クエリ: {query}")
            logger.info(f"件数: {count}")
            logger.info(f"ソート: {sort_type}")
            
            # Step 1: Twitter取得（ソート指定）
            logger.info("Step 1: Twitter取得開始")
            workflow = ScrapeOnlyWorkflowCLI()
            result = workflow.execute(
                query=job_config.get("query"),
                count=job_config.get("count", 20),
                format_type=job_config.get("format", "txt"),
                sort_type=job_config.get("sort_type", "latest")
            )
            
            if not result:
                logger.error("Twitter取得に失敗しました")
                return False
            
            logger.info(f"Twitter取得完了: {result}")
            
            # Step 2: Claude分析（CLI版）
            if claude_analysis:
                logger.info("Step 2: Claude分析開始")
                
                try:
                    claude_workflow = FileToClaudeCLI()  # ← 修正
                    analysis_result = claude_workflow.execute(result, analysis_prompt)
                    
                    if analysis_result:
                        logger.info(f"Claude分析完了: {analysis_result}")
                    else:
                        logger.warning("Claude分析に失敗しました")
                        
                except Exception as e:
                    logger.error(f"Claude分析エラー: {e}")
            
            logger.info(f"=== ジョブ完了: {job_name} ===")
            return True
            
        except Exception as e:
            logger.error(f"ジョブ実行エラー: {e}")
            return False
        
    def setup_schedules(self):
        """スケジュールを設定"""
        logger.info("スケジュール設定開始...")
        
        for job_config in self.config.get("schedules", []):
            job_name = job_config.get("name", "無名ジョブ")
            job_time = job_config.get("time", "12:00")
            days = job_config.get("days", ["daily"])
            
            logger.info(f"ジョブ設定: {job_name} - {job_time} - {days}")
            
            # 曜日別設定
            if "daily" in days:
                schedule.every().day.at(job_time).do(self.execute_job, job_config)
                logger.info(f"  → 毎日 {job_time} に実行")
            else:
                for day in days:
                    if day == "monday":
                        schedule.every().monday.at(job_time).do(self.execute_job, job_config)
                    elif day == "tuesday":
                        schedule.every().tuesday.at(job_time).do(self.execute_job, job_config)
                    elif day == "wednesday":
                        schedule.every().wednesday.at(job_time).do(self.execute_job, job_config)
                    elif day == "thursday":
                        schedule.every().thursday.at(job_time).do(self.execute_job, job_config)
                    elif day == "friday":
                        schedule.every().friday.at(job_time).do(self.execute_job, job_config)
                    elif day == "saturday":
                        schedule.every().saturday.at(job_time).do(self.execute_job, job_config)
                    elif day == "sunday":
                        schedule.every().sunday.at(job_time).do(self.execute_job, job_config)
                
                logger.info(f"  → {', '.join(days)} {job_time} に実行")
        
        logger.info("スケジュール設定完了")
    
    def start(self):
        """スケジューラー開始"""
        logger.info("=== 自動スケジューラー開始 ===")
        
        # 初期設定
        setup_logging("INFO")
        create_directories()
        
        # スケジュール設定
        self.setup_schedules()
        
        self.running = True
        
        logger.info("スケジューラー稼働中... (Ctrl+C で停止)")
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # 1分間隔でチェック
                
        except KeyboardInterrupt:
            logger.info("スケジューラーを停止します...")
            self.running = False
        
        logger.info("=== 自動スケジューラー終了 ===")
    
    def stop(self):
        """スケジューラー停止"""
        self.running = False
    
    def list_jobs(self):
        """設定されたジョブ一覧を表示"""
        print("��� 設定されたジョブ一覧:")
        for i, job in enumerate(self.config.get("schedules", []), 1):
            print(f"{i}. {job.get('name')} - {job.get('time')} - {job.get('days')}")
            print(f"   クエリ: {job.get('query')}")
            print(f"   Claude分析: {'有' if job.get('claude_analysis') else '無'}")
            print()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Twitter自動取得スケジューラー")
    parser.add_argument("--config", default="scheduler_config.json", help="設定ファイル")
    parser.add_argument("--list", action="store_true", help="ジョブ一覧表示")
    parser.add_argument("--test", help="テスト実行（ジョブ名指定）")
    
    args = parser.parse_args()
    
    scheduler = AutoScheduler(args.config)
    
    if args.list:
        scheduler.list_jobs()
    elif args.test:
        # テスト実行
        for job in scheduler.config.get("schedules", []):
            if job.get("name") == args.test:
                print(f"��� テスト実行: {args.test}")
                scheduler.execute_job(job)
                break
        else:
            print(f"❌ ジョブが見つかりません: {args.test}")
    else:
        # 通常稼働
        scheduler.start()

if __name__ == "__main__":
    main()
