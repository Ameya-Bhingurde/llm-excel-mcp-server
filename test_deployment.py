"""
Test script for deployed Render API
Replace YOUR_APP_URL with your actual Render URL
"""

import requests
import json

# Replace this with your actual Render URL
BASE_URL = "https://your-app.onrender.com"

def test_root():
    """Test root endpoint"""
    print("Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

def test_analyze_data():
    """Test analyze-data endpoint"""
    print("Testing analyze-data endpoint...")
    payload = {
        "path": "sales_data_pivot_demo.xlsx",
        "sheet": "Sales"
    }
    response = requests.post(f"{BASE_URL}/mcp/analyze-data", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Message: {data.get('message')}")
        chart_data = data.get('chart_data', {})
        profile = chart_data.get('profile', {})
        print(f"Rows: {profile.get('row_count')}")
        print(f"Columns: {profile.get('column_count')}\n")
    else:
        print(f"Error: {response.text}\n")

if __name__ == "__main__":
    print("=" * 50)
    print("Render API Test Suite")
    print("=" * 50 + "\n")
    
    try:
        test_root()
        test_health()
        test_analyze_data()
        print("✅ All tests completed!")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API. Make sure:")
        print("   1. You've updated BASE_URL with your Render URL")
        print("   2. Your app is deployed and running")
        print("   3. The URL is correct (no trailing slash)")
    except Exception as e:
        print(f"❌ Error: {e}")
