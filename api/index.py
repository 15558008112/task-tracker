# Vercel API - Twitter OAuth Login
import os
import json
import secrets
from flask import Flask, request, jsonify, redirect, session, render_template

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Twitter OAuth Config
TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY', '')
TWITTER_API_SECRET = os.environ.get('TWITTER_API_SECRET', '')
CALLBACK_URL = os.environ.get('CALLBACK_URL', 'https://task-tracker-kohl-one-14.vercel.app/callback')

# In-memory session
current_user = None

# Demo users
DEMO_USERS = {
    1: {'id': 1, 'username': 'crypto_king', 'name': 'Crypto King', 'avatar': 'https://api.dicebear.com/7.x/avataaars/svg?seed=crypto', 'links': 3, 'interactions': 12, 'is_demo': True},
}

# Tasks
all_tasks = []

def init_tasks():
    global all_tasks
    if not all_tasks:
        for i in range(1, 26):
            all_tasks.append({
                'id': i,
                'username': f'user_{i}',
                'avatar': f'https://api.dicebear.com/7.x/avataaars/svg?seed=user{i}',
                'link': f'https://x.com/user_{i}/status/{123456780+i}',
                'liked': False,
                'retweeted': False,
                'commented': False
            })

init_tasks()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    global current_user
    if current_user:
        return jsonify({'logged_in': True, 'user': current_user})
    return jsonify({'logged_in': False})

@app.route('/api/login', methods=['POST'])
def login():
    global current_user, TWITTER_API_KEY, TWITTER_API_SECRET
    
    # Demo mode - use demo user
    if not TWITTER_API_KEY or not TWITTER_API_SECRET:
        current_user = DEMO_USERS[1]
        return jsonify({'success': True, 'demo': True, 'user': current_user})
    
    # Real OAuth
    auth_url = f"https://twitter.com/i/oauth2/authorize?response_type=code&client_id={TWITTER_API_KEY}&redirect_uri={CALLBACK_URL}&scope=tweet.read%20users.read"
    return jsonify({'auth_url': auth_url})

@app.route('/api/logout', methods=['POST'])
def logout():
    global current_user
    current_user = None
    session.clear()
    return jsonify({'success': True})

@app.route('/api/user')
def get_user():
    global current_user
    if current_user:
        return jsonify(current_user)
    return jsonify(DEMO_USERS[1])

@app.route('/api/users')
def get_users():
    users = list(DEMO_USERS.values())
    users.sort(key=lambda x: x.get('interactions', 0), reverse=True)
    return jsonify(users)

@app.route('/api/tasks')
def get_tasks():
    return jsonify(all_tasks)

@app.route('/api/countdown')
def get_countdown():
    return jsonify({'seconds': 86400})

@app.route('/api/interact', methods=['POST'])
def interact():
    data = request.json
    task_id = data.get('taskId')
    
    global all_tasks
    for task in all_tasks:
        if task['id'] == task_id:
            task['liked'] = task['retweeted'] = task['commented'] = True
            break
    
    return jsonify({'success': True})

@app.route('/api/submit', methods=['POST'])
def submit():
    global current_user
    data = request.json
    link = data.get('link', '')
    
    if not current_user:
        return jsonify({'success': False, 'error': '请先登录'}), 400
    
    # Check if already submitted
    for task in all_tasks:
        if task.get('username') == current_user.get('username'):
            return jsonify({'success': False, 'error': '今日已提交'}), 400
    
    # Add new task
    new_task = {
        'id': len(all_tasks) + 1,
        'username': current_user.get('username', 'anonymous'),
        'avatar': current_user.get('avatar', 'https://api.dicebear.com/7.x/avataaars/svg?seed=anonymous'),
        'link': link,
        'liked': False,
        'retweeted': False,
        'commented': False
    }
    all_tasks.insert(0, new_task)
    
    return jsonify({'success': True, 'task': new_task})

@app.route('/callback')
def callback():
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
