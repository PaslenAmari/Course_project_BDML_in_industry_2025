import os
import sys
import requests
import json
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load environment variables
from dotenv import load_dotenv
load_dotenv()

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
CANDIDATE_FOLDER_IDS = [
    os.getenv("YANDEX_FOLDER_ID", ""),
]

def check_yandex_cloud_gpt():
    print("\n--- Checking Yandex Cloud (Foundation Models) ---")
    
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/models"
    
    
    
    
    for fid in CANDIDATE_FOLDER_IDS:
        print(f"\nTesting Folder ID: {fid} (len={len(fid)})")
        headers = {
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "x-folder-id": fid
        }
        
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                print("SUCCESS! API Key and Folder ID are valid.")
                data = resp.json()
                models = data.get('models', [])
                print(f"Found {len(models)} models available:")
                for m in models:
                    print(f" - {m.get('name')} | URI: {m.get('uri')}")
                return 
            else:
                print(f"Failed. Status: {resp.status_code}")
                
        except Exception as e:
            print(f"Error: {e}")

def check_object_storage():
    print("\n--- Checking Object Storage (S3) Connectivity ---")
    
    
    
    print("Skipping: Api-Key is not valid for S3 access (requires Access Key ID & Secret).")

if __name__ == "__main__":
    check_yandex_cloud_gpt()
    check_object_storage()
