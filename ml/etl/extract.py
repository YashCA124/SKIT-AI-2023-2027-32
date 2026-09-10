import requests

import pandas as pd
import os


def save_raw_data(bookings, path):

    os.makedirs(
        os.path.dirname(path),
        exist_ok=True
    )

    df = pd.DataFrame(bookings)

    df.to_csv(
        path,
        index=False
    )

    return df
def fetch_bookings(api_url):

    response = requests.get(
        api_url,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

  
    if isinstance(data, dict):
        bookings = data.get("bookings", [])
    else:
        bookings = data

    return bookings