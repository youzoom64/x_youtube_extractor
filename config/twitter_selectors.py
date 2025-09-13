"""Twitter用CSSセレクタ"""

# ツイート関連
TWEET_CONTAINER = '[data-testid="tweet"]'
TWEET_TEXT = '[data-testid="tweetText"]'
TWEET_TIME = 'time'
TWEET_LINK = '[data-testid="tweet"] a[href*="/status/"]'

# エンゲージメント
REPLY_COUNT = '[data-testid="reply"]'
REPOST_COUNT = '[data-testid="retweet"]' 
LIKE_COUNT = '[data-testid="like"]'
VIEW_COUNT = 'a[href*="/analytics"] span'

# ユーザー情報
USERNAME = '[data-testid="User-Name"] a'
USER_HANDLE = '[data-testid="User-Name"] span:last-child'

# 検索・ナビゲーション
SEARCH_BOX = '[data-testid="SearchBox_Search_Input"]'
SEARCH_BUTTON = '[data-testid="SearchBox_Search_Button"]'

# スクロール
TIMELINE = '[data-testid="primaryColumn"]'
