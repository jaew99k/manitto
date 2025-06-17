from flask import Flask, render_template, request, redirect
import hashlib
import os
import json
import random
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# 구글 시트 설정
SHEET_ID = "12FjEPKhsZS0UvGHx9Kdi3HBLtz6iOz7USAq9mhKG6cA"
SHEET_NAME = "participants"

# 환경 변수에서 credentials.json 불러오기
creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_info)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# SHA-256 해시 함수
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# 참가자 등록
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]
        hashed_pw = hash_password(password)

        participants = sheet.get_all_records()

        # 이미 등록된 사람인지 확인
        if any(p["name"] == name for p in participants):
            return "이미 등록된 이름입니다."

        # 9명 이상이면 등록 제한
        if len(participants) >= 9:
            return "참가자는 9명까지만 등록할 수 있습니다."

        # 시트에 정보 추가
        sheet.append_row([name, hashed_pw, ""])  # 마지막 열은 manito 결과용

        # 9명이 다 등록됐으면 마니또 배정
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
            if p["name"] == name and p["password"] == hashed_pw:
                return redirect(f"/manito/{name}")
        return "로그인 실패: 이름 또는 비밀번호가 잘못되었습니다."
    return render_template("login.html")

# 마니또 결과 보기
@app.route("/manito/<username>")
def manito(username):
    participants = sheet.get_all_records()
    for p in participants:
        if p["name"] == username:
            return render_template("manito.html", manito=p["manito"])
    return "사용자를 찾을 수 없습니다."

# 마니또 랜덤 배정 함수
def assign_manittos():
    participants = sheet.col_values(1)[1:]  # 첫 번째 열 (name), 첫 행 제외
    shuffled = participants[:]
    while True:
        random.shuffle(shuffled)
        if all(a != b for a, b in zip(participants, shuffled)):
            break
    for i, name in enumerate(participants):
        row = i + 2  # 시트에서 2행부터 시작
        sheet.update_cell(row, 3, shuffled[i])  # 3번째 열에 마니또 이름 기록

if __name__ == "__main__":
    app.run(debug=True)
