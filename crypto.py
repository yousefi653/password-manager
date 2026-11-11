import base64
import os

import bcrypt

from logger import get_logger

logger = get_logger(__name__)
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

backend = default_backend()


def encrypt_bcrypt(password):
    password = password.encode("utf-8")
    salt = bcrypt.gensalt(15)
    logger.debug("bcrypt: hashing password (cost=15)")

    hashed_pass = bcrypt.hashpw(password, salt)
    logger.debug("bcrypt: hash created (%s bytes)", len(hashed_pass))
    return hashed_pass


def check_password(password, hashed_pass):
    password = password.encode("utf-8")
    logger.debug("bcrypt: verifying password")

    result = bcrypt.checkpw(password, hashed_pass)
    logger.debug("bcrypt: verification result=%s", result)
    return result


def kdf(mpassword, salt=None):
    mpassword = mpassword.encode("utf-8")

    check_salt = False
    if salt is None:
        salt = os.urandom(16)
        logger.debug("pbkdf2: generated new 16-byte salt")
    else:
        check_salt = True
        logger.debug("pbkdf2: reusing stored salt (%s bytes)", len(salt))

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=backend,
    )

    key = kdf.derive(mpassword)
    logger.debug("pbkdf2: derived 32-byte key (iterations=100000)")

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
    logger.debug("aes-gcm: encrypted %s-byte payload", len(encrypted))
    return nonce, encrypted, tag


def aes_gcm_decrypt(key, nonce, encrypted, tag):
    decryptor = Cipher(
        algorithm=algorithms.AES(key), mode=modes.GCM(nonce, tag), backend=backend
    ).decryptor()

    data = decryptor.update(encrypted) + decryptor.finalize()
    logger.debug("aes-gcm: decrypted %s-byte payload", len(data))
    return data


def to_base64(text):
    if type(text) != bytes:
        text = text.encode("utf-8")

    return base64.b64encode(text).decode("utf-8")


def to_text(text):
    text = text.encode("utf-8")

    return base64.b64decode(text)
