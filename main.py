"""メインエントリーポイント"""
import argparse
import sys
import os
from lib.utils import setup_logging, create_directories
from workflows.scrape_only import ScrapeOnlyWorkflow
from workflows.scrape_and_analyze import ScrapeAndAnalyzeWorkflow
from config.settings import DEFAULT_TWEET_COUNT

def main():
    """メイン処理"""
    # 引数解析
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # 初期設定
    setup_logging(args.log_level)
    create_directories()
    
    # ワークフロー選択
    if args.analyze:
        workflow = ScrapeAndAnalyzeWorkflow()
        result = workflow.execute(
            query=args.query,
            count=args.count,
            format_type=args.format,
            analysis_prompt=args.prompt
        )
    else:
        workflow = ScrapeOnlyWorkflow()
        result = workflow.execute(
            query=args.query,
            count=args.count,
            format_type=args.format
        )
    
    # 結果出力
    if result:
        print(f"\n✅ 処理完了: {result}")
        return 0
    else:
        print("\n❌ 処理失敗")
        return 1

def create_argument_parser():
    """コマンドライン引数パーサー作成"""
    parser = argparse.ArgumentParser(
        description="Twitter スクレイピング + Claude 分析ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # ユーザーツイート取得
  python main.py "@himanaanya" --count 30 --format txt
  
  # キーワード検索
  python main.py "Python OR JavaScript" --count 50 --format json
  
  # ハッシュタグ検索
  python main.py "#AI #機械学習" --count 20
  
  # Claude分析付き
  python main.py "政治" --analyze --count 30
  
  # カスタム分析プロンプト
  python main.py "@someone" --analyze --prompt "この人の最近の関心事は？"

注意事項:
  - Chrome を --remote-debugging-port=9222 で起動してください
  - 例: chrome --remote-debugging-port=9222
        """
    )
    
    # 必須引数
    parser.add_argument("query", help="検索クエリ (例: @username, キーワード, #ハッシュタグ)")
    
    # オプション引数
    parser.add_argument("--count", "-c", type=int, default=DEFAULT_TWEET_COUNT,
                        help=f"取得件数 (デフォルト: {DEFAULT_TWEET_COUNT})")
    
    parser.add_argument("--format", "-f", choices=["txt", "json"], default="txt",
                        help="出力形式 (デフォルト: txt)")
    
    parser.add_argument("--analyze", "-a", action="store_true",
                        help="Claude分析を実行")
    
    parser.add_argument("--prompt", "-p", type=str,
                        help="カスタム分析プロンプト (--analyze時のみ有効)")
    
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        default="INFO", help="ログレベル (デフォルト: INFO)")
    
    return parser

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  処理が中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        sys.exit(1)
