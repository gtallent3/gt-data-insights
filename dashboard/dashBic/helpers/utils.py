import pandas as pd

# Dictionary of short labels for common violations
short_descriptions = {
    "failed to timely notify commission of a material information": "Late update to Commission",
    "a licensee must maintain copies of all inspection and certification of repair forms": "Missing inspection and or repair forms",
    "(e)   a trade waste vehicle must not be operated unless such vehicle is in safe operating": "Uncertified or unsafe trade waste vehicle",
    "a registrant must maintain copies of all daily inspection reports required by 17 rcny ? 7-03(f) for at least five (5) years": "Missing daily inspection logs",
    "an applicant for registration and a registrant": "No notice to the Commission of business changes",
    "each vehicle having a gross vehicle weight rating of": "Missing front mirror on truck",
    "a registrant must maintain copies of all inspection and certification of repair forms required by 17": "Missing 6-month repair records in vehicle",
    "a trade waste vehicle must not be operated unless": "Inspection proof not in truck",
    "it shall be unlawful for any person to operate a business for the purpose of": "No trade waste license",
    "removed collected or disposed of trade waste or without the proper commission issued license": "Unauthorized waste disposal",
    "failed to provide off-street parking": "Failed to provide off-street parking",
    "unreported change of ownership": "Ownership not filed",
}

def normalize_rule(text):
    if pd.isna(text):
        return ""
    return str(text).lower().strip().replace('\n', ' ').replace('\r', ' ')

def get_short_label(description):
    norm = normalize_rule(description)
    for key, short in short_descriptions.items():
        if norm.startswith(key):
            return short
    return description[:40] + '...' if isinstance(description, str) else "Unknown"