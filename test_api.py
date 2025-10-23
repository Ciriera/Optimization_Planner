import requests
import json

url = "http://localhost:8000/api/v1/algorithms/lexicographic"

payload = {
    "projects": [
        {"id": 1, "supervisor_id": 1},
        {"id": 2, "supervisor_id": 1},
        {"id": 3, "supervisor_id": 2}
    ],
    "instructors": [
        {"id": 1, "name": "Prof. A", "availability": [True, True, True]},
        {"id": 2, "name": "Prof. B", "availability": [True, True, True]},
        {"id": 3, "name": "Prof. C", "availability": [True, True, True]},
        {"id": 4, "name": "Prof. D", "availability": [True, True, True]}
    ],
    "timeslots": [
        {"id": 1, "start_time": "09:00", "end_time": "09:30"},
        {"id": 2, "start_time": "09:30", "end_time": "10:00"}
    ]
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, data=json.dumps(payload))

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
