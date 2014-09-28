
"""

initdb.py

This file is used to create the py and its tables. It reads the py
credentials from dbcreds.json, wipes the altchan py if it exists, and
creates the tables.

"""

from main import db

def main():
    db.drop_all()
    db.create_all()
    print('The database has been set up.')

if __name__ == '__main__':
    main()
