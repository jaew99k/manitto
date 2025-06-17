from flask import Flask, render_template, request, redirect
import hashlib
import os
import json
import random
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
        sheet.update_cell(row, 3, name)  # C열 = ManittoEncoded

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
                return redirect(f"/manito/{name}")
        return "로그인 실패: 이름 또는 비밀번호가 잘못되었습니다."
    return render_template("login.html")

# 마니또 확인
@app.route("/manito/<username>")
def manito(username):
    participants = sheet.get_all_records()
    for p in participants:
        if p["Name"] == username:
            return render_template("manito.html", manito=p["ManittoEncoded"])
    return "사용자를 찾을 수 없습니다."

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
