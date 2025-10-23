import requests
import json

url = "http://localhost:8000/lexicographic/optimize"

headers = {
    "Content-Type": "application/json"
}

# Boş veri ile test et (veritabanından veri çekecek)
response = requests.post(url, headers=headers)

print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"Başarılı! Atama sayısı: {result.get('result', {}).get('stats', {}).get('total_assignments', 0)}")
    print(f"AI Metrikleri: {result.get('result', {}).get('ai_metrics', {})}")
else:
    print(f"Hata: {response.text}")
