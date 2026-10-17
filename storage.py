import sqlite3
from contextlib import contextmanager

DB_PATH = "passwords.sqlite"


class DatabaseService:
    @staticmethod
    @contextmanager
    def _connect():
        conn = sqlite3.connect(DB_PATH)
        DatabaseService._create(cursor=conn.cursor())
        try:
            yield conn.cursor(), conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @classmethod
    def _create(cls, cursor):
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email    TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                is_verified INTEGER NOT NULL DEFAULT 0
            );"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS masterpassword (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                password TEXT NOT NULL,
                user     INTEGER NOT NULL,
                FOREIGN KEY (user) REFERENCES users(id)
            );"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS data (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user      INTEGER NOT NULL,
                site      TEXT NOT NULL,
                username  BLOB NOT NULL,
                encrypted BLOB NOT NULL,
                salt      BLOB NOT NULL,
                nonce     BLOB NOT NULL,
                tag       BLOB NOT NULL,
                FOREIGN KEY (user) REFERENCES users(id)
            );"""
        )

    # ── Users ─────────────────────────────────────────────────────────────────

    @classmethod
    def add_user(cls, username, email, password):
        with cls._connect() as (cursor, _):
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?);",
                (username, email, password),
            )
        return True

    @classmethod
    def get_user(cls, user_id):
        with cls._connect() as (cursor, _):
            cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
            return cursor.fetchone()

    @classmethod
    def get_all_users(cls):
        with cls._connect() as (cursor, _):
            cursor.execute("SELECT * FROM users;")
            return cursor.fetchall()

    @classmethod
    def update_user(cls, user_id, username=None, email=None, password=None):
        fields = {"username": username, "email": email, "password": password}
        updates = {k: v for k, v in fields.items() if v is not None}
        with cls._connect() as (cursor, _):
            for field, value in updates.items():
                cursor.execute(
                    f"UPDATE users SET {field} = ? WHERE id = ?;",
                    (value, user_id),
                )
        return True

    @classmethod
    def remove_user(cls, user_id):
        with cls._connect() as (cursor, _):
            cursor.execute("DELETE FROM data WHERE user = ?;", (user_id,))
            cursor.execute("DELETE FROM masterpassword WHERE user = ?;", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = ?;", (user_id,))
        return True

    # ── Master password ───────────────────────────────────────────────────────

    @classmethod
    def add_master_password(cls, user_id, password):
        with cls._connect() as (cursor, _):
            cursor.execute(
                "INSERT INTO masterpassword (password, user) VALUES (?, ?);",
                (password, user_id),
            )
        return True

    @classmethod
    def get_master_password(cls, user_id):
        with cls._connect() as (cursor, _):
            cursor.execute(
                "SELECT password FROM masterpassword WHERE user = ?;",
                (user_id,),
            )
            row = cursor.fetchone()
        return row[0] if row else None

    @classmethod
    def update_master_password(cls, user_id, new_password):
        with cls._connect() as (cursor, _):
            cursor.execute(
                "UPDATE masterpassword SET password = ? WHERE user = ?;",
                (new_password, user_id),
            )
        return True

    @classmethod
    def remove_master_password(cls, user_id):
        with cls._connect() as (cursor, _):
            cursor.execute(
                "DELETE FROM masterpassword WHERE user = ?;",
                (user_id,),
            )
        return True

    # ── Data ──────────────────────────────────────────────────────────────────

    @classmethod
    def add_data(cls, data):
        with cls._connect() as (cursor, _):
            cursor.execute(
                """INSERT INTO data (site, user, username, encrypted, salt, nonce, tag)
                   VALUES (?, ?, ?, ?, ?, ?, ?);""",
                (
                    data["site"],
                    data["user_id"],
                    data["username"],
                    data["encrypted"],
                    data["salt"],
                    data["nonce"],
                    data["tag"],
                ),
            )
        return True

    @classmethod
    def get_data(cls, row_id):
        with cls._connect() as (cursor, _):
            cursor.execute("SELECT * FROM data WHERE id = ?;", (row_id,))
            return cursor.fetchone()

    @classmethod
    def get_all_data(cls, user_id=None):
        with cls._connect() as (cursor, _):
            if user_id:
                cursor.execute("SELECT * FROM data WHERE user = ?;", (user_id,))
            else:
                cursor.execute("SELECT * FROM data;")
            return cursor.fetchall()

    @classmethod
    def update_data(cls, row_id, data):
        fields = ["site", "username", "encrypted", "salt", "nonce", "tag"]
        updates = {k: v for k, v in data.items() if k in fields and v is not None}
        with cls._connect() as (cursor, _):
            for field, value in updates.items():
                cursor.execute(
                    f"UPDATE data SET {field} = ? WHERE id = ?;",
                    (value, row_id),
                )
        return True

    @classmethod
    def remove_data(cls, row_id):
        with cls._connect() as (cursor, _):
            cursor.execute("DELETE FROM data WHERE id = ?;", (row_id,))
        return True
