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
            {"id": 1, "name": "Prof. A", "project_count": 2, "availability": [True, True, True]},
            {"id": 2, "name": "Prof. B", "project_count": 1, "availability": [True, True, True]},
            {"id": 3, "name": "Prof. C", "project_count": 0, "availability": [True, True, True]},
            {"id": 4, "name": "Prof. D", "project_count": 0, "availability": [True, True, True]}
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
if response.status_code == 200:
    result = response.json()
    print(f"Başarılı! Sonuç: {json.dumps(result, indent=2)}")
else:
    print(f"Hata: {response.text}")
