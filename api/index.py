# Vercel API - Twitter OAuth + Daily Reset
import os
import json
from flask import Flask, request, jsonify, redirect, session, render_template
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Twitter OAuth config
TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY', '')
TWITTER_API_SECRET = os.environ.get('TWITTER_API_SECRET', '')
CALLBACK_URL = os.environ.get('CALLBACK_URL', 'https://task-tracker-kohl-one-14.vercel.app/callback')

# In-memory store (replace with database in production)
USERS = {
    1: {'id': 1, 'username': 'crypto_king', 'name': 'Crypto King', 'avatar': 'https://picsum.photos/100', 'links': 12, 'interactions': 45, 'last_submit_date': None},
    2: {'id': 2, 'username': 'defi_girl', 'name': 'DeFi Girl', 'avatar': 'https://picsum.photos/101', 'links': 8, 'interactions': 32, 'last_submit_date': None},
    3: {'id': 3, 'username': 'whale_watcher', 'name': 'Whale Watcher', 'avatar': 'https://picsum.photos/102', 'links': 15, 'interactions': 12, 'last_submit_date': None},
    4: {'id': 4, 'username': 'nft_collector', 'name': 'NFT Collector', 'avatar': 'https://picsum.photos/103', 'links': 5, 'interactions': 28, 'last_submit_date': None},
    5: {'id': 5, 'username': 'memecoin_lad', 'name': 'Memecoin Lad', 'avatar': 'https://picsum.photos/104', 'links': 20, 'interactions': 5, 'last_submit_date': None},
}

# Tasks keyed by date
TASKS = {}

def get_today_utc_date():
    return datetime.utcnow().strftime('%Y-%m-%d')

def get_utc_midnight():
    now = datetime.utcnow()
    midnight = datetime(now.year, now.month, now.day)
    return midnight

def get_seconds_until_midnight():
    now = datetime.utcnow()
    midnight = get_utc_midnight() + timedelta(days=1)
    delta = midnight - now
    return int(delta.total_seconds())

def get_tasks_for_today():
    """核心模块1: 只返回今日(UTC)数据"""
    today = get_today_utc_date()
    if today not in TASKS:
        TASKS[today] = [
            {'id': 1, 'userId': 1, 'username': 'crypto_king', 'avatar': 'https://picsum.photos/100', 'link': 'https://x.com/crypto_king/status/123456789', 'liked': True, 'retweeted': False, 'commented': True},
            {'id': 2, 'userId': 2, 'username': 'defi_girl', 'avatar': 'https://picsum.photos/101', 'link': 'https://x.com/defi_girl/status/123456788', 'liked': False, 'retweeted': True, 'commented': False},
            {'id': 3, 'userId': 3, 'username': 'whale_watcher', 'avatar': 'https://picsum.photos/102', 'link': 'https://x.com/whale_watcher/status/123456787', 'liked': True, 'retweeted': True, 'commented': False},
        ]
    return TASKS[today]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/countdown')
def get_countdown():
    """核心模块2: 返回距离UTC午夜的倒计时"""
    return jsonify({
        'seconds': get_seconds_until_midnight(),
        'resetTime': '08:00:00',  # 北京时间
        'utcReset': '00:00:00'
    })

@app.route('/api/user')
def get_user():
    # For demo, return user 1
    return jsonify(USERS[1])

@app.route('/api/users')
def get_users():
    """返回用户排行榜(只看今日数据)"""
    today_users = []
    for uid, user in USERS.items():
        today_users.append({
            'id': user['id'],
            'username': user['username'],
            'avatar': user['avatar'],
            'links': user.get('links_today', 0),
            'interactions': user.get('interactions_today', 0)
        })
    today_users.sort(key=lambda x: x['interactions'], reverse=True)
    return jsonify(today_users)

@app.route('/api/tasks')
def get_tasks():
    """核心模块1: 只返回今日(UTC)的任务"""
    tasks = get_tasks_for_today()
    return jsonify(tasks)

@app.route('/api/submit', methods=['POST'])
def submit_link():
    """核心模块3: 防刷屏 - 每天每ID只能提交一次"""
    data = request.json
    link = data.get('link', '')
    username = data.get('username', 'demo_user')
    
    # 验证链接
    if not link or ('twitter.com' not in link and 'x.com' not in link):
        return jsonify({'success': False, 'error': '请输入有效的Twitter链接'}), 400
    
    today = get_today_utc_date()
    
    # 检查是否已提交
    for uid, user in USERS.items():
        if user['username'] == username:
            if user.get('last_submit_date') == today:
                return jsonify({'success': False, 'error': '今日已提交'}), 400
            # 更新提交记录
            user['last_submit_date'] = today
            user['links_today'] = user.get('links_today', 0) + 1
            break
    
    # 添加新任务
    tasks = get_tasks_for_today()
    new_id = max([t['id'] for t in tasks], default=0) + 1
    
    # 找到用户信息
    user_info = USERS.get(1, {'username': username, 'avatar': 'https://picsum.photos/200'})
    
    new_task = {
        'id': new_id,
        'userId': user_info.get('id', 1),
        'username': username,
        'avatar': user_info.get('avatar', 'https://picsum.photos/200'),
        'link': link,
        'liked': False,
        'retweeted': False,
        'commented': False
    }
    tasks.append(new_task)
    
    return jsonify({'success': True, 'task': new_task})

@app.route('/api/interact', methods=['POST'])
def interact():
    data = request.json
    task_id = data.get('taskId')
    action = data.get('action')
    
    tasks = get_tasks_for_today()
    
    for task in tasks:
        if task['id'] == task_id:
            if action == 'like':
                task['liked'] = not task.get('liked', False)
            elif action == 'retweet':
                task['retweeted'] = not task.get('retweeted', False)
            elif action == 'comment':
                task['commented'] = not task.get('commented', False)
            
            # 更新用户互动数
            owner_id = task.get('userId')
            if owner_id in USERS:
                USERS[owner_id]['interactions_today'] = USERS[owner_id].get('interactions_today', 0) + 1
            break
    
    return jsonify({'success': True})

@app.route('/auth/twitter')
def auth_twitter():
    if not TWITTER_API_KEY or not TWITTER_API_SECRET:
        return jsonify({'error': 'Twitter API not configured'}), 500
    
    import secrets
    oauth_token = secrets.token_urlsafe(32)
    session['oauth_token'] = oauth_token
    
    auth_url = f"https://twitter.com/i/oauth2/authorize?response_type=code&client_id={TWITTER_API_KEY}&redirect_uri={CALLBACK_URL}&scope=tweet.read%20users.read&state={oauth_token}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    return redirect('/?logged_in=true')
