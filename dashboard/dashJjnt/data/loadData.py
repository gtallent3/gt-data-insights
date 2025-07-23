import pandas as pd

def load_and_prepare_data():
    bobData = pd.read_csv("https://drive.google.com/uc?id=1EmPBIxf9Cp8xMURCWvGdr_8vtCF7sVzD")

    #return complaints, violations
    return bobData