# Flask API - Complete Twitter OAuth + Supabase
import os
import json
import secrets
import base64
import urllib.request
import urllib.parse
from flask import Flask, request, jsonify, redirect, render_template

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Twitter OAuth 2.0
CLIENT_ID = 'T05CT3pQT0hOcE1vQlJrVHN0Y3E6MTpjaQ'
CLIENT_SECRET = 'EnzHhIP22RWI8ujFOzFyPneaYQKAH1BwrUGTP8_NbrsTV67Dz8'
CALLBACK_URL = 'https://task-tracker-kohl-one-14.vercel.app/callback'

# Supabase
SUPABASE_URL = 'https://vejicltqodkdjchqlrqx.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlamljbHRxb2RkZGpjaHFscnF4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQwOTcxMDgsImV4cCI6MjA4OTY3MzEwOH0.uNeQttyjwZTjVhicd0oftdgWIkvdqFrtXLaCe9mjrJE'

auth_states = {}

def supabase_request(method, path, data=None):
    url = SUPABASE_URL + '/rest/v1/' + path
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    if method == 'GET':
        req = urllib.request.Request(url, headers=headers)
    else:
        req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None, headers=headers)
        req.get_method = lambda: method
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"Supabase error: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth/twitter')
def auth_twitter():
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(32)
    code_challenge = secrets.token_urlsafe(32)
    
    auth_states[state] = code_verifier
    
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': CALLBACK_URL,
        'scope': 'tweet.read users.read',
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'plain'
    }
    
    return redirect('https://twitter.com/i/oauth2/authorize?' + urllib.parse.urlencode(params))

@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or not state or state not in auth_states:
        return redirect('/?error=invalid')
    
    code_verifier = auth_states[state]
    
    try:
        # 换取 token
        token_url = 'https://api.twitter.com/2/oauth2/token'
        credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
        
        data = urllib.parse.urlencode({
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': CALLBACK_URL,
            'client_id': CLIENT_ID,
            'code_verifier': code_verifier
        }).encode()
        
        req = urllib.request.Request(token_url, data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        req.add_header('Authorization', f'Basic {base64.b64encode(credentials.encode()).decode()}')
        
        with urllib.request.urlopen(req, timeout=20) as resp:
            token = json.loads(resp.read())
            access_token = token.get('access_token')
            
            if access_token:
                # 获取用户信息
                user_req = urllib.request.Request(
                    'https://api.twitter.com/2/users/me?user.fields=username,name,profile_image_url'
                )
                user_req.add_header('Authorization', f'Bearer {access_token}')
                
                with urllib.request.urlopen(user_req, timeout=20) as u_resp:
                    profile = json.load(u_resp)
                    
                    if 'data' in profile:
                        data = profile['data']
                        username = data.get('username', '')
                        name = data.get('name', username)
                        avatar = data.get('profile_image_url', '').replace('_normal', '')
                        
                        # 存入 Supabase 数据库
                        user_data = {
                            'username': username,
                            'name': name,
                            'avatar_url': avatar
                        }
                        
                        # 检查用户是否存在，不存在则创建
                        existing = supabase_request('GET', f'users?username=eq.{username}')
                        if not existing or len(existing) == 0:
                            supabase_request('POST', 'users', user_data)
                        
                        # 跳转回首页
                        return redirect(
                            f'/?twitter_user={urllib.parse.quote(username)}'
                            f'&twitter_name={urllib.parse.quote(name)}'
                            f'&twitter_avatar={urllib.parse.quote(avatar)}'
                        )
    except Exception as e:
        print(f"Error: {e}")
        return redirect(f'/?error={str(e)}')
    
    return redirect('/?error=unknown')

@app.route('/api/user')
def get_user():
    username = request.args.get('username')
    if username:
        # 从 Supabase 获取用户信息
        users = supabase_request('GET', f'users?username=eq.{username}')
        if users and len(users) > 0:
            u = users[0]
            return jsonify({
                'username': u.get('username', username),
                'name': u.get('name', username),
                'avatar': u.get('avatar_url', f'https://api.dicebear.com/7.x/avataaars/svg?seed={username}'),
                'links': 0,
                'interactions': 0
            })
        return jsonify({
            'username': username,
            'name': request.args.get('name', username),
            'avatar': request.args.get('avatar', f'https://api.dicebear.com/7.x/avataaars/svg?seed={username}'),
            'links': 0,
            'interactions': 0
        })
    return jsonify({'username': 'guest', 'avatar': 'https://api.dicebear.com/7.x/avataaars/svg?seed=guest', 'links': 0, 'interactions': 0})

@app.route('/api/users')
def get_users():
    users = supabase_request('GET', 'users?order=created_at.desc&limit=20')
    return jsonify(users or [])

@app.route('/api/tasks')
def get_tasks():
    tasks = supabase_request('GET', 'tasks?order=id.desc&limit=50')
    if not tasks:
        tasks = []
        for i in range(1, 26):
            tasks.append({
                'id': i,
                'username': f'user_{i}',
                'avatar_url': f'https://api.dicebear.com/7.x/avataaars/svg?seed=user{i}',
                'link': f'https://x.com/user_{i}/status/{123456780+i}',
                'liked': False,
                'retweeted': False,
                'commented': False
            })
    return jsonify(tasks)

@app.route('/api/countdown')
def get_countdown():
    return jsonify({'seconds': 86400})

@app.route('/api/interact', methods=['POST'])
def interact():
    data = request.json
    if data:
        # 保存到 Supabase
        supabase_request('POST', 'interactions', {
            'username': data.get('username', 'guest'),
            'task_id': data.get('task_id')
        })
    return jsonify({'success': True})

@app.route('/api/submit', methods=['POST'])
def submit():
    data = request.json
    if data:
        supabase_request('POST', 'tasks', {
            'username': data.get('username', 'guest'),
            'avatar_url': data.get('avatar', ''),
            'link': data.get('link', '')
        })
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
