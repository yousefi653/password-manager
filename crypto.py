import bcrypt


def ecrypt_bcrypt(password):
    password = password.encode("utf-8")
    salt = bcrypt.gensalt(15)

    hashed_pass = bcrypt.hashpw(password, salt)
    return hashed_pass.decode("utf-8")


def decrypt_bcrypt(password, hashed_pass):
    password = password.encode("utf-8")

    return bcrypt.checkpw(password, hashed_pass.encode("utf-8"))
