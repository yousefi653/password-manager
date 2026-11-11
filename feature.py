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
from logger import get_logger
from storage import DatabaseService, StorageError

logger = get_logger(__name__)

load_dotenv()  # Load environment variables from .env file

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_HOST_PORT = int(os.getenv("EMAIL_HOST_PORT", "587"))
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


def timer(stop_event):
    logger.debug("verification timer started (120s)")
    for secound in range(120, -1, -1):
        print(f"\rYou have {secound} seconds to enter the verification code.", end="")
        time.sleep(1)
        if stop_event.is_set():
            logger.debug("verification timer stopped early by caller")
            break
    print("\nTime is up! Please request a new verification code.")
    logger.info("verification timer finished")


def generate_verfication_code(user_email):
    logger.debug("verification code requested for %s", user_email)
    try:
        count = RedisService.get(key=f"{user_email}:verification_code:count") or 0
    except Exception:
        logger.exception("failed to read verification attempts for %s", user_email)
        raise

    if int(count) > 5:
        logger.warning("verification limit reached for %s (attempts=%s)", user_email, count)
        RedisService.set(key=f"{user_email}:limit_reached", value="true", ttl=3600)
        print("You have reached the maximum number of verification code requests. Please try again after 1 hour.")
        return None

    code = f"{secrets.randbelow(1_000_000):06d}"
    RedisService.set(key=f"{user_email}:verification_code", value=code, ttl=120)
    RedisService.increase(key=f"{user_email}:verification_code:count", )
    logger.info("verification code generated for %s (ttl=120s, attempts=%s)", user_email, int(count) + 1)
    return code


def send_verfication_email(email, verification_code):
    msg = EmailMessage()
    msg.set_content(f"Your verification code is: {verification_code}")
    msg["Subject"] = "Verification Code"
    msg["From"] = EMAIL_HOST_USER
    msg["To"] = email

    logger.info("sending verification email to %s via %s:%s", email, EMAIL_HOST, EMAIL_HOST_PORT)

    try:
        with smtplib.SMTP(host=EMAIL_HOST, port=EMAIL_HOST_PORT, timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(user=EMAIL_HOST_USER, password=EMAIL_HOST_PASSWORD)
            logger.debug("SMTP session authenticated for %s", email)

    except (
        smtplib.SMTPConnectError,
        smtplib.SMTPHeloError,
        smtplib.SMTPAuthenticationError,
    ):
        logger.exception("failed to send verification email to %s", email)
        return False

    logger.warning(
        "verification email NOT dispatched to %s: no send_message() call in SMTP block",
        email,
    )


def validate_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def verify_account(email):
    logger.info("account verification started for %s", email)
    code = generate_verfication_code(user_email=email)
    if code is None:
        logger.warning("account verification aborted for %s: no code generated", email)
        return False    

    send_verfication_email(email=email, verification_code=code)
    print("A verification code has been sent to your email. Please check your inbox.")
    
    
    stop_event = threading.Event()
    thread = threading.Thread(target=timer, args=(stop_event,), daemon=True)
    thread.start()

    attempts = 0
    while thread.is_alive():
        input_code = input(">Enter the verification code: ").strip()
        code = RedisService.get(f"{email}:verification_code")
        attempts += 1
        
        if input_code != code:
            logger.warning("incorrect verification code for %s (attempt %s)", email, attempts)
            print("Incorrect verification code. Please try again.")
            continue
        else:
            logger.info("verification code accepted for %s after %s attempt(s)", email, attempts)
            stop_event.set()
            thread.join()
            return True

    logger.warning("verification code expired for %s after %s attempt(s)", email, attempts)
    print("Verification code expired. Please request a new code.")
    return False

def signup():
    logger.info("signup started")
    username = input(">Enter your username: ").strip()
    logger.debug("signup: username=%r", username)

    while True:
        email = input(">Enter your email: ").strip()
        if validate_email(email):
            break
        logger.warning("signup: rejected invalid email format %r", email)
        print("Invalid email format. Please try again.")

    logger.info("signup: registering username=%r email=%s", username, email)

    master_password = getpass(">Enter your master password: ")
    confirm_password = getpass(">Confirm your master password: ")

    if master_password != confirm_password:
        logger.warning("signup aborted for %s: passwords do not match", email)
        raise ValueError("Passwords do not match.")

    master_password = crypto.encrypt_bcrypt(master_password)
    try:
        created = DatabaseService.add_user(username=username, email=email, password=master_password)
    except StorageError as error:
        logger.warning("signup rejected for %s: %s", email, error)
        print(f"Cannot create account: {error}.")
        return False
    except Exception:
        logger.exception("signup failed for %s: could not create user", email)
        raise

    if created:
        logger.info("user registered username=%r email=%s", username, email)
        print("User registered successfully.")
    else:
        logger.error("user registration returned false for %s", email)
        print("Failed to register user.")
        print("Please try again.")
        return False

    for attempt in range(1, 6):
        logger.debug("signup: verification attempt %s/5 for %s", attempt, email)
        result = verify_account(email=email)
        if result is False:
            new_code = input(">Do you want to request a new verification code? (y/n): ").strip().lower()
            if new_code == "y":
                continue
            else:
                logger.warning("signup: verification aborted by user for %s", email)
                print("Verification process aborted.")
                return False
        else:
            logger.info("account verified successfully for %s", email)
            print("Account verified successfully.")
            return True

    logger.warning("signup: verification attempts exhausted for %s", email)
    return False


def login():
    logger.info("login started")

    while True:
        email = input(">Enter your email: ").strip()
        if not validate_email(email):
            continue

        password = getpass(">Enter your master password: ")
        break

    try:
        user = DatabaseService.get_user_by_email(email=email)
    except StorageError as error:
        logger.warning("login failed for %s: %s", email, error)
        print(f"Login failed: {error}.")
        return False
    except Exception:
        logger.exception("login failed for %s: could not retrieve user", email)
        raise

    if user is None:
        logger.warning("login failed for %s: user not found", email)
        print("User not found. Please check your email or sign up.")
        return False

    user_id = user[0]
    username = user[1]
    user_email = user[2]
    stored_password = user[3]
    is_verfied = user[-1]


    if not bool(is_verfied):
        print(
            "Your account is not verified. Please verify your account before logging in."
        )
        for attempt in range(1, 6):
            logger.debug("login: verification attempt %s/5 for %s", attempt, email)
            result = verify_account(email=email)
            if result is False:
                new_code = (
                    input(">Do you want to request a new verification code? (y/n): ")
                    .strip()
                    .lower()
                )
                if new_code == "y":
                    continue
                else:
                    logger.warning("login: verification aborted by user for %s", email)
                    print("Verification process aborted.")
                    return False
            else:
                logger.info("account verified successfully for %s", email)
                DatabaseService.update_user(user_id=user_id, is_verfied=is_verfied)
                print("Account verified successfully.")
                return True

    if crypto.check_password(password, stored_password):
        logger.info("login successful for %s", email)

        RedisService.set(
            f"sessions:user:{user_id}",
            json.dumps(
                {
                    "user_email": user_email,
                    "is_verfied": is_verfied,
                    "username": username,
                }
            ),
            60*15
        )
        print("Login successful.")

    else:
        logger.warning("login failed for %s: incorrect password", email)
        print("Incorrect password. Please try again.")
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
