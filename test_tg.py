import urllib.request
import json
import ssl

token = "8979214380:AAFd58zcERx1jNfUY6puqEPqWMcDbb8RsYw"
url = f"https://api.telegram.org/bot{token}/getUpdates"
context = ssl._create_unverified_context()
try:
    req = urllib.request.Request(url, headers={"Content-Type": "application/json"}, method="GET")
    response = urllib.request.urlopen(req, context=context)
    print(response.read().decode())
except Exception as e:
    print(f"Error: {e}")
