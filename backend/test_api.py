import requests
import json

BASE_URL = "http://localhost:5000"

def test_admin_login():
    print("Testing admin login...")
    data = {
        "email": "admin@admin.com",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/api/admin/login", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json().get('token') if response.status_code == 200 else None

def test_create_lot(token):
    print("\nTesting create lot...")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "Test Parking Lot",
        "address": "123 Test Street",
        "pincode": "123456",
        "price": "50",
        "spots": "5"
    }
    response = requests.post(f"{BASE_URL}/api/admin/lots", json=data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_get_lots(token):
    print("\nTesting get lots...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/admin/lots", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_get_users(token):
    print("\nTesting get users...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/users", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    # Test admin login
    token = test_admin_login()
    
    if token:
        # Test create lot
        test_create_lot(token)
        
        # Test get lots
        test_get_lots(token)
        
        # Test get users
        test_get_users(token)
    else:
        print("Failed to get token, cannot test other endpoints") 