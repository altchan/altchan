
import flask

app = flask.Flask(__name__)
app.config.from_object(__name__)

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

# Run the app

if __name__ == '__main__':
    app.run('0.0.0.0', 8080)
