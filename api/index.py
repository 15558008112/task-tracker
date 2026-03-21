# Vercel API
import os
import json
import secrets
from flask import Flask, request, jsonify, redirect, render_template

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Config
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://vejicltqodkdjchqlrqx.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlamljbHRxb2RrZGpjaHFscnF4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQwOTcxMDgsImV4cCI6MjA4OTY3MzEwOH0.uNeQttyjwZTjVhicd0oftdgWIkvdqFrtXLaCe9mjrJE')

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
        import urllib.request
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    return jsonify({'logged_in': False})

@app.route('/api/login')
def login():
    twitterAuthUrl = 'https://twitter.com/i/oauth2/authorize?response_type=code&client_id=T05CT3pQT0hOcE1vQlJrVHN0Y3E6MTpjaQ&redirect_uri=https://task-tracker-kohl-one-14.vercel.app/callback&scope=tweet.read%20users.read&state=xyz&code_challenge=challenge&code_challenge_method=plain'
    return redirect(twitterAuthUrl)

@app.route('/callback')
def callback():
    return redirect('/?logged_in=true')

@app.route('/api/logout', methods=['POST'])
def logout():
    return jsonify({'success': True})

@app.route('/api/user')
def get_user():
    return jsonify({'username': 'guest', 'avatar': 'https://api.dicebear.com/7.x/avataaars/svg?seed=guest', 'links': 0, 'interactions': 0})

@app.route('/api/users')
def get_users():
    result = supabase_request('users?order=interactions.desc&limit=20')
    return jsonify(result if result else [])

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
    return jsonify({'success': True})

@app.route('/api/submit', methods=['POST'])
def submit():
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
