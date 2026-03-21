# Vercel API - Supabase Database
import os
import json
import secrets
from flask import Flask, request, jsonify, redirect, render_template
import urllib.request
import urllib.parse

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Supabase Config
SUPABASE_URL = 'https://vejicltqodkdjchqlrqx.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlamljbHRxb2RrZGpjaHFscnF4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQwOTcxMDgsImV4cCI6MjA4OTY3MzEwOH0.uNeQttyjwZTjVhicd0oftdgWIkvdqFrtXLaCe9mjrJE'

def supabase_request(table, method='GET', data=None):
    """Make request to Supabase REST API"""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    if method == 'GET':
        req = urllib.request.Request(url, headers=headers)
    else:
        data_json = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=data_json, headers=headers)
        req.get_method = lambda: method
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Supabase error: {e}")
        return None

def get_user_id():
    """Get or create user from cookie"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        user_id = secrets.token_urlsafe(16)
    return user_id

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    user_id = get_user_id()
    result = supabase_request(f"users?id=eq.{user_id}")
    if result and len(result) > 0:
        return jsonify({'logged_in': True, 'user': result[0]})
    return jsonify({'logged_in': False})

@app.route('/api/login', methods=['POST'])
def login():
    user_id = get_user_id()
    username = f"user_{user_id[:6]}"
    avatar_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={user_id}"
    
    # Check if user exists
    existing = supabase_request(f"users?id=eq.{user_id}")
    
    if not existing or len(existing) == 0:
        # Create new user
        new_user = {
            'id': user_id,
            'username': username,
            'name': username,
            'avatar_url': avatar_url,
            'links': 0,
            'interactions': 0
        }
        supabase_request('users', method='POST', data=new_user)
    
    return jsonify({
        'success': True, 
        'user': {
            'id': user_id,
            'username': username,
            'avatar': avatar_url,
            'links': 0,
            'interactions': 0
        },
        'user_id': user_id
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    return jsonify({'success': True})

@app.route('/api/user')
def get_user():
    user_id = get_user_id()
    result = supabase_request(f"users?id=eq.{user_id}")
    if result and len(result) > 0:
        return jsonify(result[0])
    return jsonify({'username': 'guest', 'links': 0, 'interactions': 0})

@app.route('/api/users')
def get_users():
    result = supabase_request('users?order=interactions.desc&limit=20')
    return jsonify(result if result else [])

@app.route('/api/tasks')
def get_tasks():
    # Get today's tasks only
    result = supabase_request('tasks?order=created_at.desc&limit=50')
    if not result:
        # Return demo tasks if DB is empty
        demo_tasks = []
        for i in range(1, 26):
            demo_tasks.append({
                'id': i,
                'username': f'user_{i}',
                'avatar_url': f'https://api.dicebear.com/7.x/avataaars/svg?seed=user{i}',
                'link': f'https://x.com/user_{i}/status/{123456780+i}',
                'liked': False,
                'retweeted': False,
                'commented': False
            })
        return jsonify(demo_tasks)
    return jsonify(result)

@app.route('/api/countdown')
def get_countdown():
    return jsonify({'seconds': 86400})

@app.route('/api/interact', methods=['POST'])
def interact():
    data = request.json
    task_id = data.get('taskId')
    user_id = get_user_id()
    
    # Update task
    supabase_request(f'tasks?id=eq.{task_id}', method='PATCH', data={
        'liked': True,
        'retweeted': True,
        'commented': True
    })
    
    # Update user interactions
    result = supabase_request(f"users?id=eq.{user_id}")
    if result and len(result) > 0:
        user = result[0]
        new_interactions = user.get('interactions', 0) + 1
        supabase_request(f'users?id=eq.{user_id}', method='PATCH', data={
            'interactions': new_interactions
        })
    
    return jsonify({'success': True})

@app.route('/api/submit', methods=['POST'])
def submit():
    data = request.json
    link = data.get('link', '')
    user_id = get_user_id()
    
    # Get user info
    result = supabase_request(f"users?id=eq.{user_id}")
    if not result or len(result) == 0:
        return jsonify({'success': False, 'error': '请先登录'}), 400
    
    user = result[0]
    
    # Check if already submitted today
    today_tasks = supabase_request(f"users/username=eq.{user['username']}&tasks")
    if today_tasks and len(today_tasks) > 0:
        return jsonify({'success': False, 'error': '今日已提交'}), 400
    
    # Add new task
    new_task = {
        'user_id': user_id,
        'username': user['username'],
        'avatar_url': user.get('avatar_url', ''),
        'link': link,
        'liked': False,
        'retweeted': False,
        'commented': False
    }
    supabase_request('tasks', method='POST', data=new_task)
    
    # Update user links count
    new_links = user.get('links', 0) + 1
    supabase_request(f'users?id=eq.{user_id}', method='PATCH', data={'links': new_links})
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
