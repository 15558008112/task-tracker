#!/usr/bin/env python3
"""
24hclub Task Check-in System
Twitter OAuth Login + Task Management
"""

from flask import Flask, render_template, request, redirect, session, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from twitter import Twitter, OAuth
import os
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Twitter OAuth Config
TWITTER_CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY', '')
TWITTER_CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET', '')

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    twitter_id = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(100))
    name = db.Column(db.String(100))
    avatar_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Stats
    links_submitted = db.Column(db.Integer, default=0)
    interactions_done = db.Column(db.Integer, default=0)
    
    # Task tracking
    pending_tasks = db.relationship('Task', foreign_keys='Task.owner_id', backref='owner', lazy=True)
    completed_interactions = db.relationship('Interaction', foreign_keys='Interaction.helper_id', backref='helper', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    twitter_link = db.Column(db.String(500))
    twitter_text = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Interaction tracking
    liked = db.Column(db.Boolean, default=False)
    retweeted = db.Column(db.Boolean, default=False)
    commented = db.Column(db.Boolean, default=False)
    completed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    completed_at = db.Column(db.DateTime)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('login.html')
    
    # Get today's stats
    today = datetime.utcnow().date()
    today_tasks = Task.query.filter(
        db.func.date(Task.created_at) == today
    ).order_by(Task.created_at.desc()).all()
    
    # Get leaderboard
    leaderboard = User.query.order_by(
        User.interactions_done.desc()
    ).limit(20).all()
    
    # Calculate pending interactions needed
    pending_needed = max(0, 5 - current_user.interactions_done)
    
    return render_template('index.html', 
                         tasks=today_tasks,
                         leaderboard=leaderboard,
                         pending_needed=pending_needed)

@app.route('/login')
def login():
    # Twitter OAuth redirect
    twitter = Twitter(auth=OAuth(
        '', '', TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET
    ))
    auth_url = twitter.auth.urlize_auth_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    oauth_token = request.args.get('oauth_token')
    oauth_verifier = request.args.get('oauth_verifier')
    
    twitter = Twitter(auth=OAuth(
        '', '', TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET
    ))
    credentials = twitter.auth.get_access_token(oauth_verifier)
    
    # Get user info
    twitter = Twitter(auth=OAuth(
        credentials.oauth_token,
        credentials.oauth_token_secret,
        TWITTER_CONSUMER_KEY,
        TWITTER_CONSUMER_SECRET
    ))
    user_info = twitter.account.verify_credentials()
    
    # Create or update user
    user = User.query.filter_by(twitter_id=str(user_info.id)).first()
    if not user:
        user = User(
            twitter_id=str(user_info.id),
            username=user_info.screen_name,
            name=user_info.name,
            avatar_url=user_info.profile_image_url
        )
        db.session.add(user)
    else:
        user.username = user_info.screen_name
        user.name = user_info.name
        user.avatar_url = user_info.profile_image_url
    
    db.session.commit()
    login_user(user)
    
    return redirect('/')

@app.route('/submit', methods=['POST'])
@login_required
def submit_task():
    # Check if user has enough interactions
    if current_user.interactions_done < 5:
        return jsonify({'error': '需要先完成5次互动才能提交链接'}), 400
    
    link = request.form.get('link')
    if not link or 'twitter.com' not in link and 'x.com' not in link:
        return jsonify({'error': '请输入有效的Twitter链接'}), 400
    
    task = Task(
        owner_id=current_user.id,
        twitter_link=link
    )
    current_user.links_submitted += 1
    db.session.add(task)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/interact/<int:task_id>/<action>')
@login_required
def interact(task_id, action):
    task = Task.query.get_or_404(task_id)
    
    # Can't interact with own task
    if task.owner_id == current_user.id:
        return jsonify({'error': '不能为自己的任务互动'}), 400
    
    # Record interaction
    if action == 'like':
        task.liked = True
    elif action == 'retweet':
        task.retweeted = True
    elif action == 'comment':
        task.commented = True
    
    task.completed_by_id = current_user.id
    task.completed_at = datetime.utcnow()
    
    current_user.interactions_done += 1
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/leaderboard')
def leaderboard():
    users = User.query.order_by(
        User.interactions_done.desc()
    ).all()
    return render_template('leaderboard.html', users=users)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
