import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
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


def aes_gcm_encrypt(password, key):
    password = password.encode("utf-8")
    nonce = os.urandom(12)

    encryptor = Cipher(
        algorithm=algorithms.AES(key), mode=modes.GCM(nonce), backend=backend
    ).encryptor()
    encrypted = encryptor.update(password) + encryptor.finalize()
    tag = encryptor.tag
    return nonce, encrypted, tag


def aes_gcm_decrypt(key, nonce, encrypted, tag):
    decryptor = Cipher(
        algorithm=algorithms.AES(key), mode=modes.GCM(nonce, tag), backend=backend
    ).decryptor()

    data = decryptor.update(encrypted) + decryptor.finalize()
    return data


def to_base64(text):
    if type(text) != bytes:
        text = text.encode("utf-8")

    return base64.b64encode(text).decode("utf-8")


def to_text(text):
    text = text.encode("utf-8")

    return base64.b64decode(text)
