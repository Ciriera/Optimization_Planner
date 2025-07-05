import httpx
import asyncio
import sys
import traceback

async def test_json_login():
    """JSON login endpointini test eder"""
    try:
        async with httpx.AsyncClient() as client:
            # JSON login
            print("Login isteği gönderiliyor...")
            response = await client.post(
                "http://localhost:8000/api/v1/auth/login/json",
                json={"email": "admin@example.com", "password": "admin"}
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Login successful! Token: {data.get('access_token')[:20]}...")

                # Token ile algoritmalar listesini sorgulayalım
                token = data.get('access_token')
                headers = {"Authorization": f"Bearer {token}"}
                
                response = await client.get(
                    "http://localhost:8000/api/v1/algorithms/list",
                    headers=headers
                )
                print(f"Algorithms Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"Algorithms: {response.json()}")
                else:
                    print(f"Failed to get algorithms: {response.text}")
                    
                # Sınıfları sorgulayalım
                response = await client.get(
                    "http://localhost:8000/api/v1/classrooms/",
                    headers=headers
                )
                print(f"Classrooms Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"Classrooms: {response.json()}")
                else:
                    print(f"Failed to get classrooms: {response.text}")
                    
            else:
                print(f"Login failed: {response.text}")
                
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print(traceback.format_exc())
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_json_login())
    sys.exit(0 if success else 1) 