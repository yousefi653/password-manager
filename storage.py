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
        """CREATE TABLE masterpassword(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   password TEXT NOT NULL);"""
    )
    cursor.execute("""INSERT INTO masterpassword (password) VALUES(?)""", (mpassword,))
    conn.commit()
    conn.close()
    return True


def write_data(data):
    conn = sqlite3.connect("passwords.sqlite")
    cursor = conn.cursor()

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS data (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   site TEXT NOT NULL,
                   username TEXT NOT NULL,
                   encrypted TEXT NOT NULL,
                   salt TEXT NOT NULL,
                   nonce TEXT NOT NULL,
                   tag TEXT NOT NULL);"""
    )

    values = (
        data["site"],
        data["username"],
        data["encrypted"],
        data["salt"],
        data["nonce"],
        data["tag"]
    )


    cursor.execute(
        """INSERT INTO data (site, username, encrypted, salt, nonce, tag) VALUES(?, ?, ?, ?, ?, ?);""",
        tuple(values),
    )
    conn.commit()
    conn.close()
    return True


def check_masterp(password):
    conn = sqlite3.connect("passwords.sqlite")
    cursor = conn.cursor()

    cursor.execute("""SELECT password FROM masterpassword;""")
    row = cursor.fetchone()
    conn.close()

    return crypto.check_password(password, row[0])


def read_data():

    conn = sqlite3.connect("passwords.sqlite")
    cursor = conn.cursor()

    cursor.execute("""SELECT * FROM data;""")
    data = cursor.fetchall()
    conn.close()
    return data


def remove(id):
    conn = sqlite3.connect("passwords.sqlite")
    cursor = conn.cursor()

    cursor.execute("""DELETE FROM data WHERE id = ?""", (id,))
    conn.commit()
    conn.close()
    return True


def fix_id():
    try:
        data = read_data()
    except:
        pass
    else:
        conn = sqlite3.connect('passwords.sqlite')
        cursor = conn.cursor()
        
        n = 0
        for i in range(len(data)):
            n+=1 
            cursor.execute('''UPDATE data SET id=? WHERE id==?;''', (n, data[i][0]))
            conn.commit()
        conn.close()
