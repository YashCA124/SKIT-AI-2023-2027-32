import requests


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