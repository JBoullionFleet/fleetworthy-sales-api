# test_backend.py - Script to test the Flask backend endpoints

import requests
import json
import base64
import os

# Configuration
BASE_URL = "http://localhost:5000"  # Change to your Render.com URL for production testing

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_api_test_endpoint():
    """Test the /api/test endpoint"""
    print("\n🔍 Testing /api/test endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/test")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_chat_endpoint_basic():
    """Test the chat endpoint with basic data"""
    print("\n🔍 Testing /api/chat endpoint (basic)...")
    
    payload = {
        "question": "How can Fleetworthy help reduce my fuel costs?",
        "company_website": "https://example-trucking.com",
        "company_description": "We are a mid-size trucking company with 50 trucks operating across the Midwest. Our main challenges are rising fuel costs and inefficient route planning."
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_chat_endpoint_with_file():
    """Test the chat endpoint with file upload"""
    print("\n🔍 Testing /api/chat endpoint (with file)...")
    
    # Create a simple test file
    test_content = "This is a test company document.\nWe are a trucking company looking to optimize our operations.\nOur fleet consists of 25 trucks and we serve the East Coast."
    
    # Encode as base64
    file_data = base64.b64encode(test_content.encode()).decode()
    
    payload = {
        "question": "Based on our company document, what Fleetworthy services would be most beneficial?",
        "company_website": "https://test-trucking.com",
        "company_description": "Small trucking company focused on regional deliveries",
        "file_data": file_data,
        "file_name": "company_info.txt",
        "file_type": "text/plain"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_error_cases():
    """Test various error cases"""
    print("\n🔍 Testing error cases...")
    
    all_tests_passed = True
    
    # Test missing question
    print("Testing missing question...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Content-Type": "application/json"},
            json={"company_website": "https://example.com"}
        )
        status_ok = response.status_code == 400
        print(f"Missing question - Status: {response.status_code}, Expected: 400 {'✅' if status_ok else '❌'}")
        all_tests_passed = all_tests_passed and status_ok
    except Exception as e:
        print(f"❌ Missing question test failed: {e}")
        all_tests_passed = False
    
    # Test invalid URL
    print("Testing invalid URL...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Content-Type": "application/json"},
            json={
                "question": "Test question",
                "company_website": "invalid-url"
            }
        )
        status_ok = response.status_code == 400
        print(f"Invalid URL - Status: {response.status_code}, Expected: 400 {'✅' if status_ok else '❌'}")
        all_tests_passed = all_tests_passed and status_ok
    except Exception as e:
        print(f"❌ Invalid URL test failed: {e}")
        all_tests_passed = False
    
    # Test non-JSON request
    print("Testing non-JSON request...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Content-Type": "text/plain"},
            data="This is not JSON"
        )
        status_ok = response.status_code == 400
        print(f"Non-JSON - Status: {response.status_code}, Expected: 400 {'✅' if status_ok else '❌'}")
        all_tests_passed = all_tests_passed and status_ok
    except Exception as e:
        print(f"❌ Non-JSON test failed: {e}")
        all_tests_passed = False
    
    return all_tests_passed

def main():
    """Run all tests"""
    print("🚀 Starting Fleetworthy Backend Tests...")
    print(f"Testing against: {BASE_URL}")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("API Test Endpoint", test_api_test_endpoint),
        ("Chat Endpoint Basic", test_chat_endpoint_basic),
        ("Chat Endpoint with File", test_chat_endpoint_with_file),
        ("Error Cases", test_error_cases)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    print(f"\nOverall: {passed_count}/{total_count} tests passed")

if __name__ == "__main__":
    main()