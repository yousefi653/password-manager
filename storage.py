import sqlite3
import os
from getpass import getpass
import crypto


def check_db():
    if os.path.exists("passwords.sqlite"):
        return True

    print(">>DataBase don't exists so enter master password for create a db")

    result = False
    while not result:
        p1 = getpass(">Enter your master password: ").strip()
        p2 = getpass(">Enter your master password again: ").strip()

        if p1 == p2:
            hashed_pass = crypto.encrypt_bcrypt(p1)
            if create_db(hashed_pass):
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
    conn.commit()
    return True


def write_data(data):
    conn = sqlite3.connect('passwords.sqlite')
    curosr = conn.cursor()

    curosr.execute("""CREATE TABLE IF NOT EXISTS data (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   site TEXT NOT NULL,
                   username TEXT NOT NULL,
                   encrypted TEXT NOT NULL,
                   salt TEXT NOT NULL,
                   nonce TEXT NOT NULL,
                   tag TEXT NOT NULL);""")

    values = []
    for value in data.values():
        values.append(value)


    curosr.execute("""INSERT INTO data (site, username, encrypted, salt, nonce, tag) VALUES(?, ?, ?, ?, ?, ?);""", tuple(values))
    conn.commit()
    return True


def check_masterp(password):
    conn = sqlite3.connect('passwords.sqlite')
    cursor = conn.cursor()

    cursor.execute("""SELECT password FROM masterpassword;""")
    row = cursor.fetchone()
    
    return crypto.check_password(password, row[0])