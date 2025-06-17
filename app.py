from flask import Flask, render_template, request, redirect
import hashlib
import os
import json
import random
import base64
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Google Sheets 설정
SHEET_ID = "12FjEPKhsZS0UvGHx9Kdi3HBLtz6iOz7USAq9mhKG6cA"
SHEET_NAME = "participants"

# credentials 환경변수에서 불러오기 + 필수 OAuth scope 명시
creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# SHA-256 해시 함수
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# Base64 인코딩 함수
def encode_manitto(name):
    encoded_bytes = base64.b64encode(name.encode('utf-8'))
    return encoded_bytes.decode('utf-8')

# Base64 디코딩 함수
def decode_manitto(encoded_str):
    decoded_bytes = base64.b64decode(encoded_str.encode('utf-8'))
    return decoded_bytes.decode('utf-8')

# 마니또 배정 함수
def assign_manittos():
    names = sheet.col_values(1)[1:]  # A열: 이름, 첫 행 제외
    shuffled = names[:]
    while True:
        random.shuffle(shuffled)
        if all(a != b for a, b in zip(names, shuffled)):
            break
    for i, name in enumerate(shuffled):
        row = i + 2
        encoded_name = encode_manitto(name)  # 인코딩 후 저장
        sheet.update_cell(row, 3, encoded_name)  # C열 = ManittoEncoded

# 참가자 등록
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]
        hashed_pw = hash_password(password)

        participants = sheet.get_all_records()

        if any(p["Name"] == name for p in participants):
            return "이미 등록된 이름입니다."

        if len(participants) >= 9:
            return "참가자는 9명까지만 등록할 수 있습니다."

        sheet.append_row([name, hashed_pw, ""])

        if len(participants) + 1 == 9:
            assign_manittos()

        return redirect("/login")
    return render_template("register.html")

# 로그인
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]
        hashed_pw = hash_password(password)

        participants = sheet.get_all_records()
        for p in participants:
            if p["Name"] == name and p["PasswordHash"] == hashed_pw:
                if not p["ManittoEncoded"]:
                    return "아직 마니또 매칭이 완료되지 않았습니다."
                manitto_name = decode_manitto(p["ManittoEncoded"])  # 디코딩
                return render_template("manito.html", manito=manitto_name)
        return "로그인 실패: 이름 또는 비밀번호가 잘못되었습니다."
    return render_template("login.html")

# 마니또 확인 (직접 URL 접속용)
@app.route("/manito/<username>")
def manito(username):
    participants = sheet.get_all_records()
    for p in participants:
        if p["Name"] == username:
            if not p["ManittoEncoded"]:
                return "아직 마니또 매칭이 완료되지 않았습니다."
            manitto_name = decode_manitto(p["ManittoEncoded"])
            return render_template("manito.html", manito=manitto_name)
    return "사용자를 찾을 수 없습니다."

# 기본 URL -> /register 로 리다이렉트
@app.route("/")
def index():
    return redirect("/register")

if __name__ == "__main__":
    app.run(debug=True)
