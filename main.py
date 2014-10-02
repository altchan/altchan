
# Flask imports
from flask import Flask
from flask import request
from flask.templating import render_template
from flask_sqlalchemy import SQLAlchemy

# Standard library imports
import datetime
import json
import random

# A few configuarion variables
DBCREDS_FILENAME = 'dbcreds.json'
DEFAULT_NAME = 'Anonymous'
MAX_EMAIL_LENGTH = 30
MAX_NAME_LENGTH = 30
MAX_SUBJECT_LENGTH = 60
FILE_DIRECTORY = 'images/'
FILE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif']

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
    subject = db.Column(db.String(MAX_SUBJECT_LENGTH))
    timestamp = db.Column(db.DateTime)
    
    board = db.relationship('Board', backref='boards')
    
    def __init__(self, board, subject, timestamp):
        self.board = board
        self.subject = subject
        self.timestamp = timestamp

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('threads.id'),
                          primary_key=True)
    name = db.Column(db.String(MAX_NAME_LENGTH))
    content = db.Column(db.String(10000))
    filename = db.Column(db.String(64))
    email = db.Column(db.String(MAX_EMAIL_LENGTH))
    timestamp = db.Column(db.DateTime)
    
    thread = db.relationship('Thread', backref='posts')
    
    def __init__(self, thread, name, content, filename, email, timestamp):
        self.thread = thread
        self.name = name
        self.content = content
        self.filename = filename
        self.email = email
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

@app.route('/submit/<board>/', methods=['POST'])
def submit_thread(board):
    # Check to make sure that all of the required fields are provided. Some of
    # them can be absent, since they have default values. Also trim fields if
    # they exceed their maximum length.
    subject = request.form['subject'][:MAX_SUBJECT_LENGTH] \
        if 'subject' in request.form else ''
    email = request.form['email'][:MAX_EMAIL_LENGTH] \
        if 'email' in request.form else ''
    name = request.form['name'][:MAX_NAME_LENGTH] \
        if 'name' in request.form else DEFAULT_NAME
    
    if 'message' not in request.form or \
        len(request.form['message'].strip()) == 0:
        return 'You must enter a message'
    
    timestamp = datetime.datetime.now()
    
    if 'upload' in request.files:
        # Generate the files new name. For now, this will be the current time
        # concatenated with a random number in a range big enough to avoid
        # collision. The extension provided by the user is used, assuming it
        # is an allowed extension.
        provided_filename = request.files['upload'].filename
        extension = provided_filename[provided_filename.rfind('.') + 1:].lower()
        if extension not in FILE_EXTENSIONS:
            return 'Extension {} is not allowed'.format(extension)
        filename = '{}_{}.{}'.format( \
           timestamp.strftime('%Y%m%d%H%M%S'),
           random.getrandbits(32),
           extension)
        return filename
    else:
        return 'You must upload a file to start a thread.'

@app.route('/submit/<board>/<thread>')
def submit_post(board, thread, methods=['POST']):
    return 'Submitting post to thread {} on board {}'.format(thread, board)

@app.route('/')
def root():
    boards = Board.query.all()
    return render_template('index.html', boards=boards)
    db.session.add(None)

# Run the app

if __name__ == '__main__':
    app.run('0.0.0.0', 8080)
