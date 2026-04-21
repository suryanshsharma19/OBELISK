import os
import sys
from huggingface_hub import snapshot_download

def download():
    repo_id = "suryanshsharma19/obelisk-models"
    models_dir = os.path.join(os.path.dirname(__file__), "..", "ml_models", "saved_models")
    
    # Check if a core model metrics file exists to determine if download is needed
    core_metrics = os.path.join(models_dir, "realistic_leaderboard.json")
    
    if os.path.exists(core_metrics) and "--force" not in sys.argv:
        print(f"[OBELISK] ML Models already detected locally in {models_dir}")
        print("[OBELISK] Skipping automated HuggingFace download. Use --force to overwrite.")
        sys.exit(0)
    
    print(f"[OBELISK] Core ML models are missing or forced overwrite requested.")
    print(f"[OBELISK] Connecting to HuggingFace ({repo_id}) to securely stream model topology...")
    
    os.makedirs(models_dir, exist_ok=True)
    
    try:
        snapshot_path = snapshot_download(
            repo_id=repo_id,
            repo_type="model",
            local_dir=models_dir,
            local_dir_use_symlinks=False,
            resume_download=True,
        )
        print("---------------------------------------------------------")
        print(f"[OBELISK] Payload successfully retrieved! Models deployed to: {snapshot_path}")
    except Exception as e:
        print(f"[OBELISK] FATAL: Failed to synchronise models from HuggingFace. Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download()
