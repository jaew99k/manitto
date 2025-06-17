@app.route('/register', methods=['GET', 'POST'])
def register():
    participants = load_participants()

    if request.method == 'POST':
        name = request.form['name']
        pw = request.form['password']

        if any(p['name'] == name for p in participants):
            return "이미 등록된 이름입니다."

        # ✅ 9명까지만 등록 허용 (0~8번째까지 append 허용)
        if len(participants) >= 9:
            return "참가자가 모두 등록되어 더 이상 등록할 수 없습니다."

        # 등록
        participants.append({"name": name, "password": pw, "manito": None})

        # ✅ 등록 후 9명이 되면 추첨 실행
        if len(participants) == 9:
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
