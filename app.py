from flask import Flask, render_template, request, redirect, flash, url_for
import hashlib
import os
import json
import random
import gspread
from google.oauth2.service_account import Credentials
import base64

app = Flask(__name__)
app.secret_key = os.urandom(24)  # flash 메시지용 시크릿 키 설정

# Google Sheets 설정
SHEET_ID = "12FjEPKhsZS0UvGHx9Kdi3HBLtz6iOz7USAq9mhKG6cA"
SHEET_NAME = "participants"

# credentials 환경변수에서 불러오기 + 필수 OAuth scope 명시
creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# SHA-256 해시 함수 (비밀번호 저장용)
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# XOR 간단 암호화/복호화 함수 (마니또 암호화용)
def xor_encrypt_decrypt(text, key='secretkey'):
    key = key.encode()
    text_bytes = text.encode() if isinstance(text, str) else text
    output = bytearray()
    for i in range(len(text_bytes)):
        output.append(text_bytes[i] ^ key[i % len(key)])
    return base64.b64encode(output).decode() if isinstance(text, str) else base64.b64decode(text)

def encrypt_manito(text):
    return xor_encrypt_decrypt(text)

def decrypt_manito(encoded_text):
    decoded = xor_encrypt_decrypt(base64.b64decode(encoded_text).decode())
    return decoded

# 마니또 배정 함수 (암호화 포함)
def assign_manittos():
    names = sheet.col_values(1)[1:]  # A열: 이름, 첫 행 제외
    shuffled = names[:]
    while True:
        random.shuffle(shuffled)
        if all(a != b for a, b in zip(names, shuffled)):
            break
    for i, manito_name in enumerate(shuffled):
        row = i + 2
        encrypted_manito = encrypt_manito(manito_name)
        sheet.update_cell(row, 3, encrypted_manito)  # C열 = 암호화된 ManittoEncoded

# 기본 루트 → /register로 리다이렉트
@app.route("/")
def index():
    return redirect("/register")

# 참가자 등록
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]
        hashed_pw = hash_password(password)

        participants = sheet.get_all_records()

        if any(p["Name"] == name for p in participants):
            flash("이미 등록된 이름입니다. 로그인 화면으로 이동합니다.")
            return redirect(url_for("login"))

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
                decrypted_manito = decrypt_manito(p["ManittoEncoded"])
                return render_template("manito.html", manito=decrypted_manito)
        return "로그인 실패: 이름 또는 비밀번호가 잘못되었습니다."
    return render_template("login.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
