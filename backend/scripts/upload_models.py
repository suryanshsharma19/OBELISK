import os
import sys
from huggingface_hub import HfApi
from huggingface_hub.utils import HfHubHTTPError

def upload():
    api = HfApi()
    repo_id = "suryanshsharma19/obelisk-models"
    folder_path = os.path.join(os.path.dirname(__file__), "..", "ml_models", "saved_models")
    
    if not os.path.exists(folder_path):
        print(f"Error: Could not find saved_models directory at {folder_path}")
        sys.exit(1)
        
    print(f"[OBELISK] Initiating synchronization of {folder_path} to HuggingFace ({repo_id})...")
    
    try:
        print("[OBELISK] Verifying repository access...")
        api.create_repo(repo_id=repo_id, exist_ok=True, private=False)
        print("[OBELISK] Repository accessed successfully.")
    except HfHubHTTPError as e:
        print(f"[OBELISK] Note: Overwriting existing repository or permissions notice: {e}")

    print("[OBELISK] Uploading massive ML binaries...")
    print("---------------------------------------------------------")
    print("Please wait. This may take a few minutes based on your uplink speed.")
    try:
        api.upload_folder(
            folder_path=folder_path,
            repo_id=repo_id,
            repo_type="model",
            ignore_patterns=["*/tuning_logs/*"],
        )
        print("---------------------------------------------------------")
        print("[OBELISK] Upload complete! Models are securely backed up in the cloud.")
    except Exception as e:
        print(f"[OBELISK] FATAL: Upload failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    upload()
