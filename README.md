# Password Manager

A command-line password manager written in Python. It stores website credentials in a local SQLite database and encrypts saved passwords before storing them.

## Features

- Add and manage saved website credentials
- Protect the master password with bcrypt hashing
- Derive an encryption key from the master password using PBKDF2-HMAC-SHA256
- Encrypt and decrypt stored passwords using AES-GCM
- Copy a revealed password to the clipboard
- Store credential records in SQLite

## Technologies

- Python
- SQLite
- Click
- bcrypt
- cryptography
- pyperclip

## Requirements

- Python 3.10 or newer
- Dependencies listed in `requirements.txt`
- On Linux, a clipboard utility such as `xclip` or `xsel` may be required by the clipboard package.

## Installation

Clone the repository:

```bash
git clone https://github.com/yousefi653/password-manager.git
cd password-manager
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\\Scripts\\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

On the first run, the application prompts you to create a master password. Use the interactive help to see the available commands.

## Security Notes

- The master password is stored as a bcrypt hash rather than as plaintext.
- Saved passwords are encrypted with AES-GCM.
- The encryption key is derived from the master password using PBKDF2-HMAC-SHA256 and a per-database salt.
- AES-GCM uses a nonce and authentication tag to protect encrypted data.

This is an educational project, not a professionally audited password manager. Do not use it to store important or production credentials without a thorough security review. In particular, review the key-derivation parameters, master-password handling, database lifecycle, and backup/recovery behavior before relying on it.

## Project Structure

```text
password-manager/
├── crypto.py
├── feature.py
├── main.py
├── storage.py
├── requirements.txt
└── README.md
```
