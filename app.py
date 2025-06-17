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

        # ✅ 참가자 수가 9명을 초과하면 등록 차단
        if len(participants) >= 9:
            return "참가자가 모두 등록되어 더 이상 등록할 수 없습니다."

        # ✅ 등록 허용
        participants.append({"na
