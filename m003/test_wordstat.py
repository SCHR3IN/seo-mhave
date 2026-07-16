import os
import urllib.request
import json
import ssl

def load_env_file():
    for path in [".env", "seo/.env"]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip().strip('"').strip("'")
            break

def main():
    load_env_file()
    api_key = os.environ.get("YANDEX_API_KEY", "")
    url = "https://searchapi.api.cloud.yandex.net/v2/wordstat/topRequests"
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json"
    }

    
    data = {
        "phrase": "косметика",
        "numPhrases": 10,
        "regions": ["225"], # Russia
        "devices": ["DEVICE_ALL"]
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            status = response.getcode()
            body = response.read().decode("utf-8")
            print(f"Status: {status}")
            print(body)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(e.read().decode("utf-8"))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
