import requests
import json

url = "http://localhost:8000/lexicographic/optimize"

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
