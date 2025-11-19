# A project made with love for my girlfriend Larita
# - Create your own quiz: questions with 4 possible answers (one of them correct)
# - Save your questions to test yourself whenever you want
# - (WIP) Tag your questions and make an exam with the tags you choose
# - See your results after an exam
# - (extra) View your past results
# - (extra) add a timer

from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
import random
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'questions.db')

app = Flask(__name__)
app.config['DATABASE'] = DB_PATH



# --- Database helpers ---

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            a TEXT NOT NULL,
            b TEXT NOT NULL,
            c TEXT NOT NULL,
            d TEXT NOT NULL,
            correct TEXT NOT NULL,
            tags TEXT,
            created_at TEXT NOT NULL
        )
        ''')
    conn.commit()
    conn.close()

# Initialize DB on first run
if not os.path.exists(app.config['DATABASE']):
    init_db()

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

# Add question
@app.route('/templates/add_question.html', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        q = request.form.get('question', '').strip()
        a = request.form.get('a', '').strip()
        b = request.form.get('b', '').strip()
        c = request.form.get('c', '').strip()
        d = request.form.get('d', '').strip()
        correct = request.form.get('correct', '').strip()
        tags = request.form.get('tags', '').strip()
        if q and a and b and c and d and correct in ('a','b','c','d'):
            conn = get_db()
            conn.execute('''INSERT INTO questions (question,a,b,c,d,correct,tags,created_at)
            VALUES (?,?,?,?,?,?,?,?)''',
            (q,a,b,c,d,correct,tags, datetime.utcnow().isoformat()))
            conn.commit()
            return redirect(url_for('list_questions'))
        else:
            return render_template('add_question.html', error='Rellena todos los campos y selecciona la respuesta correcta.')
    return render_template('add_question.html')

# List questions
@app.route('/templates/list_questions.html')
def list_questions():
    conn = get_db()
    tag = request.args.get('tag', None)
    if tag:
        cur = conn.execute('SELECT * FROM questions WHERE tags LIKE ? ORDER BY id DESC', (f'%{tag}%',))
    else:
        cur = conn.execute('SELECT * FROM questions ORDER BY id DESC')
    qs = cur.fetchall()
    # fetch distinct tags
    cur_tags = conn.execute("SELECT DISTINCT tags FROM questions WHERE tags IS NOT NULL AND tags!=''")
    all_tags = cur_tags.fetchall()
    return render_template('list_questions.html', questions=qs, tags=all_tags, selected_tag=tag)

# Delete question
@app.route('/delete/<int:qid>', methods=['POST'])
def delete_question(qid):
    conn = get_db()
    conn.execute('DELETE FROM questions WHERE id = ?', (qid,))
    conn.commit()
    return redirect(url_for('list_questions'))



# Start an exam (choose number of questions)
@app.route('/templates/exam.html', methods=['GET', 'POST'])
def exam():
    conn = get_db()
    cur = conn.execute('SELECT COUNT(*) as cnt FROM questions')
    total = cur.fetchone()['cnt']
    if request.method == 'POST':
        try:
            n = int(request.form.get('n', '5'))
        except ValueError:
            n = 5
        cur = conn.execute('SELECT * FROM questions')
        all_q = cur.fetchall()
        if n > len(all_q):
            n = len(all_q)
        selected = random.sample(all_q, n) if n>0 else []
        # We store question ids and shuffle answers in template
        return render_template('exam.html', questions=selected)
    return render_template('exam.html', total=total)

# Submit exam
@app.route('/submit', methods=['POST'])
def submit():
    answers = {}
    for key, val in request.form.items():
        if key.startswith('q_'):
            qid = key.split('_',1)[1]
            answers[qid] = val
    # Fetch correct answers
    conn = get_db()
    placeholders = ','.join('?' for _ in answers.keys())
    if answers:
        cur = conn.execute(f'SELECT id, question, a, b, c, d, correct FROM questions WHERE id IN ({placeholders})', tuple(answers.keys()))
    else:
        cur = []
    results = []
    correct_count = 0
    for row in cur:
        qid = str(row['id'])
        selected = answers.get(qid, None)
        is_correct = (selected == row['correct'])
        if is_correct:
            correct_count += 1
        results.append({
            'id': qid,
            'question': row['question'],
            'selected': selected,
            'correct': row['correct'],
            'choices': {'a': row['a'], 'b': row['b'], 'c': row['c'], 'd': row['d']}
        })
    score = correct_count
    total = len(results)
    return render_template('result.html', results=results, score=score, total=total)


if __name__ == '__main__':
    # Change host to '0.0.0.0' if we want to access in the tablet (on the same network)
    app.run(debug=True, host='127.0.0.1', port=5000)


# -- to test flask works --
#@app.route("/")
#def home():
#    return "this project is working!"
#app.run(debug=True)

