import requests
import sys

def validate_online():
    # URL to a raw text file containing valid keys (one per line)
    DATABASE_URL = "https://raw.githubusercontent.com/youruser/yourrepo/main/keys.txt"
    
    try:
        response = requests.get(DATABASE_URL)
        valid_keys = response.text.splitlines()
    except Exception as e:
        print("Error connecting to the server.")
        sys.exit()

    user_key = input("Enter your license key: ")

    if user_key in valid_keys:
        print("Success! Verified online.")
    else:
        print("Invalid key or expired license.")
        sys.exit()

validate_online()