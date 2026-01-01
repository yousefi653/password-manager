# Password Manager

A secure and simple password manager to store and manage your passwords.

## Features

- Secure password storage using AES-GCM encryption
- Secure copy-to-clipboard functionality
- The ability to edit saved password information
- The ability to manage saved passwords

* Note: The Master Password is never stored. Without it, there is no access to your data.

## Security

- Uses AES-GCM for data encryption
- PBKDF2 for deriving encryption keys from the Master Password
- Random IV for each entry

## Installation

### Requirements

- Python 3.10+
- pip
- bcrypt==4.3.0
- click==8.2.1
- cryptography==45.0.7
- prettytable==3.16.0
- pycparser==2.22 >>> For use in Linux, the package (xclip or xsel) must also be installed. (sudo apt install xclip, sudo apt install xsel)

### Steps

1. Clone the repository:

    git clone https://github.com/yousefi653/password-manager.git
    cd password-manager

2. Install dependencies:

    pip install -r requirements.txt

3. Run the application:
    python main.py

## Usage

- Create an account: On the first run, choose a Master Password.
- Add passwords: Enter site, username, and password.
- manage: Categorize and search your stored passwords.

* Note: The Master Password is never stored. Without it, there is no access to your data.

## Project Structure
password-manager/
├── crypto.py
├── feature.py
├── main.py
├── README.md
├── requirements.txt
└── storage.py
