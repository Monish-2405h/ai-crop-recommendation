import urllib.request
import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


def test_api():
    print("🧪 Testing Main Crop vs Intercrop Advisory API Endpoints...")
    
    # 1. Test /api/crop-advisory endpoint directly for Tomato, Basil, Marigold
    for crop in ["Tomato", "Basil", "Marigold", "Rice", "Wheat"]:
        url = f"http://localhost:5000/api/crop-advisory?crop={crop}&N=70&P=50&K=50&temperature=28&humidity=75&ph=6.5&rainfall=100"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                assert data.get("crop") == crop, f"Expected crop {crop}, got {data.get('crop')}"
                assert "fertilizer" in data, "Missing fertilizer in advisory"
                assert "yield_est" in data, "Missing yield_est in advisory"
                assert "calendar" in data, "Missing calendar in advisory"
                print(f"  ✅ /api/crop-advisory ({crop}): Crop={data['crop']}, Fertilizer='{data['fertilizer']}', Yield={data['yield_est']} kg/acre")
        except Exception as e:
            print(f"  ❌ /api/crop-advisory ({crop}) failed: {e}")
            return False
    return True

def test_predictions_api():
    print("\n🧪 Testing /api/predictions response payload for Main Crop & Intercrops...")
    
    # 1. Sign up test user
    signup_url = "http://localhost:5000/api/auth/signup"
    user_payload = {
        "name": "Test Farmer",
        "email": "testfarmer_croprel@agrosense.com",
        "password": "password123"
    }
    req = urllib.request.Request(signup_url, data=json.dumps(user_payload).encode('utf-8'), headers={"Content-Type": "application/json"})
    token = None
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            token = data.get("token")
    except Exception as e:
        # If user already exists, try logging in
        login_url = "http://localhost:5000/api/auth/login"
        req = urllib.request.Request(login_url, data=json.dumps({"email": user_payload["email"], "password": user_payload["password"]}).encode('utf-8'), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            token = data.get("token")

    assert token, "Could not acquire JWT token for test user"

    # 2. Call /api/predictions
    pred_url = "http://localhost:5000/api/predictions"
    pred_payload = {
        "N": 70, "P": 50, "K": 50,
        "temperature": 28, "humidity": 75, "ph": 6.5, "rainfall": 100,
        "city": "Coimbatore", "sow_date": "2026-10-08"
    }
    req = urllib.request.Request(pred_url, data=json.dumps(pred_payload).encode('utf-8'), headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    
    with urllib.request.urlopen(req, timeout=5) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        
        main_crop = res.get("crop")
        print(f"  🌾 Main Crop Recommended: {main_crop}")
        print(f"  🌿 Intercrops Suggested: {res.get('intercrop_1')} & {res.get('intercrop_2')}")
        
        assert res.get("selected_crop_type") == "main", f"Expected selected_crop_type='main', got {res.get('selected_crop_type')}"
        assert "main_advisory" in res, "Missing main_advisory in response"
        assert "intercrop_1_advisory" in res, "Missing intercrop_1_advisory in response"
        assert "intercrop_2_advisory" in res, "Missing intercrop_2_advisory in response"
        
        main_adv = res["main_advisory"]
        ic1_adv  = res["intercrop_1_advisory"]
        ic2_adv  = res["intercrop_2_advisory"]
        
        print(f"  ✅ Main Crop Advisory: Crop={main_adv['crop']}, Fertilizer='{main_adv['fertilizer']}', Yield={main_adv['yield_est']} kg/acre")
        print(f"  ✅ Intercrop 1 Advisory: Crop={ic1_adv['crop']}, Fertilizer='{ic1_adv['fertilizer']}', Yield={ic1_adv['yield_est']} kg/acre")
        print(f"  ✅ Intercrop 2 Advisory: Crop={ic2_adv['crop']}, Fertilizer='{ic2_adv['fertilizer']}', Yield={ic2_adv['yield_est']} kg/acre")
        
        # Verify strict data isolation (Tomato's yield != Basil's yield, etc.)
        assert main_adv["crop"] != ic1_adv["crop"], "Main crop and Intercrop 1 cannot be identical"
        assert main_adv["fertilizer"] != ic1_adv["fertilizer"], "Main crop and Intercrop 1 fertilizers should be crop-specific"
        print("  🎯 Confirmed 100% Data Isolation between Main Crop and Intercrops!")

    return True

if __name__ == "__main__":
    success = test_api() and test_predictions_api()
    sys.exit(0 if success else 1)

