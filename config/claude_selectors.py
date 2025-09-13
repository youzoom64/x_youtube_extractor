"""Claude用CSSセレクタ（2025年最新UI対応）"""

# テキスト入力エリア
TEXT_INPUT_SELECTORS = [
    'div[contenteditable="true"]',
    'textarea',
    'div[data-testid="chat-input"]',
    'div[role="textbox"]',
    'div[aria-label*="メッセージ"]'
]

# 送信ボタン
SEND_BUTTON_SELECTORS = [
    'button[type="submit"]',
    'button[aria-label*="送信"]',
    'button[aria-label*="Send"]',
    'button[data-testid="send-button"]',
    'svg[data-icon="send"]',
    'button:has(svg)',
    'button[disabled="false"]:last-of-type'
]

# ファイルアップロード
FILE_UPLOAD_TRIGGER = 'button[data-testid="input-menu-plus"]'
FILE_INPUT = 'input[type="file"]'

# レスポンス
RESPONSE_CONTAINER_SELECTORS = [
    'div[data-is-streaming="false"]',
    'div[data-message-author="assistant"]',
    'div[role="article"]',
    'div[data-testid="conversation-turn"]'
]