
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
    timestamp = db.Column(db.DateTime)
    
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
    timestamp = db.Column(db.DateTime)
    
    thread = db.relationship('Thread', backref='posts')
    
    def __init__(self, thread, content, filename, timestamp):
        self.thread = thread
        self.content = content
        self.filename = filename
        self.timestamp = timestamp

# Read-only URL trees

@app.route('/boards/<board_tag>/', methods=['GET'])
def board(board_tag):
    # Retrieve information on the board based on the tag.
    board = Board.query.filter_by(tag=board_tag).first()
    
    #Get the threads for that board.
    threads = Thread.query.filter_by(board_id=board.id).all()
    
    # For each thread, get its posts.
    try:
        for thread in threads:
            thread.posts = Post.query.filter_by(thread_id=thread.id).all()
    except Exception as e:
        print(e)
    
    return render_template('board.html', board=board, threads=threads)

@app.route('/boards/<board_tag>/<thread>/', methods=['GET'])
def thread(board_tag, thread):
    return 'Visiting thread {} on board {}'.format(thread, board_tag)

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
    db.session.add(None)

# Run the app

if __name__ == '__main__':
    app.run('0.0.0.0', 8080)
