import requests
import json

# Start call
print("1. Starting call...")
response = requests.post(
    "http://localhost:8000/call/start",
    json={"call_id": "test_001"}
)
data = response.json()
print(f"   Session: {data['session_id']}")
print(f"   Greeting: {data['greeting_text']}")

# Simulate scammer message
print("\n2. Scammer speaks...")
scammer_msg = "Hello madam, this is HDFC Bank. Your KYC is pending. Pay ₹500 to 9876543210@paytm"

response = requests.post(
    "http://localhost:8000/call/text",
    json={
        "call_id": "test_001",
        "text": scammer_msg
    }
)

result = response.json()
print(f"   AI Response: {result['response_text']}")
print(f"   Intelligence: {result.get('intelligence', [])}")
print(f"   Threat Level: {result.get('threat_level', 0)}/10")

# Check if UPI was captured
if result.get('intelligence'):
    for item in result['intelligence']:
        if item['data_type'] == 'upi_id':
            print(f"\n✅ SUCCESS! Captured UPI: {item['value']}")