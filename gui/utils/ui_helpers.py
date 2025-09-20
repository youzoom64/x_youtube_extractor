"""
UI共通ヘルパー関数
"""
import tkinter as tk
import threading
import requests
from datetime import datetime

class UIHelpers:
    """UI操作ヘルパークラス"""
    
    @staticmethod
    def log_message(log_text_widget, message, root_widget):
        """ログメッセージを追加（スレッドセーフ）"""
        def _add_message():
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_text_widget.insert(tk.END, f"[{timestamp}] {message}\n")
            log_text_widget.see(tk.END)
            root_widget.update()
        
        # メインスレッドで実行
        if threading.current_thread() is threading.main_thread():
            _add_message()
        else:
            root_widget.after(0, _add_message)
    
    @staticmethod
    def check_chrome_connection_async(status_label):
        """Chrome接続確認（非同期）"""
        def check():
            try:
                response = requests.get("http://localhost:9222/json", timeout=5)
                if response.status_code == 200:
                    status_label.config(text="Chrome接続状態: ✅ 接続OK", foreground="green")
                else:
                    status_label.config(text="Chrome接続状態: ❌ 接続エラー", foreground="red")
            except Exception:
                status_label.config(text="Chrome接続状態: ❌ デバッグモードで起動してください", foreground="red")
        
        threading.Thread(target=check, daemon=True).start()
    
    @staticmethod
    def safe_button_state(button, state):
        """ボタン状態を安全に変更"""
        try:
            button.config(state=state)
        except tk.TclError:
            # ウィジェットが破棄されている場合は無視
            pass
    
    @staticmethod
    def safe_label_update(label, text, **kwargs):
        """ラベルテキストを安全に更新"""
        try:
            label.config(text=text, **kwargs)
        except tk.TclError:
            # ウィジェットが破棄されている場合は無視
            pass
    
    @staticmethod
    def safe_progress_update(progress_var, value):
        """プログレスバーを安全に更新"""
        try:
            progress_var.set(value)
        except tk.TclError:
            # ウィジェットが破棄されている場合は無視
            pass
    
    @staticmethod
    def create_model_info_text(model_name):
        """Whisperモデル情報テキストを生成"""
        model_info = {
            "tiny": "精度: 低 | 速度: 最高 | サイズ: 39MB",
            "base": "精度: 中 | 速度: 高 | サイズ: 74MB",
            "small": "精度: 中高 | 速度: 中 | サイズ: 244MB",
            "medium": "精度: 高 | 速度: 中低 | サイズ: 769MB",
            "large": "精度: 最高 | 速度: 低 | サイズ: 1550MB",
            "large-v2": "精度: 最高+ | 速度: 低 | サイズ: 1550MB",
            "large-v3": "精度: 最高++ | 速度: 最低 | サイズ: 1550MB"
        }
        return model_info.get(model_name, "情報なし")
    
    @staticmethod
    def disable_buttons_during_execution(button_list):
        """実行中のボタン無効化"""
        for button in button_list:
            UIHelpers.safe_button_state(button, 'disabled')
    
    @staticmethod
    def enable_buttons_after_execution(button_list):
        """実行後のボタン有効化"""
        for button in button_list:
            UIHelpers.safe_button_state(button, 'normal')

class DialogHelpers:
    """ダイアログヘルパークラス"""
    
    @staticmethod
    def create_prompt_dialog(parent, title, default_text, width=600, height=400):
        """プロンプト入力ダイアログを作成"""
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.geometry(f"{width}x{height}")
        dialog.transient(parent)
        dialog.grab_set()
        dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        frame = tk.Frame(dialog, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="分析内容を指定してください:", font=("Arial", 12)).pack(pady=(0, 10))
        
        text_area = tk.Text(frame, height=15, width=70, font=("Arial", 11), wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        text_area.insert(tk.END, default_text)
        text_area.focus()
        
        button_frame = tk.Frame(frame)
        button_frame.pack(pady=(10, 0))
        
        result = [None]
        
        def ok_clicked():
            result[0] = text_area.get("1.0", tk.END).strip()
            dialog.destroy()
        
        def cancel_clicked():
            result[0] = None
            dialog.destroy()
        
        tk.Button(button_frame, text="OK", command=ok_clicked).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(button_frame, text="キャンセル", command=cancel_clicked).pack(side=tk.LEFT)
        
        def on_key(event):
            if event.state & 0x4 and event.keysym == 'Return':  # Ctrl+Enter
                ok_clicked()
                return 'break'
        
        text_area.bind('<Key>', on_key)
        dialog.wait_window()
        
        return result[0]