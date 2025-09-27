import gdown
import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import getpass
import hashlib
import numpy as np

def download_and_decrypt_data(file_id="1V2S-lUrFxcAJze_opSaWZrfk3_6LBdJL", encrypted_filename="encrypted_data.enc", decrypted_filename="decrypted_data_file.csv"):
    """
    Downloads an encrypted file from Google Drive and decrypts it.

    Args:
        file_id (str): The Google Drive file ID of the encrypted file.
        encrypted_filename (str): The name to save the downloaded encrypted file as.
        decrypted_filename (str): The name to save the decrypted file as.

    Returns:
        bool: True if decryption is successful, False otherwise.
    """
    gdown.download(f"https://drive.google.com/uc?id={file_id}", encrypted_filename, quiet=False)

    # Prompt for the password
    password = getpass.getpass('Enter the password to decrypt the file: ').encode()

    # Read the encrypted file
    with open(encrypted_filename, 'rb') as encrypted_file:
        encrypted_data_with_salt = encrypted_file.read()

    # Extract the salt (first 16 bytes)
    salt = encrypted_data_with_salt[:16]
    encrypted_data = encrypted_data_with_salt[16:]

    # Regenerate the key using the password and salt
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))

    # Create a Fernet instance
    fernet = Fernet(key)

    try:
        # Decrypt the data
        decrypted_data = fernet.decrypt(encrypted_data)

        # Save the decrypted data to a file
        with open(decrypted_filename, 'wb') as decrypted_file:
            decrypted_file.write(decrypted_data)

        print(f"File decrypted successfully and saved as '{decrypted_filename}'")

        FILENAME = encrypted_filename
        try:
            with open(FILENAME, 'rb') as f:
                bytes = f.read()
                readable_hash = hashlib.sha256(bytes).hexdigest()
                print(f"The SHA-256 hash of {FILENAME} is:")
                print(readable_hash)
        except FileNotFoundError:
            print(f"Error: Could not find the file named '{FILENAME}'. Please check the file name and location.")

        return True
    except Exception as e:
        print(f"An error occurred during decryption: {e}")
        print("Please check if the password is correct.")
        return False


