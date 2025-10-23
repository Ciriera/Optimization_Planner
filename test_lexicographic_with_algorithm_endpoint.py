import requests
import json

url = "http://localhost:8000/api/v1/algorithms/execute"

payload = {
    "algorithm_type": "lexicographic",
    "data": {
        "projects": [
            {"id": 1, "supervisor_id": 1, "title": "Test Project 1"},
            {"id": 2, "supervisor_id": 1, "title": "Test Project 2"},
            {"id": 3, "supervisor_id": 2, "title": "Test Project 3"}
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
        ],
        "classrooms": [
            {"id": 1, "name": "Room A", "capacity": 30},
            {"id": 2, "name": "Room B", "capacity": 25}
        ]
    },
    "parameters": {}
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, data=json.dumps(payload))

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
