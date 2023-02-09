import sqlite3


class Database:
    def __init__(self):
        self.con = sqlite3.connect("spotify_tools.db")
        c = self.con.cursor()
        c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='Resources'")
        if not c.fetchone():
            c.execute("""CREATE TABLE 'Resources' ('uri' TEXT NOT NULL, 'type'TEXT NOT NULL, PRIMARY KEY('uri'));""")

        #ALTER
        #TABLE
        #ADD
        #COLUMN