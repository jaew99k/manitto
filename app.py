from flask import Flask, render_template, request, redirect, flash, url_for
import hashlib
import os
import json
import random
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key')

# Google Sheets 설정
SHEET_ID = "12FjEPKhsZS0UvGHx9Kdi3HBLtz6iOz7USAq9mhKG6cA"
SHEET_NAME = "participants"

# 환경변수에서 구글 인증 정보 불러오기 및 권한 설정
creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# SHA-256 해시 함수
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# 간단한 시저 암호 방식으로 마니또 암호화/복호화
def encrypt_manito(name):
    return ''.join(chr((ord(c) + 3) % 256) for c in name)

def decrypt_manito(enc_name):
    return ''.join(chr((ord(c) - 3) % 256) for c in enc_name)

# 마니또 배정 함수
def assign_manittos():
    names = sheet.col_values(1)[1:]  # A열 (이름), 첫 행 제외
    shuffled = names[:]
    while True:
        random.shuffle(shuffled)
        if all(a != b for a, b in zip(names, shuffled)):
            break
    for i, name in enumerate(shuffled):
        row = i + 2
        encrypted = encrypt_manito(name)
        sheet.update_cell(row, 3, encrypted)  # C열에 암호화된 마니또 저장

# 루트 접속 시 /register로 리다이렉트
@app.route("/")
def index():
    return redirect(url_for('register'))

# 참가자 등록
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "").strip()

        if not name or not password:
            flash("이름과 비밀번호를 모두 입력하세요.")
            return redirect(url_for('register'))

        hashed_pw = hash_password(password)
        participants = sheet.get_all_records()

        if any(p["Name"] == name for p in participants):
            flash("이미 등록된 이름입니다. 로그인 화면으로 이동합니다.")
            return redirect(url_for('login'))

        if len(participants) >= 9:
            return "참가자는 9명까지만 등록할 수 있습니다."

        sheet.append_row([name, hashed_pw, ""])

        if len(participants) + 1 == 9:
            assign_manittos()

        flash("등록이 완료되었습니다. 로그인해 주세요.")
        return redirect(url_for('login'))

    return render_template("register.html")

# 로그인
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "").strip()
        hashed_pw = hash_password(password)

        participants = sheet.get_all_records()

        for p in participants:
            if p["Name"] == name and p["PasswordHash"] == hashed_pw:
                manito_enc = p.get("ManittoEncoded", "")
                if not manito_enc:
                    flash("아직 마니또 매칭이 완료되지 않았습니다.")
                    return redirect(url_for('login'))
                manito_dec = decrypt_manito(manito_enc)
                return render_template("manito.html", manito=manito_dec)

        flash("로그인 실패: 이름 또는 비밀번호가 잘못되었습니다.")
        return redirect(url_for('login'))

    return render_template("login.html")

# 마니또 확인 (직접 URL 접속 시)
@app.route("/manito/<username>")
def manito(username):
    participants = sheet.get_all_records()
    for p in participants:
        if p["Name"] == username:
            manito_enc = p.get("ManittoEncoded", "")
            if not manito_enc:
                return "아직 마니또 매칭이 완료되지 않았습니다."
            manito_dec = decrypt_manito(manito_enc)
            return render_template("manito.html", manito=manito_dec)
    return "사용자를 찾을 수 없습니다."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
