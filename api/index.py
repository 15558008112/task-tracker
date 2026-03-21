# Vercel API
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

# Twitter OAuth
TWITTER_CLIENT_ID = 'T05CT3pQT0hOcE1vQlJrVHN0Y3E6MTpjaQ'
TWITTER_CLIENT_SECRET = 'EnzHhIP22RWI8ujFOzFyPneaYQKAH1BwrUGTP8_NbrsTV67Dz8'
CALLBACK_URL = 'https://task-tracker-kohl-one-14.vercel.app/callback'

# In-memory store
users_db = {}

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

def get_session_user():
    user_id = request.cookies.get('user_id')
    if user_id and user_id in users_db:
        return users_db[user_id]
    return None

@app.route('/')
def index():
    return render_template('index.html', logged_in=False)

@app.route('/api/status')
def get_status():
    user = get_session_user()
    if user:
        return jsonify({'logged_in': True, 'user': user})
    return jsonify({'logged_in': False})

@app.route('/api/login')
def login():
    state = secrets.token_urlsafe(16)
    auth_url = f"https://twitter.com/i/oauth2/authorize?response_type=code&client_id={TWITTER_CLIENT_ID}&redirect_uri={CALLBACK_URL}&scope=tweet.read%20users.read&state={state}&code_challenge=challenge&code_challenge_method=plain"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    from flask import make_response
    
    if code:
        try:
            # Exchange code for token
            import urllib.request
            import urllib.parse
            import base64
            
            token_url = 'https://api.twitter.com/2/oauth2/token'
            data = urllib.parse.urlencode({
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': CALLBACK_URL,
                'client_id': TWITTER_CLIENT_ID,
                'code_verifier': 'challenge'
            }).encode('utf-8')
            
            req = urllib.request.Request(token_url, data=data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            credentials = base64.b64encode(f"{TWITTER_CLIENT_ID}:{TWITTER_CLIENT_SECRET}".encode()).decode()
            req.add_header('Authorization', f'Basic {credentials}')
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                token_data = json.loads(resp.read().decode('utf-8'))
                access_token = token_data.get('access_token')
                
                if access_token:
                    # Get user info
                    user_req = urllib.request.Request('https://api.twitter.com/2/users/me?user.fields=username,name,profile_image_url',
                        headers={'Authorization': f'Bearer {access_token}'})
                    with urllib.request.urlopen(user_req, timeout=10) as user_resp:
                        twitter_user = json.loads(user_resp.read().decode('utf-8'))
                        
                        if 'data' in twitter_user:
                            t_user = twitter_user['data']
                            username = t_user.get('username', 'user')
                            avatar = t_user.get('profile_image_url', '').replace('_normal', '')
                            
                            response = make_response(redirect(f'/?logged_in=true&username={username}&avatar={avatar}'))
                            response.set_cookie('twitter_auth', 'true', max_age=60*60*24*30)
                            return response
        except Exception as e:
            print(f"OAuth error: {e}")
    
    response = make_response(redirect('/'))
    response.set_cookie('twitter_auth', 'true', max_age=60*60*24*30)
    return response

@app.route('/api/logout', methods=['POST'])
def logout():
    response = jsonify({'success': True})
    response.set_cookie('user_id', '', max_age=0)
    return response

@app.route('/api/user')
def get_user():
    user = get_session_user()
    if user:
        return jsonify(user)
    return jsonify({'username': 'guest', 'avatar': 'https://api.dicebear.com/7.x/avataaars/svg?seed=guest', 'links': 0, 'interactions': 0})

@app.route('/api/users')
def get_users():
    users = list(users_db.values())
    users.sort(key=lambda x: x.get('interactions', 0), reverse=True)
    return jsonify(users[:20])

@app.route('/api/tasks')
def get_tasks():
    result = supabase_request('tasks?order=id.desc&limit=50')
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
    user = get_session_user()
    if user:
        user['interactions'] = user.get('interactions', 0) + 1
    return jsonify({'success': True})

@app.route('/api/submit', methods=['POST'])
def submit():
    user = get_session_user()
    if not user:
        return jsonify({'success': False, 'error': '请先登录'}), 400
    
    user['links'] = user.get('links', 0) + 1
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
