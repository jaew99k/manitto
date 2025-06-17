from flask import Flask, request, render_template, redirect, url_for
import json, os, random

app = Flask(__name__)

DATA_FILE = 'participants.json'

def load_participants():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_participants(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register():
    participants = load_participants()
    if request.method == 'POST':
        name = request.form['name']
        pw = request.form['password']
        if any(p['name'] == name for p in participants):
            return "이미 등록된 이름입니다."
        participants.append({"name": name, "password": pw, "manito": None})
        if len(participants) == 10:
            names = [p['name'] for p in participants]
            shuffled = names[:]
            while True:
                random.shuffle(shuffled)
                if all(a != b for a, b in zip(names, shuffled)):
                    break
            for i, p in enumerate(participants):
                p['manito'] = shuffled[i]
        save_participants(participants)
        return redirect('/login')
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    participants = load_participants()
    if request.method == 'POST':
        name = request.form['name']
        pw = request.form['password']
        user = next((p for p in participants if p['name'] == name and p['password'] == pw), None)
        if not user:
            return "로그인 실패. 이름/비밀번호 확인하세요."
        if not user['manito']:
            return "아직 마니또 매칭이 완료되지 않았습니다."
        return render_template("manito.html", manito=user['manito'])
    return render_template("login.html")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
