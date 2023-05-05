# app.py
from flask import Flask, redirect, url_for, render_template, request, session
from flask_mysqldb import MySQL
from flask_login import LoginManager, login_required, login_user

app = Flask(__name__)
app.config['MYSQL_HOST'] = '10.37.0.31'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'letmein'
app.config['MYSQL_DB'] = 'chat2'
app.config['MYSQL_PORT'] = 3307
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
login_manager = LoginManager()

USERNAME = "username"
PASSWORD = "password"
USER = "user"

mysql = MySQL(app)
login_manager.init_app(app)

def run_query(q:str):
    print(f"running query: {q}")
    cursor = mysql.connection.cursor()
    cursor.execute(q)
    result = list(cursor.fetchall())
    print(f"got {len(result)} results ")
    print(f"result: {result}")
    mysql.connection.commit()
    cursor.close()
    return result

class User:
    def __init__(self, username: str, password: str):
        print("__init__")
        self.username = None
        self.password = None
        self.id = None
        query = f" select * from user_ids where username = '{username}' and password = '{password}';"
        result = run_query(query)
        if int(len(result)) == 0:
            return None
        else:
            self.username = username
            self.password = password
            self.id = result[0][0]
            return None
        
    def is_authenticated(self):
        print("is_authenticated")
        if self.id is not None:
            return True
        return False
    
    def is_active(self):
        print("is_active")
        if self.id is None:
            print("is_active: False")
            return False
        print("is_active: True")
        return True
    
    def is_anonymous(self):
        print("is_anonymous")
        return False
    
    def get_id(self):
        print(f"get_id{self.id}")
        return self.id

@login_manager.user_loader
def load_user(user_id):
    query = f" select * from user_ids where id = '{user_id}';"
    results = run_query(query)
    userInfo = results[0]
    if int(len(results)) == 0:
        return None
    else:
        return User(userInfo[2], userInfo[3])

@app.route('/', methods=['POST', 'GET'])
def index():
    error = None
    if request.method == 'POST':
        print(f"got username login request {request.form}")
        user = request.form[USERNAME]
        password = request.form[PASSWORD]
        query = f" select * from user_ids where username = '{user}' and password = '{password}';"
        results= run_query(query)
        if int(len(results)) == 0:
            error = "wrong username or password"
            return render_template('login.html', error=error)
        else:
            userID = results[0][0]
            u = load_user(userID)
            session[USER] = u.id
            login_user(u)
            
            return redirect(url_for('home'))
    return render_template('login.html', error = "")

@app.route('/home', methods=['POST', 'GET'])
@login_required
def home():
    groupsQuery = f"select * from memberships where uid = '{session[USER]}';"
    groups = run_query(groupsQuery)
    messages = []
    if request.args.get('gid'):
        query = f"select * from messages where gid = {request.args.get('gid')};"
        messages = run_query(query)
        messages = [list(m) for m in messages]
        for m in messages:
            groupsQuery = f"select username from user_ids where id = '{m[4]}';"
            author = run_query(groupsQuery)
            author = [a[0] for a in author]
            m[4] = author[0]
    return render_template('home.html', groups=groups, current_group=request.args.get('gid'), messages=messages)
    
    
@app.route('/add', methods=['POST'])
@login_required
def add():
    uid = request.form['uid']
    gid = request.form['gid']
    msg = request.form['message']
    query = f"insert into messages (body, author, gid)values ('{msg}', {uid}, {gid});"
    run_query(query)
    return redirect(url_for('home', gid=gid))

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug = False)
