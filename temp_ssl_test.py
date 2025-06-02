import requests
import certifi
import os

# Explicitly set environment variables that requests might use
# (though requests usually picks up certifi automatically)
certifi_path = certifi.where()
print(f"Using certifi CA bundle: {certifi_path}")
os.environ['REQUESTS_CA_BUNDLE'] = certifi_path
# os.environ['CURL_CA_BUNDLE'] = certifi_path # Not directly used by requests, but no harm
# os.environ['SSL_CERT_FILE'] = certifi_path   # For other libs, no harm

# Test URL (same as your manual curl test, but a valid API endpoint is better)
# Let's use a generic Yahoo v7 chart API endpoint structure (won't get data without params, but tests connection)
# Or a known public Yahoo page
url = "https://query1.finance.yahoo.com/v7/finance/spark?symbols=AAPL&range=1d&interval=1d"
# url = "https://finance.yahoo.com/" # A simpler HTML page

print(f"Attempting to GET: {url}")

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
    print("SUCCESS! Connected and got a response.")
    print(f"Status Code: {response.status_code}")
    # print(f"Response content (first 200 chars): {response.text[:200]}")
except requests.exceptions.SSLError as e:
    print(f"SSL ERROR: {e}")
except requests.exceptions.ConnectionError as e:
    print(f"CONNECTION ERROR: {e}")
except requests.exceptions.HTTPError as e:
    print(f"HTTP ERROR: {e}")
    print(f"Status Code: {e.response.status_code}")
    print(f"Response content: {e.response.text}")
except requests.exceptions.RequestException as e:
    print(f"OTHER REQUESTS ERROR: {e}")
except Exception as e:
    print(f"UNEXPECTED ERROR: {e}") 