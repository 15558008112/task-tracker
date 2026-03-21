# Vercel API - Twitter OAuth 2.0
import os
import json
import secrets
import base64
import time
import hashlib
import hmac
import urllib.request
import urllib.parse
from flask import Flask, request, jsonify, redirect, render_template

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Twitter OAuth 2.0 Config (用户提供的Keys)
TWITTER_CLIENT_ID = 'T05CT3pQT0hOcE1vQlJrVHN0Y3E6MTpjaQ'
TWITTER_CLIENT_SECRET = 'EnzHhIP22RWI8ujFOzFyPneaYQKAH1BwrUGTP8_NbrsTV67Dz8'
CALLBACK_URL = 'https://task-tracker-kohl-one-14.vercel.app/callback'

# 存储 state 和 code_verifier
auth_states = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth/twitter')
def auth_twitter():
    # 生成 OAuth 2.0 授权 URL
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(32)
    code_challenge = secrets.token_urlsafe(32)
    
    # 存储 state 对应关系
    auth_states[state] = {'code_verifier': code_verifier}
    
    params = {
        'response_type': 'code',
        'client_id': TWITTER_CLIENT_ID,
        'redirect_uri': CALLBACK_URL,
        'scope': 'tweet.read users.read',
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'plain'
    }
    
    auth_url = 'https://twitter.com/i/oauth2/authorize?' + urllib.parse.urlencode(params)
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or not state:
        return redirect('/?error=no_code')
    
    if state not in auth_states:
        return redirect('/?error=invalid_state')
    
    code_verifier = auth_states[state].get('code_verifier')
    
    try:
        # 换取 access token
        token_url = 'https://api.twitter.com/2/oauth2/token'
        
        credentials = f"{TWITTER_CLIENT_ID}:{TWITTER_CLIENT_SECRET}"
        auth_header = base64.b64encode(credentials.encode()).decode()
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': CALLBACK_URL,
            'client_id': TWITTER_CLIENT_ID,
            'code_verifier': code_verifier
        }
        
        req = urllib.request.Request(token_url, data=urllib.parse.urlencode(data).encode(), method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        req.add_header('Authorization', f'Basic {auth_header}')
        
        with urllib.request.urlopen(req, timeout=20) as resp:
            token_result = json.loads(resp.read().decode('utf-8'))
            access_token = token_result.get('access_token')
            
            if access_token:
                # 获取用户信息
                user_req = urllib.request.Request('https://api.twitter.com/2/users/me?user.fields=username,name,profile_image_url')
                user_req.add_header('Authorization', f'Bearer {access_token}')
                
                with urllib.request.urlopen(user_req, timeout=20) as user_resp:
                    profile = json.loads(user_resp.read().decode('utf-8'))
                    
                    if 'data' in profile:
                        data = profile['data']
                        username = data.get('username', 'user')
                        name = data.get('name', username)
                        avatar = data.get('profile_image_url', '').replace('_normal', '')
                        
                        # 跳转回首页并携带用户信息
                        return redirect(f'/?twitter_user={username}&twitter_name={name}&twitter_avatar={urllib.parse.quote(avatar)}')
    except Exception as e:
        print(f"OAuth error: {e}")
        return redirect(f'/?error={str(e)}')
    
    return redirect('/?error=unknown')

@app.route('/api/user')
def get_user():
    username = request.args.get('username')
    if username:
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
    return jsonify([])

@app.route('/api/tasks')
def get_tasks():
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
    return jsonify({'success': True})

@app.route('/api/submit', methods=['POST'])
def submit():
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
