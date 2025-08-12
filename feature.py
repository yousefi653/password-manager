from getpass import getpass
import crypto
import storage


def add(site, username, password):
    mpassword = getpass(">Enter your master password: ")
    if storage.check_masterp(mpassword):

        key, salt = crypto.kdf(mpassword)
        nonce, encrypted_data, tag = crypto.aes_gcm_encrypt(password, key)

        data = {
            "site": site,
            "username": username,
            "encrypted": crypto.to_base64(encrypted_data),
            "salt": crypto.to_base64(salt),
            "nonce": crypto.to_base64(nonce),
            "tag": crypto.to_base64(tag),
        }
        return storage.write_data(data)

    print(">>master password is incorrect!!!")
    return False
