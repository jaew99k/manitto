from flask import Flask, request, render_template, redirect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import hashlib
import base64
import os
import json

app = Flask(__name__)

# Google Sheets 연결 설정
def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not credentials_json:
        raise Exception("환경변수 GOOGLE_CREDENTIALS_JSON이 설정되지 않았습니다.")
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(credentials_json), scope)
    client = gspread.authorize(creds)
    sheet = client.open("ManittoParticipants").sheet1
    return sheet

# 비밀번호 해시 함수
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 마니또 이름 인코딩 (Base64)
def encode_manito(name):
    return base64.b64encode(name.encode()).decode()

# 마니또 이름 디코딩
def decode_manito(encoded_name):
    return base64.b64decode(encoded_name.encode()).decode()

@app.route('/')
def index():
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register():
    sheet = get_sheet()
    records = sheet.get_all_records()
    if request.method == 'POST':
        name = request.form['name']
        pw = request.form['password']

        if any(r['Name'] == name for r in records):
            return "이미 등록된 이름입니다."

        if len(records) >= 9:
            return "참가자가 모두 등록되어 더 이상 등록할 수 없습니다."

        pw_hash = hash_password(pw)
        sheet.append_row([name, pw_hash, ""])  # 마니또는 아직 없음

        records = sheet.get_all_records()
        if len(records) == 9:
            names = [r['Name'] for r in records]
            shuffled = names[:]
            import random
            while True:
                random.shuffle(shuffled)
                if all(a != b for a, b in zip(names, shuffled)):
                    break
            for i, name in enumerate(names):
                encoded = encode_manito(shuffled[i])
                sheet.u
