import sys
import json
import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, CROP_DATA, CROP_STAGE_DATA, crop_calendar, make_token

def run_calendar_tests():
    print("==================================================")
    print("Testing Enhanced Dynamic Crop Calendar Feature")
    print("==================================================")

    # Test 1: Rice + October 2026 sowing date
    print("\n[TEST 1] Rice + 2026-10-08 Sowing Date")
    res1 = crop_calendar(CROP_DATA["Rice"], sow_date_str="2026-10-08", crop_name="Rice")
    print(f"Crop: {res1['crop']}")
    print(f"Sowing Date: {res1['sow_date_display']}")
    print(f"Total Duration: {res1['total_duration_days']} Days")
    print(f"Estimated Harvest Date: {res1['harvest_date_display']} ({res1['harvest_month_year']})")
    print("Stages:")
    for stg in res1['stages']:
        print(f"  - {stg['name']} ({stg['duration_days']}d): {stg['start_display']} – {stg['end_display']}")
    assert res1['sow_date'] == "2026-10-08"
    assert res1['harvest_month_year'] == "Feb 2027"
    print("✅ Test 1 Passed! Year transition 2026 -> 2027 verified.")

    # Test 2: Wheat + November 2026 sowing date
    print("\n[TEST 2] Wheat + 2026-11-15 Sowing Date")
    res2 = crop_calendar(CROP_DATA["Wheat"], sow_date_str="2026-11-15", crop_name="Wheat")
    print(f"Crop: {res2['crop']}")
    print(f"Sowing Date: {res2['sow_date_display']}")
    print(f"Estimated Harvest Date: {res2['harvest_date_display']}")
    assert res2['harvest_month_year'] == "Mar 2027"
    print("✅ Test 2 Passed!")

    # Test 3: Tomato + January 2027 sowing date
    print("\n[TEST 3] Tomato + 2027-01-10 Sowing Date")
    res3 = crop_calendar(CROP_DATA["Tomato"], sow_date_str="2027-01-10", crop_name="Tomato")
    print(f"Crop: {res3['crop']}")
    print(f"Sowing Date: {res3['sow_date_display']}")
    print(f"Estimated Harvest Date: {res3['harvest_date_display']}")
    assert res3['harvest_month_year'] == "Apr 2027"
    print("✅ Test 3 Passed!")

    # Test 4: Sugarcane + 2026-03-01 sowing date (360 days crossing into 2027)
    print("\n[TEST 4] Sugarcane + 2026-03-01 Sowing Date (360 days)")
    res4 = crop_calendar(CROP_DATA["Sugarcane"], sow_date_str="2026-03-01", crop_name="Sugarcane")
    print(f"Crop: {res4['crop']}")
    print(f"Sowing Date: {res4['sow_date_display']}")
    print(f"Estimated Harvest Date: {res4['harvest_date_display']}")
    assert res4['harvest_month_year'] == "Feb 2027"
    print("✅ Test 4 Passed!")

    # Test 5: Verify API predictions endpoint returns dynamic calendar
    print("\n[TEST 5] POST /api/predictions with sow_date")
    client = app.test_client()
    token = make_token("test_user_123", "user")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "N": 90, "P": 40, "K": 40, "temperature": 25, "humidity": 80, "ph": 6.5, "rainfall": 200,
        "lat": 11.0168, "lon": 76.9558, "city": "Coimbatore", "sow_date": "2026-10-08"
    }
    res = client.post("/api/predictions", json=payload, headers=headers)
    assert res.status_code in (200, 201)
    data = res.get_json()
    cal = data.get("calendar", {})
    print("API Calendar Output Crop:", cal.get("crop"))
    print("API Calendar Harvest Date:", cal.get("harvest_date_display"))
    assert cal.get("sow_date") == "2026-10-08"
    assert "stages" in cal and len(cal["stages"]) == 4
    print("✅ Test 5 Passed!")

    print("\n🎉 ALL CROP CALENDAR TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_calendar_tests()
