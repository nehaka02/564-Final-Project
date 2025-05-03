import time
import requests

url = "http://localhost:80/result" #remember to change this to the actual IP address of machine running the C2 Server.

while True:
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            result = res.json()["result"]
            if result:
                print(result, flush=True)
    except Exception as e:
        print(f"[!] Error polling result: {e}")
    
    time.sleep(2)  # Poll every 2 seconds
