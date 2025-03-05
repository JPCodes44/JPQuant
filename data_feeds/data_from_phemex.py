import requests


def fetch_phemex_testnet_data():
    url = "https://testnet-api.phemex.com/md/ticker/24hr"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None


if __name__ == "__main__":
    data = fetch_phemex_testnet_data()
    if data:
        print(data)
