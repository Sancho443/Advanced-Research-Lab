import requests
import urllib

def send_request(url: str, method: str = "GET", data: dict = None, headers: dict = None) -> requests.Response: -> requests.Response:
    """
    Sends an HTTP request to the specified URL using the given method.
    Supports GET and POST methods. Additional data and headers can be provided.
    """
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, data=data, headers=headers)
        return response
    except requests.RequestException as e:
        print(f"Error sending request: {e}")
        return None