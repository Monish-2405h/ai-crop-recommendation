import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, make_token

def test_endpoints():
    client = app.test_client()
    
    print("==================================================")
    print("Testing Agmarknet Integration Endpoints")
    print("==================================================")
    
    # 1. Test /api/market-price for various crops
    test_crops = ["Rice", "Tomato", "Onion", "Cotton", "Chilli"]
    
    for crop in test_crops:
        print(f"\n[TEST] GET /api/market-price?crop={crop}&latitude=11.0168&longitude=76.9558")
        res = client.get(f"/api/market-price?crop={crop}&latitude=11.0168&longitude=76.9558")
        print(f"Status Code: {res.status_code}")
        data = res.get_json()
        print(f"Response: {json.dumps(data, indent=2)}")
        assert res.status_code == 200
        assert "available" in data
        if not data["available"]:
            assert data.get("message") == "Live market price currently unavailable."
            print(f"✅ Correctly handled fallback message when Agmarknet is unreachable for {crop}")
        else:
            print(f"✅ Successfully fetched live Agmarknet data for {crop}: Modal Price = ₹{data.get('modal_price')}")

    # 2. Test /api/predictions (POST) with JWT token
    token = make_token("test_user_123", "user")
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n[TEST] POST /api/predictions")
    payload = {
        "N": 90,
        "P": 40,
        "K": 40,
        "temperature": 25,
        "humidity": 80,
        "ph": 6.5,
        "rainfall": 200,
        "lat": 11.0168,
        "lon": 76.9558,
        "city": "Coimbatore"
    }
    res = client.post("/api/predictions", json=payload, headers=headers)
    print(f"Status Code: {res.status_code}")
    data = res.get_json()
    assert res.status_code in (200, 201)
    print("Recommended Crop:", data.get("crop"))
    print("Market Data:", data.get("market_data"))
    print("Estimated Revenue:", data.get("estimated_revenue"))
    print("Profit per Acre:", data.get("profit_per_acre"))
    print("Market Trend:", data.get("market_trend"))
    print("\n🎉 ALL AGMARKNET INTEGRATION TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_endpoints()
