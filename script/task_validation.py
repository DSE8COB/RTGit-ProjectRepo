import requests
import sys
 
url = "https://ews-emea.api.bosch.com/reviewtool/common-router-reviewdetail/q/v1/reviewdetails/status/1234"
 
headers = {
    "KeyId": "9bc39618-a714-4d87-aa6a-c4fd4985d9ba"
}
 
try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
 
    data = response.json()
    print("Response:", data)
 
    if data.get("returnId") == 0:
        print("❌ FAILURE:", data.get("returnErrorMessage"))
        sys.exit(1)
    else:
        print("✅ SUCCESS")
        sys.exit(0)
 
except Exception as e:
    print("❌ ERROR:", str(e))
    sys.exit(1)
