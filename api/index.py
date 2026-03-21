# Vercel API - Advanced Features
import os
import json
from flask import Flask, request, jsonify, redirect, session, render_template
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY', '')
TWITTER_API_SECRET = os.environ.get('TWITTER_API_SECRET', '')
CALLBACK_URL = os.environ.get('CALLBACK_URL', 'https://task-tracker-kohl-one-14.vercel.app/callback')

# 高级用户数据结构
USERS = {
    1: {
        'id': 1, 'username': 'crypto_king', 'name': 'Crypto King', 
        'avatar': 'https://picsum.photos/100', 
        'links_today': 3, 'interactions_today': 12,
        'last_submit_date': None,
        # 信用分系统
        'credit_score': 10,  # 互动信用分
        'negative_days': 0,  # 连续负数天数
        'is_restricted': False,  # 是否被熔断
        'submissions_received': 0,  # 被别人互动的次数
    },
    2: {'id': 2, 'username': 'defi_girl', 'name': 'DeFi Girl', 'avatar': 'https://picsum.photos/101', 'links_today': 2, 'interactions_today': 8, 'last_submit_date': None, 'credit_score': 5, 'negative_days': 0, 'is_restricted': False, 'submissions_received': 0},
    3: {'id': 3, 'username': 'whale_watcher', 'name': 'Whale Watcher', 'avatar': 'https://picsum.photos/102', 'links_today': 5, 'interactions_today': 2, 'last_submit_date': None, 'credit_score': -3, 'negative_days': 2, 'is_restricted': False, 'submissions_received': 0},
    4: {'id': 4, 'username': 'nft_collector', 'name': 'NFT Collector', 'avatar': 'https://picsum.photos/103', 'links_today': 1, 'interactions_today': 15, 'last_submit_date': None, 'credit_score': 14, 'negative_days': 0, 'is_restricted': False, 'submissions_received': 0},
    5: {'id': 5, 'username': 'memecoin_lad', 'name': 'Memecoin Lad', 'avatar': 'https://picsum.photos/104', 'links_today': 8, 'interactions_today': 1, 'last_submit_date': None, 'credit_score': -7, 'negative_days': 3, 'is_restricted': True, 'submissions_received': 0},
}

TASKS = {}

def get_today_utc_date():
    return datetime.utcnow().strftime('%Y-%m-%d')

def get_utc_midnight():
    now = datetime.utcnow()
    return datetime(now.year, now.month, now.day)

def get_seconds_until_midnight():
    now = datetime.utcnow()
    midnight = get_utc_midnight() + timedelta(days=1)
    delta = midnight - now
    return int(delta.total_seconds())

def get_tasks_for_today():
    today = get_today_utc_date()
    if today not in TASKS:
        TASKS[today] = [
            {'id': 1, 'userId': 1, 'username': 'crypto_king', 'avatar': 'https://picsum.photos/100', 'link': 'https://x.com/crypto_king/status/123456789', 'liked': False, 'retweeted': False, 'commented': False},
            {'id': 2, 'userId': 2, 'username': 'defi_girl', 'avatar': 'https://picsum.photos/101', 'link': 'https://x.com/defi_girl/status/123456788', 'liked': False, 'retweeted': False, 'commented': False},
            {'id': 3, 'userId': 3, 'username': 'whale_watcher', 'avatar': 'https://picsum.photos/102', 'link': 'https://x.com/whale_watcher/status/123456787', 'liked': False, 'retweeted': False, 'commented': False},
            {'id': 4, 'userId': 4, 'username': 'nft_collector', 'avatar': 'https://picsum.photos/103', 'link': 'https://x.com/nft_collector/status/123456786', 'liked': False, 'retweeted': False, 'commented': False},
            {'id': 5, 'userId': 5, 'username': 'memecoin_lad', 'avatar': 'https://picsum.photos/104', 'link': 'https://x.com/memecoin_lad/status/123456785', 'liked': False, 'retweeted': False, 'commented': False},
        ]
    return TASKS[today]

# 前置任务要求数量
REQUIRED_INTERACTIONS_TO_UNLOCK = 3

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config')
def get_config():
    """返回前端配置"""
    return jsonify({
        'requiredInteractions': REQUIRED_INTERACTIONS_TO_UNLOCK
    })

@app.route('/api/countdown')
def get_countdown():
    return jsonify({
        'seconds': get_seconds_until_midnight(),
        'resetTime': '08:00:00',
        'utcReset': '00:00:00'
    })

@app.route('/api/user')
def get_user():
    return jsonify(USERS[1])

