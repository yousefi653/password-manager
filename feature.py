from getpass import getpass
from prettytable import PrettyTable
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

    raise PermissionError("master password is incorrect!!!")


def remove(id):
    mpassword = getpass(">Enter your masster password: ")
    if storage.check_masterp(mpassword):
        if storage.remove(id):
            return True


def show_data():
    data = storage.read_data()
    my_table = PrettyTable(["id", "site", "username", "password"])

    for item in data:
        my_table.add_row(item[:4])
        my_table.add_divider()

    print(my_table)


def reveal(id):
    data = storage.read_data()

    for item in data:
        if item[0] == id:
            encrypted, salt, nonce, tag = item[3:]
            mpassword = getpass(">Enter your master password: ")

            if storage.check_masterp(mpassword):
                key = crypto.kdf(mpassword, crypto.to_text(salt))
                password = crypto.aes_gcm_decrypt(
                    key,
                    crypto.to_text(nonce),
                    crypto.to_text(encrypted),
                    crypto.to_text(tag),
                )
                return password.decode("utf-8")
            raise PermissionError("master password is incorrect.")
    raise KeyError("ID not found.")
