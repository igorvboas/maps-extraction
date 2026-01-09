import subprocess
import sys
import json
import os
from app.models import SearchInput, Lead


async def scrape_google_maps(input: SearchInput) -> list[Lead]:
    """Run the scraper in a subprocess to avoid asyncio event loop conflicts."""
    
    # Get the path to the worker script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    worker_script = os.path.join(script_dir, "scraper_worker.py")
    
    try:
        # Pass all location parameters to the worker
        result = subprocess.run(
            [sys.executable, worker_script, input.query, input.city, input.state, input.country],
            capture_output=True,
            text=True,
            timeout=180,  # 3 minute timeout
            cwd=os.path.dirname(script_dir)
        )
        
        if result.returncode != 0:
            print(f"Scraper stderr: {result.stderr}")
            return []
        
        leads_data = json.loads(result.stdout)
        leads = [Lead(**data) for data in leads_data]
        return leads
        
    except subprocess.TimeoutExpired:
        print("Scraper timed out")
        return []
    except json.JSONDecodeError as e:
        print(f"Failed to parse scraper output: {e}")
        return []
    except Exception as e:
        print(f"Scraper error: {e}")
        return []
