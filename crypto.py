import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import bcrypt


backend = default_backend()


def encrypt_bcrypt(password):
    password = password.encode("utf-8")
    salt = bcrypt.gensalt(15)

    hashed_pass = bcrypt.hashpw(password, salt)
    return hashed_pass.decode("utf-8")


def check_password(password, hashed_pass):
    password = password.encode("utf-8")

    return bcrypt.checkpw(password, hashed_pass.encode("utf-8"))


def kdf(mpassword, salt=None):
    mpassword = mpassword.encode("utf-8")

    check_salt = False
    if salt is None:
        salt = os.urandom(16)
    else:
        check_salt = True

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=backend,
    )

    key = kdf.derive(mpassword)

    if check_salt:
        return key
    return key, salt
