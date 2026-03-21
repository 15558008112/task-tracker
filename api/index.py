# Simple Flask API
from flask import Flask, jsonify, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/user')
def get_user():
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
