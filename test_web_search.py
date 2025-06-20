# test_web_search.py - Test the web search functionality

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_fleetworthy_question():
    """Test a Fleetworthy-related question"""
    print("🔍 Testing Fleetworthy-related question...")
    
    payload = {
        "question": "How can Fleetworthy help reduce my fleet's fuel costs?",
        "company_website": "https://example-trucking.com",
        "company_description": "We operate 25 trucks for regional delivery services across the Southeast US. Our main challenges are rising fuel costs and inefficient routing."
    }
    
    try:
        print("Sending request...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60  # Extended timeout for AI processing
        )
        
        elapsed_time = time.time() - start_time
        print(f"Response received in {elapsed_time:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ SUCCESS!")
            print("AI Response:")
            print("=" * 50)
            print(data['message'])
            print("=" * 50)
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (this is normal for the first run)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_non_fleetworthy_question():
    """Test a non-Fleetworthy question (should be rejected)"""
    print("\n🔍 Testing non-Fleetworthy question...")
    
    payload = {
        "question": "What's the weather like today?"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            message = data['message']
            if "sorry" in message.lower() and "fleetworthy" in message.lower():
                print("✅ Correctly rejected non-Fleetworthy question")
                print(f"Response: {message}")
                return True
            else:
                print("❌ Should have rejected non-Fleetworthy question")
                print(f"Response: {message}")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_company_research():
    """Test company research functionality"""
    print("\n🔍 Testing company research...")
    
    payload = {
        "question": "What Fleetworthy solutions would benefit our transportation operations?",
        "company_website": "https://www.ups.com",
        "company_description": "Large logistics company with thousands of delivery vehicles"
    }
    
    try:
        print("Sending request (this may take longer due to web research)...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=120  # Extended timeout for research
        )
        
        elapsed_time = time.time() - start_time
        print(f"Response received in {elapsed_time:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ SUCCESS!")
            print("Research-based Response:")
            print("=" * 50)
            print(data['message'])
            print("=" * 50)
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (research can take time)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 Testing Fleetworthy Web Search Integration...")
    print(f"Testing against: {BASE_URL}")
    print("=" * 60)
    
    # First check if the server is running
    try:
        health_check = requests.get(f"{BASE_URL}/", timeout=5)
        if health_check.status_code != 200:
            print("❌ Server not responding. Make sure Flask app is running.")
            return
    except:
        print("❌ Cannot connect to server. Make sure Flask app is running on localhost:5000")
        return
    
    print("✅ Server is running")
    
    tests = [
        ("Fleetworthy Question", test_fleetworthy_question),
        ("Non-Fleetworthy Question", test_non_fleetworthy_question),
        ("Company Research", test_company_research)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
        
        time.sleep(2)  # Brief pause between tests
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    print(f"\nOverall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Your web search integration is working!")
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. Check the output above for details.")

if __name__ == "__main__":
    main()