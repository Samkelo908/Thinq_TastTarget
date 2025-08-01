import requests

# Your API key
api_key = "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"

# Test with a simple model
url = "https://api-inference.huggingface.co/models/gpt2"
headers = {
    "Authorization": f"Bearer {api_key}"
}
payload = {
    "inputs": "Hello, I am",
    "parameters": {
        "max_new_tokens": 10
    }
}

print(f"Testing API key: {api_key[:10]}...{api_key[-4:]}")
print(f"URL: {url}")
print(f"Headers: {headers}")

try:
    response = requests.post(url, headers=headers, json=payload)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")