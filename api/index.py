# Vercel API - Real Twitter OAuth
import os
import json
import secrets
from flask import Flask, request, jsonify, redirect, render_template
import urllib.request
import urllib.parse
import urllib.error

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Twitter OAuth 2.0 Config
TWITTER_CLIENT_ID = 'T05CT3pQT0hOcE1vQlJrVHN0Y3E6MTpjaQ'
TWITTER_CLIENT_SECRET = 'EnzHhIP22RWI8ujFOzFyPneaYQKAH1BwrUGTP8_NbrsTV67Dz8'
CALLBACK_URL = 'https://task-tracker-kohl-one-14.vercel.app/callback'

# Supabase Config
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://vejicltqodkdjchqlrqx.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlamljbHRxb2RrZGpjaHFscnF4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQwOTcxMDgsImV4cCI6MjA4OTY3MzEwOH0.uNeQttyjwZTjVhicd0oftdgWIkvdqFrtXLaCe9mjrJE')

# In-memory token storage (in production, use database)
access_tokens = {}

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
        
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Supabase error: {e}")
        return None

def get_user_id():
    return request.cookies.get('user_id')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    user_id = get_user_id()
    if user_id and user_id in access_tokens:
        return jsonify({'logged_in': True, 'user': {'username': 'Twitter User', 'avatar': 'https://api.dicebear.com/7.x/avataaars/svg?seed=twitter'}})
    return jsonify({'logged_in': False})

@app.route('/api/login')
def login():
    redirect_param = request.args.get('redirect')
    
    # Generate state for security
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    # Build Twitter OAuth 2.0 authorization URL
    auth_url = (
        f"https://twitter.com/i/oauth2/authorize?"
        f"response_type=code&"
        f"client_id={TWITTER_CLIENT_ID}&"
        f"redirect_uri={CALLBACK_URL}&"
        f"scope=tweet.read%20users.read&"
        f"state={state}&"
        f"code_challenge=challenge&"
        f"code_challenge_method=plain"
    )
    
    if redirect_param == 'true':
        return redirect(auth_url)
    
    return jsonify({'auth_url': auth_url})

@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code:
        return redirect('/')
    
    # Exchange code for access token
    token_url = 'https://api.twitter.com/2/oauth2/token'
    data = urllib.parse.urlencode({
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': CALLBACK_URL,
        'client_id': TWITTER_CLIENT_ID,
        'code_verifier': 'challenge'
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(token_url, data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        import base64
        credentials = base64.b64encode(f"{TWITTER_CLIENT_ID}:{TWITTER_CLIENT_SECRET}".encode()).decode()
        req.add_header('Authorization', f'Basic {credentials}')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            token_data = json.loads(response.read().decode('utf-8'))
            access_token = token_data.get('access_token')
            
            if access_token:
                # Get user info from Twitter
                user_req = urllib.request.Request('https://api.twitter.com/2/users/me?tweet.fields=public_metrics', 
                    headers={'Authorization': f'Bearer {access_token}'})
                with urllib.request.urlopen(user_req, timeout=10) as user_response:
                    twitter_user = json.loads(user_response.read().decode('utf-8'))
                    
                    if 'data' in twitter_user:
                        user_data = twitter_user['data']
                        user_id = str(user_data.get('id'))
                        
                        # Save token
                        access_tokens[user_id] = access_token
                        
                        # Save to Supabase
                        supabase_request('users', method='POST', data={
                            'id': user_id,
                            'username': user_data.get('username'),
                            'name': user_data.get('name'),
                            'avatar_url': user_data.get('profile_image_url', '').replace('_normal', ''),
                            'links': 0,
                            'interactions': 0
                        })
                        
                        return jsonify({'success': True, 'user': user_data})
    except Exception as e:
        print(f"OAuth error: {e}")
    
    return redirect('/')

@app.route('/api/logout', methods=['POST'])
def logout():
    return jsonify({'success': True})

@app.route('/api/user')
def get_user():
    user_id = get_user_id()
    if user_id and user_id in access_tokens:
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
    result = supabase_request('tasks?order=created_at.desc&limit=50')
    if not result:
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
    
    supabase_request(f'tasks?id=eq.{task_id}', method='PATCH', data={
        'liked': True,
        'retweeted': True,
        'commented': True
    })
    
    return jsonify({'success': True})

@app.route('/api/submit', methods=['POST'])
def submit():
    data = request.json
    link = data.get('link', '')
    user_id = get_user_id()
    
    if not user_id:
        return jsonify({'success': False, 'error': '请先登录'}), 400
    
    result = supabase_request(f"users?id=eq.{user_id}")
    if not result or len(result) == 0:
        return jsonify({'success': False, 'error': '请先登录'}), 400
    
    user = result[0]
    
    new_task = {
        'user_id': user_id,
        'username': user.get('username', 'anonymous'),
        'avatar_url': user.get('avatar_url', ''),
        'link': link,
        'liked': False,
        'retweeted': False,
        'commented': False
    }
    supabase_request('tasks', method='POST', data=new_task)
    
    new_links = user.get('links', 0) + 1
    supabase_request(f'users?id=eq.{user_id}', method='PATCH', data={'links': new_links})
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
