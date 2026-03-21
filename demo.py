#!/usr/bin/env python3
"""
24hclub Task Tracker - Demo Version
"""

from flask import Flask, render_template, request, redirect, session, jsonify
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo-secret-key'

# Demo data
DEMO_USERS = [
    {'id': 1, 'username': 'crypto_king', 'name': 'Crypto King', 'avatar_url': 'https://picsum.photos/100', 'links_submitted': 12, 'interactions_done': 45},
    {'id': 2, 'username': 'defi_girl', 'name': 'DeFi Girl', 'avatar_url': 'https://picsum.photos/101', 'links_submitted': 8, 'interactions_done': 32},
    {'id': 3, 'username': 'whale_watcher', 'name': 'Whale Watcher', 'avatar_url': 'https://picsum.photos/102', 'links_submitted': 15, 'interactions_done': 12},
    {'id': 4, 'username': 'nft_collector', 'name': 'NFT Collector', 'avatar_url': 'https://picsum.photos/103', 'links_submitted': 5, 'interactions_done': 28},
    {'id': 5, 'username': 'memecoin_lad', 'name': 'Memecoin Lad', 'avatar_url': 'https://picsum.photos/104', 'links_submitted': 20, 'interactions_done': 5},
]

DEMO_TASKS = [
    {'id': 1, 'username': 'crypto_king', 'avatar_url': 'https://picsum.photos/100', 'link': 'https://x.com/crypto_king/status/123456789', 'liked': True, 'retweeted': False, 'commented': True},
    {'id': 2, 'username': 'defi_girl', 'avatar_url': 'https://picsum.photos/101', 'link': 'https://x.com/defi_girl/status/123456788', 'liked': False, 'retweeted': True, 'commented': False},
    {'id': 3, 'username': 'whale_watcher', 'avatar_url': 'https://picsum.photos/102', 'link': 'https://x.com/whale_watcher/status/123456787', 'liked': True, 'retweeted': True, 'commented': False},
]

@app.route('/')
def index():
    # Mock logged in user
    current_user = DEMO_USERS[0]
    pending_needed = 0  # User has done enough interactions
    
    return render_template('index.html', 
                         tasks=DEMO_TASKS,
                         leaderboard=DEMO_USERS,
                         pending_needed=pending_needed,
                         current_user=current_user)

@app.route('/login')
def login():
    return redirect('/')

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html', users=DEMO_USERS)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
