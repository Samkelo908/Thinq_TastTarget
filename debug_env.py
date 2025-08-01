import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== Environment Variables Debug ===\n")

# Check Hugging Face
hf_key = os.getenv("HUGGINGFACE_API_KEY")
print(f"HUGGINGFACE_API_KEY exists: {bool(hf_key)}")
if hf_key:
    print(f"HUGGINGFACE_API_KEY value: {hf_key[:10]}...{hf_key[-4:]}")
else:
    print("HUGGINGFACE_API_KEY is None or empty")

# Check Qloo
qloo_key = os.getenv("QLOO_API_KEY")
print(f"\nQLOO_API_KEY exists: {bool(qloo_key)}")
if qloo_key:
    print(f"QLOO_API_KEY value: {qloo_key[:10]}...{qloo_key[-4:]}")
else:
    print("QLOO_API_KEY is None or empty")

# Check file location
print(f"\n.env file location: {os.path.abspath('.env')}")
print(f".env file exists: {os.path.exists('.env')}")

# Show all env variables (be careful with this in production!)
print("\n=== All Environment Variables ===")
for key, value in os.environ.items():
    if "API" in key or "KEY" in key:
        if value:
            print(f"{key}: {value[:10]}...{value[-4:] if len(value) > 14 else value}")
        else:
            print(f"{key}: (empty)")

# Test reading .env file directly
print("\n=== Direct .env File Content ===")
try:
    with open('.env', 'r') as f:
        content = f.read()
        print(content)
except Exception as e:
    print(f"Error reading .env file: {e}")