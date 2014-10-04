
# Flask imports
from flask import Flask, flash, redirect, request
from flask.templating import render_template
from flask_sqlalchemy import SQLAlchemy

# Project imports
from config import CONFIG

# Standard library imports
import datetime
import json
import os
import random

app = Flask(__name__, static_url_path='/static')
app.secret_key = CONFIG['secret_key']

CONFIG['file_directory'] = '/static/' + CONFIG['file_directory']

# Database information

def create_db_string():
    dbcreds = CONFIG['database']
    required_fields = ['host', 'port', 'username', 'password', 'database']
    
    for field in required_fields:
        if field not in dbcreds:
            raise ValueError('Error: {} is required in the py \
                    configuration'.format(field))
    
    db_string = 'postgresql://{}:{}@{}:{}/{}'.format(
         dbcreds['username'],
         dbcreds['password'],
         dbcreds['host'],
         dbcreds['port'],
         dbcreds['database'])
    
    return db_string

app.config['SQLALCHEMY_DATABASE_URI'] = create_db_string()

db = SQLAlchemy(app)

class Board(db.Model):
    __tablename__ = 'boards'
    name = db.Column(db.String(64))
    tag = db.Column(db.String(8), unique=True, primary_key=True)
    nsfw = db.Column(db.Boolean)
    
    def __init__(self, name, tag, nsfw):
        self.name = name
        self.tag = tag
        self.nsfw = nsfw

class Thread(db.Model):
    __tablename__ = 'threads'
    id = db.Column(db.Integer, primary_key=True)
    board_tag = db.Column(db.String(8), db.ForeignKey('boards.tag'))
    subject = db.Column(db.String(CONFIG['max_subject_length']))
    
    board = db.relationship('Board', backref='boards')
    
    def __init__(self, board, subject):
        self.board = board
        self.subject = subject

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('threads.id'),
                          primary_key=True)
    name = db.Column(db.String(CONFIG['max_name_length']))
    content = db.Column(db.String(CONFIG['max_message_length']))
    filename = db.Column(db.String(40))
    email = db.Column(db.String(CONFIG['max_email_length']))
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
    threads = Thread.query.filter_by(board_tag=board.tag).all()
    
    # For each thread, get its posts.
    try:
        for thread in threads:
            thread.posts = Post.query.filter_by(thread_id=thread.id).all()
    except Exception as e:
        print(e)
    
    try:
        return render_template('board.html', board=board, threads=threads, config=CONFIG)
    except Exception as e:
        print(e)

@app.route('/boards/<board_tag>/<thread>/', methods=['GET'])
def thread(board_tag, thread):
    return 'Visiting thread {} on board {}'.format(thread, board_tag)

# Write-only URL trees

@app.route('/submit/<board_tag>/', methods=['POST'])
def submit_thread(board_tag):
    # Check to make sure that all of the required fields are provided. Some of
    # them can be absent, since they have default values. Also trim fields if
    # they exceed their maximum length.
    subject = request.form['subject'][:CONFIG['max_subject_length']] \
        if 'subject' in request.form else ''
    email = request.form['email'][:CONFIG['max_email_length']] \
        if 'email' in request.form else ''
    name = request.form['name'][:CONFIG['max_name_length']] \
        if 'name' in request.form else CONFIG['default_name']
    
    error = False
    
    if 'message' not in request.form or \
        len(request.form['message'].strip()) == 0:
        # Don't return yet; if there are more errors, they should be
        # flashed as well.
        error = True
        flash('You must enter a message', 'error')
    elif len(request.form['message']) > CONFIG['max_message_length']:
        error = True
        flash('Your message was too long (maximum {})'.format( \
           CONFIG['max_message_length']))
    else:
        message = request.form['message']
    
    timestamp = datetime.datetime.now()
    
    if not 'upload' in request.files or \
        len(request.files['upload'].filename.strip()) == 0:
        error = True
        flash('You must upload a file to start a thread.', 'error')
    else:
        # Generate the files new name. For now, this will be the current time
        # concatenated with a random number in a range big enough to avoid
        # collision. The extension provided by the user is used, assuming it
        # is an allowed extension.
        provided_filename = request.files['upload'].filename
        extension = \
            provided_filename[provided_filename.rfind('.') + 1:].lower()
        
        if extension not in CONFIG['file_extensions']:
            flash('Extension {} is not allowed'.format(extension), 'error')
    
    if not error:
        filename = '{}_{}.{}'.format( \
           timestamp.strftime('%Y%m%d%H%M%S'),
           random.getrandbits(32),
           extension)
        # Get the associated board
        board = Board.query.filter_by(tag=board_tag).first()
        
        if board is None:
            flash('Board {} does not exist'.format(board_tag))
        else:
            thread = Thread(board, subject)
            post = Post(thread, name, message, filename, email, timestamp)
            request.files['upload'].save( \
                os.path.join(CONFIG['file_directory'][1:], filename))
            db.session.add(thread)
            db.session.add(post)
            db.session.commit()
    
    return redirect('/boards/{}/'.format(board_tag))

@app.route('/submit/<board>/<thread>')
def submit_post(board, thread, methods=['POST']):
    return 'Submitting post to thread {} on board {}'.format(thread, board)

@app.route('/')
def root():
    boards = Board.query.all()
    return render_template('index.html', boards=boards)

# Run the app

if __name__ == '__main__':
    app.run('0.0.0.0', 8080)
