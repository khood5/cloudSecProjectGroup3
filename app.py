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
GID = "current_group"

mysql = MySQL(app)
login_manager.init_app(app)

################################################################################################################
####         utlis avlable to all routes and functions                                                 
################################################################################################################
def run_query(q:str):
    if q[-1] is not ';':
        q = q + ';'
    print(f"running query: {q}")
    cursor = mysql.connection.cursor()
    cursor.execute(q)
    result = list(cursor.fetchall())
    print(f"got {len(result)} results ")
    print(f"result: {result}")
    mysql.connection.commit()
    cursor.close()
    return result

def getUserGroups():
    groupsQuery = f"select * from memberships where uid = '{session[USER]}';"
    groupMem = run_query(groupsQuery)
    gids = [i[-1] for i in groupMem]
    gids = ', '.join(gids)
    getGroups = f"select * from group_id where id in ({gids});"
    return run_query(getGroups)
################################################################################################################
####         User login, and maintacne functions and routes                                                 
################################################################################################################
class User:
    def __init__(self, username: str, password: str):
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
        if self.id is not None:
            return True
        return False
    
    def is_active(self):
        if self.id is None:
            return False
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
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

################################################################################################################
####         Home page methods, routes and functions                                                        
################################################################################################################

## Route for home page
# POST: used for posting a search request, needs search terms passed as <from> arguments 'words' and group id as 'gid' renders home normally otherwise a.k.a same as GET
# GET: displays the messages in a group chat where the group id is passed as <URL> argument 'gid'
# if no 'gid' is provided no messages will be shown note that in the in a POST request 'gid' is a form argument (a.k.a posted to the route) while a get request it's a url argument
@app.route('/home', methods=['POST', 'GET'])
@login_required
def home():
    searchResults = []
    session[GID] = request.args.get('gid')
    print(f"session[GID]:{session[GID]}")
    print(f"request:{request.args.get('gid')}")
    if request.method == 'POST':
        words = request.form['words']
        session[GID] = request.form['gid']
        query = f"select * from messages where body like '%{words}%' and gid = {session[GID]};"
        searchResults = run_query(query)
        searchResults = [list(m) for m in searchResults]
        for m in searchResults:
                groupsQuery = f"select username from user_ids where id = '{m[4]}';"
                author = run_query(groupsQuery)
                author = [a[0] for a in author]
                m[4] = author[0]
    groups = getUserGroups()
    messages = []
    if session[GID]:
        query = f"select * from messages where gid = {session[GID]};"
        messages = run_query(query)
        messages = [list(m) for m in messages]
        for m in messages:
            groupsQuery = f"select username from user_ids where id = '{m[4]}';"
            author = run_query(groupsQuery)
            author = [a[0] for a in author]
            m[4] = author[0]
    groupName = run_query(f"select * from group_id where id = '{session[GID]}'")
    if groupName:
        groupName = groupName[0][-1]
    else:
        groupName = None
    return render_template('home.html', searchResults=searchResults, groups=groups, current_group=session[GID], messages=messages, groupName=groupName)
    
## Route add message to a group chat
# POST: takes a group to post the message as 'gid' or group id and the message itself as 'message'
# redirects to home page passing the group id as 'gid' after the message has been inserted into the DB
@app.route('/add', methods=['POST'])
@login_required
def add():
    msg = request.form['message']
    query = f"insert into messages (body, author, gid)values ('{msg}', {session[USER]}, {session[GID]});"
    run_query(query)
    return redirect(url_for('home', gid=session[GID]))

################################################################################################################
####         New group routes and functions                                                        
################################################################################################################
@app.route('/newgroup', methods=['GET', 'POST'])
@login_required
def newgroup():
    if request.method == 'POST':
        newGroupName = request.form['groupName']
        if len(run_query(f"select * from group_id where name = '{newGroupName}'")) > 0:
            return render_template('newgroup.html', groups=getUserGroups(), error="Group name is already taken")
        
        addGroupQuery = f"insert into group_id (name) values ('{newGroupName}')"
        run_query(addGroupQuery)
        newGroupID = run_query(f"select id from group_id where name = '{newGroupName}'")[0][0]
        addCreaterAsMemberQuery = f"insert into memberships (gid, uid) values ('{newGroupID}','{session[USER]}')"
        run_query(addCreaterAsMemberQuery)
    return render_template('newgroup.html', groups=getUserGroups())

@app.route('/editgroup', methods=['GET', 'POST'])
@login_required
def editgroup():
    if request.method == 'POST':
        editgroupName = request.form['groupName']
        newUsername = request.form['username']
        group = run_query(f"select * from group_id where name = '{editgroupName}'")
        if len(group) == 0:
            return render_template('editgroup.html', groupName=editgroupName, error="Invalid Group name")
        newUser = run_query(f"select * from user_ids where username = '{newUsername}'")
        if len(newUser) == 0:
            return render_template('editgroup.html', groupName=editgroupName, error="Invalid username")
        run_query(f"insert into memberships (uid,gid) values ('{newUser[0][0]}','{group[0][0]}')")
        return redirect(url_for('home', gid=group[0][0])) 
    groupName = run_query(f"select * from group_id where id = '{session[GID]}'")
    if groupName:
        groupName = groupName[0][-1]
    else:
        groupName = None
    return render_template('editgroup.html', groupName=groupName, groups=getUserGroups())
if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug = False)
