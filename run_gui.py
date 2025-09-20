"""
GUI起動スクリプト
"""
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# GUIアプリケーション起動
from gui.main_window import main

if __name__ == "__main__":
    main()