@app.route('/api/users')
def get_users():
    today_users = []
    for uid, user in USERS.items():
        today_users.append({
            'id': user['id'],
            'username': user['username'],
            'avatar': user['avatar'],
            'links': user.get('links_today', 0),
            'interactions': user.get('interactions_today', 0),
            'credit_score': user.get('credit_score', 0),
            'is_restricted': user.get('is_restricted', False),
            'negative_days': user.get('negative_days', 0)
        })
    today_users.sort(key=lambda x: x['interactions'], reverse=True)
    return jsonify(today_users)

@app.route('/api/tasks')
def get_tasks():
    """随机化任务池"""
    tasks = get_tasks_for_today()
    # 随机打乱任务顺序
    random.shuffle(tasks)
    return jsonify(tasks)

@app.route('/api/my-progress')
def get_my_progress():
    """获取当前用户的互动进度"""
    user = USERS[1]
    interactions_done = user.get('interactions_today', 0)
    return jsonify({
        'interactions_done': interactions_done,
        'required': REQUIRED_INTERACTIONS_TO_UNLOCK,
        'remaining': max(0, REQUIRED_INTERACTIONS_TO_UNLOCK - interactions_done),
        'is_unlocked': interactions_done >= REQUIRED_INTERACTIONS_TO_UNLOCK,
        'is_restricted': user.get('is_restricted', False),
        'credit_score': user.get('credit_score', 0)
    })

@app.route('/api/submit', methods=['POST'])
def submit_link():
    data = request.json
    link = data.get('link', '')
    username = data.get('username', 'demo_user')
    
    if not link or ('twitter.com' not in link and 'x.com' not in link):
        return jsonify({'success': False, 'error': '请输入有效的Twitter链接'}), 400
    
    # 查找用户
    user = None
    for uid, u in USERS.items():
        if u['username'] == username:
            user = u
            break
    
    if not user:
        return jsonify({'success': False, 'error': '用户不存在'}), 400
    
    # 检查是否被熔断
    if user.get('is_restricted', False):
        return jsonify({'success': False, 'error': '🚫 您已被限制提交，请先补齐欠下的互动'}), 400
    
    # 检查是否完成前置任务
    if user.get('interactions_today', 0) < REQUIRED_INTERACTIONS_TO_UNLOCK:
        return jsonify({'success': False, 'error': f'还需完成 {REQUIRED_INTERACTIONS_TO_UNLOCK - user.get("interactions_today", 0)} 次互动才能提交'}), 400
    
    today = get_today_utc_date()
    if user.get('last_submit_date') == today:
        return jsonify({'success': False, 'error': '今日已提交'}), 400
    
    # 添加任务
    tasks = get_tasks_for_today()
    new_id = max([t['id'] for t in tasks], default=0) + 1
    
    new_task = {
        'id': new_id,
        'userId': user['id'],
        'username': username,
        'avatar': user['avatar'],
        'link': link,
        'liked': False,
        'retweeted': False,
        'commented': False
    }
    tasks.append(new_task)
    
    user['last_submit_date'] = today
    user['links_today'] = user.get('links_today', 0) + 1
    
    return jsonify({'success': True, 'task': new_task})

@app.route('/api/interact', methods=['POST'])
def interact():
    data = request.json
    task_id = data.get('taskId')
    action = data.get('action')
    
    tasks = get_tasks_for_today()
    
    for task in tasks:
        if task['id'] == task_id:
            already_done = task.get('liked', False) and task.get('retweeted', False) and task.get('commented', False)
            
            if action == 'like':
                task['liked'] = not task.get('liked', False)
            elif action == 'retweet':
                task['retweeted'] = not task.get('retweeted', False)
            elif action == 'comment':
                task['commented'] = not task.get('commented', False)
            
            # 只有从"未完成"变为"完成"时才增加计数
            if not already_done and (task['liked'] or task['retweeted'] or task['commented']):
                # 增加互动者的计数
                USERS[1]['interactions_today'] = USERS[1].get('interactions_today', 0) + 1
                USERS[1]['credit_score'] = USERS[1].get('credit_score', 0) + 1
                
                # 增加被互动者的被互动次数
                owner_id = task.get('userId')
                if owner_id in USERS:
                    USERS[owner_id]['submissions_received'] = USERS[owner_id].get('submissions_received', 0) + 1
                    # 更新信用分：被互动 = 获得收益
                    USERS[owner_id]['credit_score'] = USERS[owner_id].get('credit_score', 0) + 1
                
                # 检查是否解锁
                if USERS[1].get('interactions_today', 0) >= REQUIRED_INTERACTIONS_TO_UNLOCK:
                    # 播放解锁音效（前端处理）
                    pass
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
    return redirect('/?logged_in=true')
