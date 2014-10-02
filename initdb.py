
"""

initdb.py

This file is used to create the py and its tables. It reads the py
credentials from dbcreds.json, wipes the altchan py if it exists, and
creates the tables.

"""

from main import db, Board, Thread, Post

import datetime
import sys

def main():
    db.drop_all()
    db.create_all()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'd':
        # Entering some sample data
        b = Board('Random', 'b', True)
        b_thread1 = Thread(b, 'A Subject', datetime.datetime.now())
        b_thread1_post1 = Post(b_thread1, 'Person 1', 'First post content', None,
                               'first@email.com', datetime.datetime.now())
        b_thread1_post2 = Post(b_thread1, 'Person 2', 'Second post content', None,
                               'second@email.com', datetime.datetime.now())
        b_thread1_post3 = Post(b_thread1, 'Person 3', 'Third post content', None,
                               'third@email.com', datetime.datetime.now())
        
        # The UndefinedVariable comments tell PyDev to suppress errors that it
        # wrongly generates for the add and commit methods.
        db.session.add(b) #@UndefinedVariable
        db.session.add(b_thread1) #@UndefinedVariable
        db.session.add(b_thread1_post1) #@UndefinedVariable
        db.session.add(b_thread1_post2) #@UndefinedVariable
        db.session.add(b_thread1_post3) #@UndefinedVariable
        
        db.session.commit() #@UndefinedVariable
        
    
    print('The database has been set up.')

if __name__ == '__main__':
    main()
