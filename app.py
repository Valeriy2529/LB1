from flask import Flask, render_template, request, redirect, url_for, session
import telebot
from telebot.types import Message
from matplotlib.figure import Figure
import io
import base64
from bot import users_table, log_message, get_random_line
from SQLTable import SQLTable

app = Flask(__name__)
HOMEDIR = 'data\\'
HELLO_FILE = HOMEDIR + 'hello.txt'
FACTS_FILE = HOMEDIR + 'facts.txt'

DB_CONFIG = {
    'user': 'j1007852',
    'password': 'el|N#2}-F8',
    'host': 'mysql.j1007852.myjino.ru',
    'database': 'j1007852_petrova_andreev'
}

users_table = SQLTable(DB_CONFIG, "users")
messages_table = SQLTable(DB_CONFIG, "messages")
games_table = SQLTable(DB_CONFIG, "games")

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/facts', methods=['GET', 'POST'])
def facts():
    if request.method == 'POST':
        try:
            fact = request.form['fact']
            with open(FACTS_FILE, 'a', encoding='utf-8') as f:
                f.write(fact + '\n')
            return redirect(url_for('facts'))
        except Exception as e:
            return f"Error saving fact: {e}"
    try:
        with open(FACTS_FILE, 'r', encoding='utf-8') as f:
            facts = f.readlines()
    except Exception as e:
        facts = []
        print(f"Error reading facts: {e}")
    return render_template('facts.html', facts=facts)


@app.route('/hello', methods=['GET', 'POST'])
def hello():
    if request.method == 'POST':
        try:
            greeting = request.form['greeting']
            with open(HELLO_FILE, 'a', encoding='utf-8') as f:
                f.write(greeting + '\n')
            return redirect(url_for('hello'))
        except Exception as e:
            return f"Error saving greeting: {e}"
    try:
        with open(HELLO_FILE, 'r', encoding='utf-8') as f:
            greetings = f.readlines()
    except Exception as e:
        greetings = []
        print(f"Error reading greetings: {e}")
    return render_template('hello.html', greetings=greetings)


@app.route('/users')
def all_users():
    try:
        df_users = users_table.fetch_all()
        users = df_users.to_dict(orient="records")
        with open("zxc.txt", "a") as file:
            file.write("1" + "\n")
        for user in users:
            for key, value in user.items():
                if isinstance(value, str):
                    user[key] = value.encode('utf-8', errors='ignore').decode('utf-8')
        with open("zxc.txt", "a") as file:
            file.write("2" + "\n")
        for user in users:
            user_id = user['user_id']

            df_messages = messages_table.fetch_all()
            user_messages = df_messages[df_messages['user_id'] == user_id]
            with open("zxc.txt", "a") as file:
                file.write("2.1" + "\n")
            user['messages'] = user_messages.to_dict(orient="records")
            with open("zxc.txt", "a") as file:
                file.write("2.2" + "\n")
            df_games = games_table.fetch_all()
            user_games = df_games[df_games['user_id'] == user_id]
            user['games'] = user_games.to_dict(orient="records")
            with open("zxc.txt", "a") as file:
                file.write("2.3" + "\n")

        return render_template('users.html', users=users)
    except Exception as e:
        with open("zxc.txt", "a") as file:
            file.write(str(e) + "\n")
        return f"Error fetching users: {e}"





@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    try:
        users_table.delete_row("user_id", user_id)
        return redirect(url_for('all_users'))
    except Exception as e:
        return f"Error deleting user: {e}"

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'role' not in session:
        return redirect(url_for('login'))

    role = session['role']
    conn = get_db_connection()
    responses = conn.execute('SELECT * FROM responses').fetchall()
    conn.close()

    if role == 'Руководитель':
        return render_template('dashboard.html', responses=responses, show_stats=True)
    elif role == 'Управляющий':
        return render_template('dashboard.html', responses=responses, show_stats=False)
    else:
        return "Access denied"

@app.route('/edit_response/<int:response_id>', methods=['GET', 'POST'])
def edit_response(response_id):
    if 'role' not in session or session['role'] not in ['Управляющий', 'Руководитель']:
        return redirect(url_for('login'))

    conn = get_db_connection()
    response = conn.execute('SELECT * FROM responses WHERE id = ?', (response_id,)).fetchone()

    if request.method == 'POST':
        new_response = request.form['response']
        conn.execute('UPDATE responses SET response = ? WHERE id = ?', (new_response, response_id))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template('edit_response.html', response=response)



@app.route('/stats')
def stats():
    if 'role' not in session or session['role'] != 'Руководитель':
        return redirect(url_for('login'))

    conn = get_db_connection()
    messages = conn.execute('SELECT * FROM messages').fetchall()
    conn.close()

    # Generate statistics graph
    fig = Figure()
    ax = fig.subplots()
    ax.hist([row['timestamp'] for row in messages], bins=10)
    ax.set_title("Messages Statistics")
    ax.set_xlabel("Time")
    ax.set_ylabel("Number of Messages")

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return render_template('stats.html', messages=messages, img_base64=img_base64)




if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
