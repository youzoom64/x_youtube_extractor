"""Streamlit GUI アプリケーション（同時実行版）"""
import streamlit as st
import sys
import os
import threading
import time
from io import StringIO

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflows.scrape_only import ScrapeOnlyWorkflow
from workflows.scrape_with_screenshots import ScrapeWithScreenshotsWorkflow
from lib.utils import setup_logging, create_directories, validate_query

def main():
    st.set_page_config(
        page_title="Twitter スクレイピング + Claude 分析 + スクリーンショット",
        page_icon="🐦",
        layout="wide"
    )
    
    st.title("🐦 Twitter スクレイピング + Claude 分析 + スクリーンショットツール")
    
    # サイドバー設定
    with st.sidebar:
        st.header("⚙️ 設定")
        
        # Chrome接続状態チェック
        if st.button("Chrome接続確認"):
            check_chrome_connection()
        
        st.divider()
        
        # 設定項目
        count = st.slider("取得件数", 1, 100, 20)
        format_type = st.selectbox("出力形式", ["txt", "json"])
        
        # スクリーンショット設定
        st.subheader("📸 スクリーンショット設定")
        enable_screenshots = st.checkbox("スクリーンショットを撮影", value=True)
        if enable_screenshots:
            capture_mode = st.selectbox("撮影モード", ["individual", "smart_batch"])
        else:
            capture_mode = None
        
        # Claude分析設定
        analyze = st.checkbox("Claude分析を実行")
        if analyze:
            custom_prompt = st.text_area(
                "カスタム分析プロンプト（オプション）",
                placeholder="例: この人の最近の関心事は？"
            )
        else:
            custom_prompt = None
    
    # メイン画面
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🔍 検索クエリ")
        query = st.text_input(
            "検索したい内容を入力してください",
            placeholder="例: @himanaanya, #Python, キーワード"
        )
        
        # 実行ボタン
        if st.button("🚀 実行", type="primary", use_container_width=True):
            if query:
                run_scraping(query, count, format_type, enable_screenshots, capture_mode, analyze, custom_prompt)
            else:
                st.error("検索クエリを入力してください")
    
    with col2:
        st.header("💡 使用例")
        st.code("""
# ユーザーツイート
@himanaanya

# キーワード検索  
Python OR JavaScript

# ハッシュタグ検索
#AI #機械学習

# 複合検索
from:@username since:2025-01-01
        """)
        
        if enable_screenshots:
            st.info("📸 スクリーンショット機能が有効です")
    
    # 結果表示エリア
    if 'results' in st.session_state:
        display_results()

@st.cache_data(ttl=300)
def check_chrome_connection():
    """キャッシュ付きChrome接続確認"""
    try:
        import requests
        response = requests.get("http://localhost:9222/json", timeout=3)
        return response.status_code == 200
    except:
        return False

def display_chrome_status():
    """Chrome接続状態表示"""
    if check_chrome_connection():
        st.success("✅ Chrome接続OK")
    else:
        st.error("❌ Chrome デバッグモードで起動してください")

def run_scraping(query, count, format_type, enable_screenshots, capture_mode, analyze, custom_prompt):
    """スクレイピング実行（同時実行版）"""
    
    # 入力チェック
    is_valid, error_msg = validate_query(query)
    if not is_valid:
        st.error(f"❌ {error_msg}")
        return
    
    # プログレスバー
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # 即座に最初のステップを表示
        progress_bar.progress(0.2)
        status_text.text("Chrome接続中...")
        
        # ワークフロー作成
        if enable_screenshots:
            workflow = ScrapeWithScreenshotsWorkflow()
            workflow_type = "スクリーンショット付き"
        elif analyze:
            workflow = ScrapeAndAnalyzeWorkflow()
            workflow_type = "Claude分析付き"
        else:
            workflow = ScrapeOnlyWorkflow()
            workflow_type = "ツイート取得のみ"
        
        # Chrome接続
        if not workflow.chrome.connect():
            st.error("❌ Chrome接続に失敗しました")
            return
        
        # 同時実行開始
        progress_bar.progress(0.4)
        status_text.text(f"{workflow_type}処理中...")
        
        # ワークフロー実行
        if enable_screenshots:
            txt_file, screenshot_files, summary_file = workflow.execute(
                query, count, format_type, "latest", capture_mode
            )
            result = {
                'txt_file': txt_file,
                'screenshot_files': screenshot_files,
                'summary_file': summary_file
            }
        elif analyze:
            result = workflow.execute(query, count, format_type, custom_prompt)
        else:
            result = workflow.execute(query, count, format_type)
        
        # 完了
        progress_bar.progress(1.0)
        status_text.text("完了!")
        
        if result:
            st.success(f"✅ 処理完了: {workflow_type}")
            
            # 結果をセッションに保存
            st.session_state.results = {
                'result': result,
                'query': query,
                'count': count,
                'format': format_type,
                'screenshots': enable_screenshots,
                'analyzed': analyze,
                'workflow_type': workflow_type
            }
            
            # 結果表示
            show_results(result, format_type, enable_screenshots)
            
        else:
            st.error("❌ 処理に失敗しました")
            
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {e}")
    finally:
        # 少し待ってからクリア
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()

def show_results(result, format_type, enable_screenshots):
    """結果を表示"""
    st.header("📊 取得結果")
    
    if enable_screenshots and isinstance(result, dict) and 'txt_file' in result:
        # スクリーンショット付きの場合
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📝 テキストファイル")
            if result['txt_file']:
                show_file_content(result['txt_file'], format_type)
            else:
                st.error("テキストファイルが生成されませんでした")
        
        with col2:
            st.subheader("📸 スクリーンショット")
            if result['screenshot_files']:
                st.success(f"✅ {len(result['screenshot_files'])}件のスクリーンショットを撮影")
                for i, screenshot_file in enumerate(result['screenshot_files'][:5]):  # 最初の5件を表示
                    st.text(f"📷 {os.path.basename(screenshot_file)}")
                if len(result['screenshot_files']) > 5:
                    st.text(f"... 他 {len(result['screenshot_files']) - 5}件")
            else:
                st.warning("スクリーンショットが撮影されませんでした")
    else:
        # 通常の結果表示
        if isinstance(result, str):
            show_file_content(result, format_type)
        else:
            st.json(result)

def show_file_content(file_path, format_type):
    """ファイル内容を表示"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if format_type == "json":
            st.json(content)
        else:
            st.text(content)
        
        # ダウンロードボタン
        st.download_button(
            label="💾 ファイルをダウンロード",
            data=content,
            file_name=os.path.basename(file_path),
            mime="text/plain" if format_type == "txt" else "application/json"
        )
        
    except Exception as e:
        st.error(f"ファイル読み込みエラー: {e}")

def display_results():
    """保存された結果を表示"""
    results = st.session_state.results
    
    st.header("📈 最新の実行結果")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("クエリ", results['query'])
    with col2:
        st.metric("取得件数", results['count'])
    with col3:
        st.metric("フォーマット", results['format'].upper())
    with col4:
        st.metric("ワークフロー", results['workflow_type'])

if __name__ == "__main__":
    main()
