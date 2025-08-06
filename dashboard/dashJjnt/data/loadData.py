import pandas as pd
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials


"""
def load_and_prepare_data():
    bobData = pd.read_csv("https://drive.google.com/uc?id=1EmPBIxf9Cp8xMURCWvGdr_8vtCF7sVzD")

    #return complaints, violations
    return bobData
"""


# Get path to creds from environment variable
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
client = gspread.authorize(creds)

print("✅ Connected to Google successfully.")
print("📄 Sheets accessible by service account:")
for s in client.openall():
    print("   -", s.title)

sheet = client.open("DailyPnl").sheet1

def load_and_prepare_data():
    values = sheet.get_all_values()
    if not values or len(values) < 2:
        return pd.DataFrame(columns=["Date", "Instrument", "Pnl"])

    header = values[0]
    rows = values[1:]
    df = pd.DataFrame(rows, columns=header)

    # Clean up date: remove leading quotes if they exist
    df['Date'] = df['Date'].str.lstrip("'").str.strip()
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
    df['Pnl'] = pd.to_numeric(df['Pnl'], errors='coerce')

    if 'Daily Goal' in df.columns:
        df['Daily Goal'] = pd.to_numeric(df['Daily Goal'], errors='coerce')
    else:
        df['Daily Goal'] = None  # fallback column if not present

    return df.dropna(subset=['Date', 'Instrument', 'Pnl'])

def append_new_entry(date, instrument, pnl):
    # Format date as MM/DD/YYYY (string) — prevents Google Sheets from adding `'`
    formatted_date = pd.to_datetime(date).strftime('%m/%d/%Y')
    sheet.append_row([formatted_date, str(instrument), float(pnl)])
    return load_and_prepare_data()
