import os
import re
import secrets
import smtplib
import ssl
import threading
import time
from email.message import EmailMessage
from getpass import getpass

from dotenv import load_dotenv
from prettytable import PrettyTable

import crypto
from cache_service import RedisService
from storage import DatabaseService

load_dotenv()  # Load environment variables from .env file

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_HOST_PORT = int(os.getenv("EMAIL_HOST_PORT", "587"))
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


def timer(stop_event):
    for secound in range(120, -1, -1):
        print(f"\rYou have {secound} seconds to enter the verification code.", end="")
        time.sleep(1)
        if stop_event.is_set():
            break
    print("\nTime is up! Please request a new verification code.")


def generate_verfication_code(user_email):
    count = RedisService.get(key=f"{user_email}:verification_code:count") or 0
    if int(count) > 5:
        RedisService.set(key=f"{user_email}:limit_reached", value="true", ttl=3600)
        print("You have reached the maximum number of verification code requests. Please try again after 1 hour.")
        return None

    code = f"{secrets.randbelow(1_000_000):06d}"
    RedisService.set(key=f"{user_email}:verification_code", value=code, ttl=120)
    RedisService.increase(key=f"{user_email}:verification_code:count", )
    return code


def send_verfication_email(email, verification_code):
    msg = EmailMessage()
    msg.set_content(f"Your verification code is: {verification_code}")
    msg["Subject"] = "Verification Code"
    msg["From"] = EMAIL_HOST_USER
    msg["To"] = email

    try:
        with smtplib.SMTP(host=EMAIL_HOST, port=EMAIL_HOST_PORT, timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(user=EMAIL_HOST_USER, password=EMAIL_HOST_PASSWORD)

    except (
        smtplib.SMTPConnectError,
        smtplib.SMTPHeloError,
        smtplib.SMTPAuthenticationError,
    ):
        return False


def validate_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def verify_account(email):
    code = generate_verfication_code(user_email=email)
    if code is None:
        return False    

    send_verfication_email(email=email, verification_code=code)
    print("A verification code has been sent to your email. Please check your inbox.")
    
    
    stop_event = threading.Event()
    thread = threading.Thread(target=timer, args=(stop_event,), daemon=True)
    thread.start()

    while thread.is_alive():
        input_code = input(">Enter the verification code: ").strip()
        code = RedisService.get(f"{email}:verification_code")
        
        if input_code != code:
            print("Incorrect verification code. Please try again.")
            continue
        else:
            stop_event.set()
            thread.join()
            return True

    print("Verification code expired. Please request a new code.")
    return False

def signup():
    username = input(">Enter your username: ").strip()

    while True:
        email = input(">Enter your email: ").strip()
        if validate_email(email):
            break
        print("Invalid email format. Please try again.")

    master_password = getpass(">Enter your master password: ")
    confirm_password = getpass(">Confirm your master password: ")

    if master_password != confirm_password:
        raise ValueError("Passwords do not match.")

    master_password = crypto.encrypt_bcrypt(master_password)
    if DatabaseService.add_user(username=username, email=email, password=master_password):
        print("User registered successfully.")
    else:
        print("Failed to register user.")
        print("Please try again.")
        return False

    for i in range(5):
        result = verify_account(email=email)
        if result is False:
            new_code = input(">Do you want to request a new verification code? (y/n): ").strip().lower()
            if new_code == "y":
                continue
            else:
                print("Verification process aborted.")
                return False
        else:
            print("Account verified successfully.")
            return True
    return False



# def add(site, username, password):
#     mpassword = getpass(">Enter your master password: ")
#     if storage.check_masterp(mpassword):
#         key, salt = crypto.kdf(mpassword)
#         nonce, encrypted_data, tag = crypto.aes_gcm_encrypt(password, key)

#         data = {
#             "site": site,
#             "username": username,
#             "encrypted": crypto.to_base64(encrypted_data),
#             "salt": crypto.to_base64(salt),
#             "nonce": crypto.to_base64(nonce),
#             "tag": crypto.to_base64(tag),
#         }
#         return storage.write_data(data)

#     raise PermissionError("master password is incorrect!!!")


# def remove(id):
#     mpassword = getpass(">Enter your masster password: ")
#     if storage.check_masterp(mpassword):
#         if storage.remove(id):
#             return True


# def show_data():
#     data = storage.read_data()
#     my_table = PrettyTable(["id", "site", "username", "password"])

#     for item in data:
#         my_table.add_row(item[:4])
#         my_table.add_divider()

#     print(my_table)


# def reveal(id):
#     data = storage.read_data()

#     for item in data:
#         if item[0] == id:
#             encrypted, salt, nonce, tag = item[3:]
#             mpassword = getpass(">Enter your master password: ")

#             if storage.check_masterp(mpassword):
#                 key = crypto.kdf(mpassword, crypto.to_text(salt))
#                 password = crypto.aes_gcm_decrypt(
#                     key,
#                     crypto.to_text(nonce),
#                     crypto.to_text(encrypted),
#                     crypto.to_text(tag),
#                 )
#                 return password.decode("utf-8")
#             raise PermissionError("master password is incorrect.")
#     raise KeyError("ID not found.")
