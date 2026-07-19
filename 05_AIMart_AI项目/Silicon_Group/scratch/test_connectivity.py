import os
from dotenv import load_dotenv
import requests

load_dotenv()
key = os.getenv('OPENAI_API_KEY')
base = os.getenv('OPENAI_API_BASE')
print('Key prefix:', key[:4] if key else None)
print('Base URL:', base)
if not key or not base:
    print('Missing API key or base URL')
else:
    url = f"{base.rstrip('/')}/models"
    headers = {'Authorization': f'Bearer {key}'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print('Status:', r.status_code)
        print('Response snippet:', r.text[:200])
    except Exception as e:
        print('Error:', e)
