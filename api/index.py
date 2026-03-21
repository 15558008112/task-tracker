# Vercel API - Twitter OAuth
import os
import json
import secrets
import base64
from flask import Flask, request, jsonify, redirect, render_template
import urllib.request
import urllib.parse

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Config
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://vejicltqodkdjchqlrqx.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlamljbHRxb2RrZGpjaHFscnF4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQwOTcxMDgsImV4cCI6MjA4OTY3MzEwOH0.uNeQttyjwZTjVhicd0oftdgWIkvdqFrtXLaCe9mjrJE')

TWITTER_CLIENT_ID = 'T05CT3pQT0hOcE1vQlJrVHN0Y3E6MTpjaQ'
TWITTER_CLIENT_SECRET = 'EnzHhIP22RWI8ujFOzFyPneaYQKAH1BwrUGTP8_NbrsTV67Dz8'
CALLBACK_URL = 'https://task-tracker-kohl-one-14.vercel.app/callback'

def supabase_request(table, method='GET', data=None, query=''):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    if query:
        url += '?' + query
    
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    try:
        if method == 'GET':
            req = urllib.request.Request(url, headers=headers)
        else:
            data_json = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=data_json, headers=headers)
            req.get_method = lambda: method
        
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login')
def login():
    state = secrets.token_urlsafe(32)
    auth_url = f"https://twitter.com/i/oauth2/authorize?response_type=code&client_id={TWITTER_CLIENT_ID}&redirect_uri={CALLBACK_URL}&scope=tweet.read%20users.read&state={state}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    
    if not code:
        return redirect('/?error=no_code')
    
    try:
        # Exchange code for token
        token_url = 'https://api.twitter.com/2/oauth2/token'
        credentials = base64.b64encode(f"{TWITTER_CLIENT_ID}:{TWITTER_CLIENT_SECRET}".encode()).decode()
        
        data = urllib.parse.urlencode({
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': CALLBACK_URL,
            'code_verifier': 'challenge'
        }).encode('utf-8')
        
        req = urllib.request.Request(token_url, data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        req.add_header('Authorization', f'Basic {credentials}')
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            token_result = json.loads(resp.read().decode('utf-8'))
            access_token = token_result.get('access_token')
            
            if access_token:
                # Get user info
                user_req = urllib.request.Request('https://api.twitter.com/2/users/me?user.fields=username,name,profile_image_url')
                user_req.add_header('Authorization', f'Bearer {access_token}')
                
                with urllib.request.urlopen(user_req, timeout=15) as user_resp:
                    user_data = json.loads(user_resp.read().decode('utf-8'))
                    
                    if 'data' in user_data:
                        t_user = user_data['data']
                        username = t_user.get('username', 'user')
                        name = t_user.get('name', username)
                        avatar = t_user.get('profile_image_url', '').replace('_normal', '')
                        
                        # Redirect with user info
                        return redirect(f'/?twitter_user={username}&twitter_name={name}&twitter_avatar={avatar}')
    except Exception as e:
        print(f"Callback error: {e}")
        return redirect('/?error=oauth_failed')
    
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
