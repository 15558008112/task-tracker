# Vercel API - Auto Login
import os
import json
import secrets
from flask import Flask, request, jsonify, redirect, session, render_template

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Simple in-memory storage (works during session)
users = {}
tasks = []

def get_user_id():
    """Get or create user from cookie"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        user_id = secrets.token_urlsafe(16)
    return user_id

def init_tasks():
    global tasks
    if not tasks:
        for i in range(1, 26):
            tasks.append({
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
    user_id = get_user_id()
    user = users.get(user_id)
    if user:
        return jsonify({'logged_in': True, 'user': user})
    return jsonify({'logged_in': False})

@app.route('/api/login', methods=['POST'])
def login():
    user_id = get_user_id()
    
    # Auto-create or get user
    if user_id not in users:
        username = f"user_{user_id[:6]}"
        users[user_id] = {
            'id': user_id,
            'username': username,
            'name': username,
            'avatar': f'https://api.dicebear.com/7.x/avataaars/svg?seed={user_id}',
            'links': 0,
            'interactions': 0
        }
    
    return jsonify({
        'success': True, 
        'user': users[user_id],
        'user_id': user_id
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    return jsonify({'success': True})

@app.route('/api/user')
def get_user():
    user_id = get_user_id()
    if user_id in users:
        return jsonify(users[user_id])
    return jsonify({'username': 'guest', 'avatar': 'https://api.dicebear.com/7.x/avataaars/svg?seed=guest', 'links': 0, 'interactions': 0})

@app.route('/api/users')
def get_users():
    user_list = list(users.values())
    user_list.sort(key=lambda x: x.get('interactions', 0), reverse=True)
    return jsonify(user_list[:20])

@app.route('/api/tasks')
def get_tasks():
    return jsonify(tasks)

@app.route('/api/countdown')
def get_countdown():
    return jsonify({'seconds': 86400})

@app.route('/api/interact', methods=['POST'])
def interact():
    data = request.json
    task_id = data.get('taskId')
    user_id = get_user_id()
    
    global tasks
    for task in tasks:
        if task['id'] == task_id:
            task['liked'] = task['retweeted'] = task['commented'] = True
            break
    
    # Update user interactions
    if user_id in users:
        users[user_id]['interactions'] = users[user_id].get('interactions', 0) + 1
    
    return jsonify({'success': True})

@app.route('/api/submit', methods=['POST'])
def submit():
    data = request.json
    link = data.get('link', '')
    user_id = get_user_id()
    
    if user_id not in users:
        return jsonify({'success': False, 'error': '请先登录'}), 400
    
    user = users[user_id]
    
    # Check if already submitted
    for task in tasks:
        if task.get('username') == user.get('username'):
            return jsonify({'success': False, 'error': '今日已提交'}), 400
    
    # Add new task
    new_task = {
        'id': len(tasks) + 1,
        'username': user['username'],
        'avatar': user['avatar'],
        'link': link,
        'liked': False,
        'retweeted': False,
        'commented': False
    }
    tasks.insert(0, new_task)
    user['links'] = user.get('links', 0) + 1
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
