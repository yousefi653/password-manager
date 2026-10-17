import sqlite3
from contextlib import contextmanager

from logger import get_logger

logger = get_logger(__name__)

DB_PATH = "passwords.sqlite"


class DatabaseService:
    @staticmethod
    @contextmanager
    def _connect():
        logger.debug("database: opening connection to %s", DB_PATH)
        conn = sqlite3.connect(DB_PATH)
        DatabaseService._create(cursor=conn.cursor())
        try:
            yield conn.cursor(), conn
            conn.commit()
            logger.debug("database: transaction committed")
        except Exception:
            logger.exception("database: transaction failed, rolling back")
            conn.rollback()
            raise
        finally:
            conn.close()
            logger.debug("database: connection closed")

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
        logger.info("users: creating user username=%r email=%s", username, email)
        with cls._connect() as (cursor, _):
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?);",
                (username, email, password),
            )
            logger.info("users: created user id=%s username=%r", cursor.lastrowid, username)
        return True

    @classmethod
    def get_user(cls, user_id):
        with cls._connect() as (cursor, _):
            cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
            row = cursor.fetchone()
        logger.debug("users: lookup id=%s found=%s", user_id, row is not None)
        return row

    @classmethod
    def get_all_users(cls):
        with cls._connect() as (cursor, _):
            cursor.execute("SELECT * FROM users;")
            rows = cursor.fetchall()
        logger.debug("users: fetched %s row(s)", len(rows))
        return rows

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
            logger.info("users: updated id=%s fields=%s", user_id, sorted(updates))
        return True

    @classmethod
    def remove_user(cls, user_id):
        logger.warning("users: deleting user id=%s and all owned rows", user_id)
        with cls._connect() as (cursor, _):
            cursor.execute("DELETE FROM data WHERE user = ?;", (user_id,))
            cursor.execute("DELETE FROM masterpassword WHERE user = ?;", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = ?;", (user_id,))
        logger.info("users: user id=%s deleted", user_id)
        return True

    # ── Master password ───────────────────────────────────────────────────────

    @classmethod
    def add_master_password(cls, user_id, password):
        logger.info("masterpassword: storing hash for user id=%s", user_id)
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
        logger.debug("masterpassword: lookup user id=%s found=%s", user_id, row is not None)
        return row[0] if row else None

    @classmethod
    def update_master_password(cls, user_id, new_password):
        logger.info("masterpassword: updating hash for user id=%s", user_id)
        with cls._connect() as (cursor, _):
            cursor.execute(
                "UPDATE masterpassword SET password = ? WHERE user = ?;",
                (new_password, user_id),
            )
        return True

    @classmethod
    def remove_master_password(cls, user_id):
        logger.warning("masterpassword: removing hash for user id=%s", user_id)
        with cls._connect() as (cursor, _):
            cursor.execute(
                "DELETE FROM masterpassword WHERE user = ?;",
                (user_id,),
            )
        return True

    # ── Data ──────────────────────────────────────────────────────────────────

    @classmethod
    def add_data(cls, data):
        logger.info(
            "data: saving entry site=%r user_id=%s username=%r",
            data.get("site"),
            data.get("user_id"),
            data.get("username"),
        )
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
            logger.info("data: saved entry id=%s site=%r", cursor.lastrowid, data.get("site"))
        return True

    @classmethod
    def get_data(cls, row_id):
        with cls._connect() as (cursor, _):
            cursor.execute("SELECT * FROM data WHERE id = ?;", (row_id,))
            row = cursor.fetchone()
        logger.debug("data: lookup id=%s found=%s", row_id, row is not None)
        return row

    @classmethod
    def get_all_data(cls, user_id=None):
        with cls._connect() as (cursor, _):
            if user_id:
                cursor.execute("SELECT * FROM data WHERE user = ?;", (user_id,))
            else:
                cursor.execute("SELECT * FROM data;")
            rows = cursor.fetchall()
        logger.debug("data: fetched %s row(s) user_id=%s", len(rows), user_id)
        return rows

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
            logger.info("data: updated id=%s fields=%s", row_id, sorted(updates))
        return True

    @classmethod
    def remove_data(cls, row_id):
        logger.warning("data: deleting entry id=%s", row_id)
        with cls._connect() as (cursor, _):
            cursor.execute("DELETE FROM data WHERE id = ?;", (row_id,))
        logger.info("data: deleted entry id=%s", row_id)
        return True
