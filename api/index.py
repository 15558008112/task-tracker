# Vercel API - Twitter OAuth v2
import os
import json
import secrets
from flask import Flask, request, jsonify, redirect, render_template
import urllib.request
import urllib.parse

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Twitter OAuth v2 Config
TWITTER_CLIENT_ID = os.environ.get('TWITTER_CLIENT_ID', 'T05CT3pQT0hOcE1vQlJrVHN0Y3E6MTpjaQ')
TWITTER_CLIENT_SECRET = os.environ.get('TWITTER_CLIENT_SECRET', 'EnzHhIP22RWI8ujFOzFyPneaYQKAH1BwrUGTP8_NbrsTV67Dz8')
CALLBACK_URL = 'https://task-tracker-kohl-one-14.vercel.app/callback'

# Store auth in memory
auth_data = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth/twitter')
def auth_twitter():
    # Generate state
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(32)
    code_challenge = secrets.token_urlsafe(32)
    
    auth_data[state] = {'code_verifier': code_verifier}
    
    # Twitter OAuth v2
    auth_url = f"https://twitter.com/i/oauth2/authorize?response_type=code&client_id={TWITTER_CLIENT_ID}&redirect_uri={CALLBACK_URL}&scope=tweet.read%20users.read&state={state}&code_challenge={code_challenge}&code_challenge_method=plain"
    
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or not state or state not in auth_data:
        return redirect('/?error=auth_failed')
    
    code_verifier = auth_data[state].get('code_verifier')
    
    try:
        # Exchange code for token
        token_url = 'https://api.twitter.com/2/oauth2/token'
        credentials = f"{TWITTER_CLIENT_ID}:{TWITTER_CLIENT_SECRET}"
        import base64
        auth_header = base64.b64encode(credentials.encode()).decode()
        
        data = urllib.parse.urlencode({
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': CALLBACK_URL,
            'client_id': TWITTER_CLIENT_ID,
            'code_verifier': code_verifier
        }).encode()
        
        req = urllib.request.Request(token_url, data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        req.add_header('Authorization', f'Basic {auth_header}')
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            token_result = json.loads(resp.read().decode('utf-8'))
            access_token = token_result.get('access_token')
            
            if access_token:
                # Get user profile using v2 API
                user_req = urllib.request.Request('https://api.twitter.com/2/users/me?user.fields=username,name,profile_image_url')
                user_req.add_header('Authorization', f'Bearer {access_token}')
                
                with urllib.request.urlopen(user_req, timeout=15) as user_resp:
                    profile = json.loads(user_resp.read().decode('utf-8'))
                    
                    if 'data' in profile:
                        data = profile['data']
                        user_info = {
                            'id': data.get('id'),
                            'username': data.get('username'),
                            'name': data.get('name'),
                            'avatar': data.get('profile_image_url', '').replace('_normal', '')
                        }
                        # Redirect with user info
                        return redirect(f'/?twitter_user={user_info["username"]}&twitter_name={user_info["name"]}&twitter_avatar={urllib.parse.quote(user_info["avatar"])}')
    except Exception as e:
        print(f"Auth error: {e}")
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
