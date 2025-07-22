import pandas as pd
from ..helpers.utils import get_short_label

def load_and_prepare_data():
    complaints = pd.read_csv("https://drive.google.com/uc?export=download&id=1OHuktLCuMQLOPM3igyxDeFr7U2iTfKEH")
    violations = pd.read_csv("https://drive.google.com/uc?export=download&id=1SOaADySZRl_mHg--NA4M0ZiORSecljwI")

    # Convert dates
    complaints['DATE COMPLAINT/INQUIRY REPORTED ON'] = pd.to_datetime(complaints['DATE COMPLAINT/INQUIRY REPORTED ON'], errors='coerce')
    violations['DATE VIOLATION ISSUED'] = pd.to_datetime(violations['DATE VIOLATION ISSUED'], errors='coerce')

    # Filter by year
    complaints = complaints[complaints['DATE COMPLAINT/INQUIRY REPORTED ON'].dt.year >= 2015]
    violations = violations[violations['DATE VIOLATION ISSUED'].dt.year >= 2015]

    # Add Year and ShortLabel
    complaints['Year'] = complaints['DATE COMPLAINT/INQUIRY REPORTED ON'].dt.year
    violations['Year'] = violations['DATE VIOLATION ISSUED'].dt.year
    violations['ShortLabel'] = violations['DESCRIPTION OF RULE'].apply(get_short_label)

    return complaints, violations