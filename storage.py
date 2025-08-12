import sqlite3
import os
from getpass import getpass


def check_db():
    if os.path.exists("passwords.sqlite"):
        return True

    print(">>DataBase don't exists so enter master password for create a db")

    result = False
    while not result:
        p1 = getpass(">Enter your master password: ").strip()
        p2 = getpass(">Enter your master password again: ").strip()

        if p1 == p2:
            if create_db(p1):
                result = True
        else:
            print(">>passwords are not match!!")
    return True


def create_db(mpassword):

    conn = sqlite3.connect("passwords.sqlite")
    cursor = conn.cursor()

    cursor.execute(
        """CREATE TABLE masterpassword (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   password TEXT NOT NULL);"""
    )
    cursor.execute("""INSERT INTO masterpassword (password) VALUES(?)""", (mpassword,))
    return True
