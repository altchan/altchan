
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import json
from flask.templating import render_template

DBCREDS_FILENAME = 'dbcreds.json'

app = Flask(__name__)

# Database information

def create_db_string(filename):
    with open('dbcreds.json', 'r') as dbcredsfile:
        dbcreds = json.load(dbcredsfile)
    
    required_fields = ['host', 'port', 'username', 'password', 'database']
    
    for field in required_fields:
        if field not in dbcreds:
            raise ValueError('Error: {} is required in the py \
                    configuration'.format(field))
    
    db_string = 'postgresql://{}:{}@{}:{}/{}'.format(dbcreds['username'],
                                                     dbcreds['password'],
                                                     dbcreds['host'],
                                                     dbcreds['port'],
                                                     dbcreds['database'])
    
    return db_string

app.config['SQLALCHEMY_DATABASE_URI'] = create_db_string(DBCREDS_FILENAME)

db = SQLAlchemy(app)

class Board(db.Model):
    __tablename__ = 'boards'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    tag = db.Column(db.String(8), unique=True)
    nsfw = db.Column(db.Boolean)
    
    def __init__(self, name, tag, nsfw):
        self.name = name
        self.tag = tag
        self.nsfw = nsfw

class Thread(db.Model):
    __tablename__ = 'threads'
    id = db.Column(db.Integer, primary_key=True)
    board_id = db.Column(db.Integer, db.ForeignKey('boards.id'))
    timestamp = db.Column(db.String(64))
    
    board = db.relationship('Board', backref='boards')
    
    def __init__(self, board, timestamp):
        self.board = board
        self.timestamp = timestamp

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('threads.id'),
                          primary_key=True)
    content = db.Column(db.String(10000))
    filename = db.Column(db.String(64))
    timestamp = db.Column(db.String(64))
    
    thread = db.relationship('Thread', backref='posts')
    
    def __init__(self, thread, content, filename, timestamp):
        self.thread = thread
        self.content = content
        self.filename = filename
        self.timestamp = timestamp

# Read-only URL trees

@app.route('/boards/<board>/', methods=['GET'])
def board(board):
    return 'Visiting board {}'.format(board)

@app.route('/boards/<board>/<thread>/', methods=['GET'])
def thread(board, thread):
    return 'Visiting thread {} on board {}'.format(thread, board)

# Write-only URL trees

@app.route('/submit/<board>/')
def submit_thread(board):
    return 'Submitting thread on board {}'.format(board)

@app.route('/submit/<board>/<thread>')
def submit_post(board, thread):
    return 'Submitting post to thread {} on board {}'.format(thread, board)

@app.route('/')
def root():
    boards = Board.query.all()
    return render_template('index.html', boards=boards)

# Run the app

if __name__ == '__main__':
    app.run('0.0.0.0', 8080)
