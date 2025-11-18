"""
Test the login endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Test login
print("=" * 80)
print("Testing Login Endpoint")
print("=" * 80)

login_data = {
    "username": "a@gmail.com",
    "password": "123456"
}

print(f"\nSending login request:")
print(f"  URL: {BASE_URL}/auth/login")
print(f"  Username: {login_data['username']}")
print(f"  Password: {login_data['password']}")

try:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data=login_data,  # Form data, not JSON
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        print("\n✓ Login successful!")
        token = response.json().get("access_token")
        print(f"Access Token: {token[:50]}...")
    else:
        print(f"\n✗ Login failed with status {response.status_code}")
        
except Exception as e:
    print(f"\n✗ Error: {e}")

print("=" * 80)
