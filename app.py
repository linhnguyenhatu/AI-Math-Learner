from flask import Flask, jsonify, render_template, request, redirect, session, url_for, flash
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
import os
import time
import torch
import numpy as np
from train import training, transform
from sklearn.preprocessing import StandardScaler

sc = StandardScaler()
model = training()
app = Flask(__name__)
app.secret_key = 'app_secret_key'

result = []
all_result = []
user_id = 0

@app.route("/", methods=["GET", "POST"])
def index():
    if 'user' in session:
        return redirect(url_for('account')) 
    return render_template("index.html")

# Đăng nhập và đăng ký
def save_user_to_excel(name, email, phone, studytype, password):

    df = pd.read_excel('datasets/users.xlsx')
    hashed_password = generate_password_hash(password)
    user_id = 0
    if (len(df.iloc[:, 0]) != 0):
        user_id = df.iloc[len(df.iloc[:, 0]) - 1, 0] + 1
    else:
        user_id = 0
    user_input = [user_id, name, email, phone, studytype, hashed_password]
    new_user = pd.DataFrame([user_input], columns=['id', 'name', 'email', 'phone', 'studytype', 'password'])
    df = pd.concat([df, new_user], ignore_index=True)
    
    df.to_excel('datasets/users.xlsx', index=False)


def verify_user(email, password):
    if os.path.exists('datasets/users.xlsx'):
        df = pd.read_excel('datasets/users.xlsx')
        user = df[df['email'] == email]
        if not user.empty:
            stored_password = user.iloc[0]['password']
            return check_password_hash(stored_password, password)
    return False


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        rname = request.form['rname']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        studytype = request.form['studytype']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Mật khẩu không khớp. Vui lòng thử lại.')
            return render_template('register.html', rname=rname, name=name, email=email, phone=phone)

        save_user_to_excel(name, email, phone, studytype, password)
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if verify_user(email, password):
            session['user'] = email
            return redirect(url_for('account'))
        else:
            flash('Email hoặc mật khẩu không đúng. Vui lòng thử lại.')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'user' not in session:  # Kiểm tra nếu người dùng chưa đăng nhập
        flash('Bạn phải đăng nhập để truy cập trang này.')
        return redirect(url_for('login'))

    # Lấy email của người dùng từ session
    user_email = session['user']
    if request.method == "POST":
        if request.form.get('ChooseTopic') == 'activated1':
            return redirect(url_for('reading'))
    return render_template('account.html', user_email=user_email)

# Route đăng xuất
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Bạn đã đăng xuất.')
    return redirect(url_for('login'))


def load_questions_from_excel(file_path):
    df = pd.read_excel(file_path)
    questions = {}

    for _, row in df.iterrows():
        question = {
            "question": row["Question"],
            "options": [row["Option 1"], row["Option 2"], row["Option 3"], row["Option 4"]],
            "correct_answer": row["Correct Answer"]
        }
        questions[row["Index"]] = question
    
    return questions

questions = load_questions_from_excel("datasets/quiz.xlsx")
etime = 0
@app.route('/reading', methods=["GET", 'POST'])
def reading():
    start_time = time.time()
    result.append(start_time)
    if request.form.get('button_action') == 'activated':
        end_time = time.time()
        etime = end_time - result[0]
        all_result.append(etime)
        result.clear()
        return redirect(url_for('quiz'))
            
    return render_template("reading.html")
answer = []
@app.route('/quiz', methods=["GET", "POST"])
def quiz():
    start_time = time.time()
    result.append(start_time)
    if request.form.get('button_action') == 'activated':
        end_time = time.time()
        etime = end_time - result[0]
        all_result.append(etime)
        result.clear()
        for question_id, question in questions.items():
            answer.append(request.form.get(f"question_{question_id+1}"))
        return redirect(url_for('final'))
    return render_template("quiz.html", questions=questions, result = result)


@app.route('/final', methods=["POST", "GET"])
def final():
    score = 0
    total_questions = len(questions)
    count = 0
    for question_id, question in questions.items():
        user_answer = answer[count]
        print(user_answer)
        correct_answer = question['correct_answer']
        user_answer = str(user_answer).strip().lower() if user_answer else ""
        correct_answer = str(correct_answer).strip().lower()
        count += 1
        if user_answer == correct_answer:
            score += 1
    answer.clear()
    save_per_to_excel(all_result, 2, score)
    all_result.clear()
    
    personalize(user_id)
    print(weak)
    weak.clear()
    return render_template('results.html', score=score, total_questions=total_questions)

def save_per_to_excel(list, difficulty, num):

    df = pd.read_excel('datasets/ScoreDatabase.xlsx')
    studytime = list[0]
    examtime = list[1]
    user_input = [user_id, difficulty, num, studytime, examtime]
    user_performance = pd.DataFrame([user_input], columns=['id', 'difficulty', 'score', 'studytime', 'examtime'])
    df = pd.concat([df, user_performance], ignore_index=True)
    df.to_excel('datasets/ScoreDatabase.xlsx', index=False)    


weak = []
def personalize(id):
    df = pd.read_excel('datasets/ScoreDatabase.xlsx')
    for i in range (0 ,len(df.iloc[:, 0])):
        if (df.loc[i][0] == id):
            x = df.loc[i][1:]
            y_pred = model(torch.from_numpy(transform(x.to_numpy().reshape(1, -1)).astype(np.float32)))
            weak.append(round(y_pred.item()))

            
    
if __name__ == "__main__":
    app.run(debug=True)
