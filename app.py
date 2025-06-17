from flask import Flask, render_template, request, redirect, url_for, Response
import hashlib
import os
import json
import random
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

SHEET_ID = "12FjEPKhsZS0UvGHx9Kdi3HBLtz6iOz7USAq9mhKG6cA"
SHEET_NAME = "participants"

creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# 암호화 함수 (간단한 시저 암호)
def encrypt_manito(name):
    return ''.join(chr((ord(c) + 3) % 256) for c in name)

# 복호화 함수
def decrypt_manito(enc_name):
    return ''.join(chr((ord(c) - 3) % 256) for c in enc_name)

def assign_manittos():
    names = sheet.col_values(1)[1:]
    shuffled = names[:]
    while True:
        random.shuffle(shuffled)
        if all(a != b for a, b in zip(names, shuffled)):
            break
    for i, name in enumerate(shuffled):
        row = i + 2
        encrypted_name = encrypt_manito(name)
        sheet.update_cell(row, 3, encrypted_name)

@app.route("/")
def index():
    return redirect(url_for('register'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]
        hashed_pw = hash_password(password)

        participants = sheet.get_all_records()

        if any(p["Name"] == name for p in participants):
            html = f"""
            <!DOCTYPE html>
            <html lang="ko">
            <head>
                <meta charset="UTF-8" />
                <title>알림</title>
                <meta http-equiv="refresh" content="3; url={url_for('login')}">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        text-align: center;
                        padding-top: 100px;
                        font-size: 18px;
                    }}
                </style>
            </head>
            <body>
                <p>이미 존재하는 이름입니다.<br>로그인 화면으로 이동합니다.</p>
                <p>3초 후에 자동으로 이동합니다.</p>
                <p>이동하지 않으면 <a href="{url_for('login')}">여기를 클릭</a>하세요.</p>
            </body>
            </html>
            """
            return Response(html, mimetype='text/html')

        if len(participants) >= 9:
            return "참가자는 9명까지만 등록할 수 있습니다."

        sheet.append_row([name, hashed_pw, ""])

        if len(participants) + 1 == 9:
            assign_manittos()

        return redirect(url_for('login'))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]
        hashed_pw = hash_password(password)

        participants = sheet.get_all_records()
        for p in participants:
            if p["Name"] == name and p["PasswordHash"] == hashed_pw:
                if not p.get("ManittoEncoded", ""):
                    return "아직 마니또 매칭이 완료되지 않았습니다."
                return redirect(url_for('manito', username=name))
        return "로그인 실패: 이름 또는 비밀번호가 잘못되었습니다."
    return render_template("login.html")

@app.route("/manito/<username>")
def manito(username):
    participants = sheet.get_all_records()
    for p in participants:
        if p["Name"] == username:
            encrypted_manito = p.get("ManittoEncoded", "")
            if not encrypted_manito:
                return "아직 마니또 매칭이 완료되지 않았습니다."
            decrypted_manito = decrypt_manito(encrypted_manito)
            return render_template("manito.html", manito=decrypted_manito)
    return "사용자를 찾을 수 없습니다."

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
