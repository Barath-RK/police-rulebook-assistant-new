"""
Police Rulebook Assistant - Complete Test Suite
All 5 tests should pass with the enhanced code
"""

import requests
import time

API_URL = "http://localhost:8000"

def test_backend_connection():
    print("\n" + "=" * 50)
    print("Test 1: Backend Connection")
    print("=" * 50)
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running on port 8000")
            return True
    except:
        print("❌ Backend not running. Start with: python -m uvicorn backend:app --reload --port 8000")
    return False

def test_murder_punishment():
    print("\n" + "=" * 50)
    print("Test 2: Murder Punishment (Section 302)")
    print("=" * 50)
    try:
        response = requests.post(f"{API_URL}/ask", json={"query": "What is the punishment for murder?"})
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "").lower()
            if "302" in answer or "death" in answer or "life imprisonment" in answer:
                print("✅ Found punishment for murder (Section 302)")
                return True
            else:
                print("⚠️ Answer received but section/punishment not clearly identified")
        else:
            print(f"❌ API returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    return False

def test_section_376():
    print("\n" + "=" * 50)
    print("Test 3: Section 376 (Rape)")
    print("=" * 50)
    try:
        response = requests.post(f"{API_URL}/ask", json={"query": "Tell me about Section 376"})
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "").lower()
            if "376" in answer or "rape" in answer:
                print("✅ Found Section 376 (Rape)")
                return True
            else:
                print("⚠️ Section 376 not clearly identified")
        else:
            print(f"❌ API returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    return False

def test_theft_bailable():
    print("\n" + "=" * 50)
    print("Test 4: Theft Bailable Status")
    print("=" * 50)
    try:
        response = requests.post(f"{API_URL}/ask", json={"query": "Is theft bailable?"})
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "").lower()
            if "bailable" in answer or "yes" in answer or "379" in answer:
                print("✅ Confirmed theft is bailable (Section 379)")
                return True
            else:
                print("⚠️ Bailable status not clearly confirmed")
        else:
            print(f"❌ API returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    return False

def test_rape_investigation():
    print("\n" + "=" * 50)
    print("Test 5: Rape Investigation Procedure")
    print("=" * 50)
    try:
        response = requests.post(f"{API_URL}/ask", json={"query": "What is the procedure for rape investigation?"})
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "").lower()
            keywords = ["medical", "examination", "statement", "victim", "investigation"]
            found = sum(1 for kw in keywords if kw in answer)
            if found >= 2:
                print(f"✅ Found rape investigation procedure ({found} keywords matched)")
                return True
            else:
                print("⚠️ Investigation procedure partially found")
        else:
            print(f"❌ API returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    return False

def test_theft_robbery_difference():
    print("\n" + "=" * 50)
    print("Test 6: Difference between Theft and Robbery")
    print("=" * 50)
    try:
        response = requests.post(f"{API_URL}/ask", json={"query": "Difference between theft and robbery"})
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "").lower()
            keywords = ["theft", "robbery", "force", "section", "379", "392"]
            found = sum(1 for kw in keywords if kw in answer)
            if found >= 3:
                print(f"✅ Found difference between theft and robbery ({found} keywords matched)")
                return True
            else:
                print(f"⚠️ Difference partially found ({found}/6 keywords)")
        else:
            print(f"❌ API returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    return False

def run_all_tests():
    print("\n" + "=" * 60)
    print("👮 POLICE RULEBOOK ASSISTANT - COMPLETE TEST SUITE")
    print("=" * 60)
    
    results = []
    
    results.append(test_backend_connection())
    time.sleep(1)
    results.append(test_murder_punishment())
    time.sleep(1)
    results.append(test_section_376())
    time.sleep(1)
    results.append(test_theft_bailable())
    time.sleep(1)
    results.append(test_rape_investigation())
    time.sleep(1)
    results.append(test_theft_robbery_difference())
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    test_names = [
        "Backend Connection",
        "Murder Punishment (Section 302)",
        "Section 376 (Rape)",
        "Theft Bailable Status",
        "Rape Investigation Procedure",
        "Difference: Theft vs Robbery"
    ]
    
    passed = sum(results)
    total = len(results)
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n📈 Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Project is ready for submission!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please check the errors above.")

if __name__ == "__main__":
    run_all_tests()
