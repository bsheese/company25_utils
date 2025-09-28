import gdown
import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import getpass
import hashlib
import numpy as np
import pandas as pd

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

def general_df_clean_up(df):
  # Convert all column names to lowercase
  df.columns = df.columns.str.lower()

  # shiptocounty and shipfromcounty, are monotonic (always US) and are dropped
  print('\nshiptocounty and shipfromcounty, are monotonic (always US) and are dropped.\n')
  df = df.drop(columns=['shiptocounty', 'shipfromcounty'])

  # convert invoicedate to datetime, there is no hours, minutes, seconds, so only the date is extracted
  df['invoicedate'] = pd.to_datetime(df['invoicedate'])

  # we have many columns with redudant text
  redundant_text_columns = ['counterpartyidentifier', 'productdescription', 'productgroup', 'productline', 'shiptoname', 'shipfromname']

  for col in redundant_text_columns:
    # Use .str.replace with a regular expression to remove non-numeric characters
    df[col] = df[col].str.replace(r'\D', '', regex=True)

    # Use pd.to_numeric to convert the cleaned strings to integers
    # errors='coerce' will turn any values that still can't be converted into NaN (Not a Number)
    df[col] = pd.to_numeric(df[col], errors='coerce')


  # Finally, if you need the columns to be strictly of integer type (not float), you can use .astype(int)
  df[redundant_text_columns] = df[redundant_text_columns].astype(int)

  # resolving the single issues using CAD by coverting to USD
  cad_mask = df.unit_price_currency == 'CAD'
  print('Fixing the Canadian Currenty issue...')
  print(f'# of rows with CAD: {cad_mask.sum()}')
  cad_value = df.loc[cad_mask, 'unit_price'].values[0]
  cad_date = df.loc[cad_mask, 'invoicedate'].values[0]

  print(f'Canadian Sale\tAmount in Canadian: {cad_value}\tDate of Sale: {cad_date}')
  print(f'CAD/USD Rate on 2021-2-5: 1 CAD = 078351')
  df.loc[cad_mask, 'unit_price'] = df.loc[cad_mask, 'unit_price'] * .78351  # the actual coversion is done here, the rest is just for display purposes
  print(f'Amount after conversion: {df.loc[cad_mask, 'unit_price'].values[0]}')

  print('Dropping unit price currency as all values are now in USD.\n')
  df = df.drop(columns = 'unit_price_currency')

  # Count all duplicate rows
  num_duplicate_rows = df.duplicated().sum()
  print(f"\nNumber of duplicate rows (considering all columns): {num_duplicate_rows}\n")

  # Show all rows that are duplicates (including their first occurrence)
  # all_duplicate_rows = df[df.duplicated(keep=False)]

  # Drop duplicates
  df = df.drop_duplicates()
  print('Dropped all duplicate rows\n')

  # Exploring zeros in columns of interest
  columns_of_interest = ['quantity', 'unit_price', 'total']
  for col in columns_of_interest:
    zero_counts = df[df[col] == 0].shape[0]
    print(f"Number of rows with zero values in '{col}': {zero_counts}")

  print(f"Original DataFrame shape: {df.shape}")
  df = df[df['total'] != 0].copy() # Use .copy() to avoid SettingWithCopyWarning
  print(f"DataFrame shape after dropping rows with total = 0: {df.shape}\n")  

  # Exploring Quantities of Less than One
  # ~89k sale transactions have a quantity of 0.74 
  # ~25k return transactions have a quantity of 0.74 
  # visualization of distributions show 0.74 heavily contribute to non-normality
  # visualization of distributions show 1.48 (2 X .74) also heavily contribute to non-normality

  # lets do a transform to normalize the quantites in integers values
  df['quantity'] = df['quantity'] / .74

  # lets do a tranform to normalize the unit_prices in values that tend to end in ,99
  df['unit_price'] = df['unit_price'] * .74

  # then lets recalculate the total
  df['total'] = df['quantity'] * df['unit_price']
  print('Normalized Quantity, Unit Price, and Total\n')
    
  df['month'] = df.invoicedate.dt.month
  df['year'] = df.invoicedate.dt.year
  df['day'] = df.invoicedate.dt.day
  print('Separate month, year, day columns created.\n')
  return df


