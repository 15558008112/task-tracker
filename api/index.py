# Vercel API - Twitter OAuth
import os
import json
from flask import Flask, request, jsonify, redirect, session, render_template

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Twitter OAuth config
TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY', '')
TWITTER_API_SECRET = os.environ.get('TWITTER_API_SECRET', '')
CALLBACK_URL = os.environ.get('CALLBACK_URL', 'https://task-tracker-kohl-one-14.vercel.app/callback')

# Demo data
USERS = [
    {'id': 1, 'username': 'crypto_king', 'name': 'Crypto King', 'avatar': 'https://picsum.photos/100', 'links': 12, 'interactions': 45},
    {'id': 2, 'username': 'defi_girl', 'name': 'DeFi Girl', 'avatar': 'https://picsum.photos/101', 'links': 8, 'interactions': 32},
    {'id': 3, 'username': 'whale_watcher', 'name': 'Whale Watcher', 'avatar': 'https://picsum.photos/102', 'links': 15, 'interactions': 12},
    {'id': 4, 'username': 'nft_collector', 'name': 'NFT Collector', 'avatar': 'https://picsum.photos/103', 'links': 5, 'interactions': 28},
    {'id': 5, 'username': 'memecoin_lad', 'name': 'Memecoin Lad', 'avatar': 'https://picsum.photos/104', 'links': 20, 'interactions': 5},
]

TASKS = [
    {'id': 1, 'userId': 1, 'username': 'crypto_king', 'avatar': 'https://picsum.photos/100', 'link': 'https://x.com/crypto_king/status/123456789', 'liked': True, 'retweeted': False, 'commented': True},
    {'id': 2, 'userId': 2, 'username': 'defi_girl', 'avatar': 'https://picsum.photos/101', 'link': 'https://x.com/defi_girl/status/123456788', 'liked': False, 'retweeted': True, 'commented': False},
    {'id': 3, 'userId': 3, 'username': 'whale_watcher', 'avatar': 'https://picsum.photos/102', 'link': 'https://x.com/whale_watcher/status/123456787', 'liked': True, 'retweeted': True, 'commented': False},
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/user')
def get_user():
    # For demo, return user 1
    return jsonify(USERS[0])

@app.route('/api/users')
def get_users():
    return jsonify(USERS)

@app.route('/api/tasks')
def get_tasks():
    return jsonify(TASKS)

@app.route('/api/interact', methods=['POST'])
def interact():
    data = request.json
    task_id = data.get('taskId')
    action = data.get('action')
    
    for task in TASKS:
        if task['id'] == task_id:
            if action == 'like':
                task['liked'] = not task.get('liked', False)
            elif action == 'retweet':
                task['retweeted'] = not task.get('retweeted', False)
            elif action == 'comment':
                task['commented'] = not task.get('commented', False)
            break
    
    return jsonify({'success': True})

@app.route('/auth/twitter')
def auth_twitter():
    if not TWITTER_API_KEY or not TWITTER_API_SECRET:
        return jsonify({'error': 'Twitter API not configured'}), 500
    
    # Generate OAuth URL
    import secrets
    oauth_token = secrets.token_urlsafe(32)
    session['oauth_token'] = oauth_token
    
    auth_url = f"https://twitter.com/i/oauth2/authorize?response_type=code&client_id={TWITTER_API_KEY}&redirect_uri={CALLBACK_URL}&scope=tweet.read%20users.read&state={oauth_token}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    # In real app, exchange code for access token
    # For demo, just redirect to home with user info
    return redirect('/?logged_in=true')
