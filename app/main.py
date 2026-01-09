import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from app.models import SearchInput, Lead
from app.scraper import scrape_google_maps

# Load environment variables from .env file
load_dotenv()

# API Key configuration
API_KEY = os.getenv("API_KEY", "")
API_KEY_NAME = "X-API-Key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Validate the API key from the request header."""
    if not api_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API Key is missing. Please provide 'X-API-Key' header."
        )
    if api_key != API_KEY:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Invalid API Key."
        )
    return api_key

app = FastAPI(title="Google Maps Leads Scraper API")

@app.post("/search", response_model=list[Lead])
async def search_leads(input: SearchInput, api_key: str = Depends(verify_api_key)):
    """
    Search for leads on Google Maps based on city, state, country and query.
    
    Requires X-API-Key header for authentication.
    """
    try:
        leads = await scrape_google_maps(input)
        if not leads:
             # Depending on requirement, might return empty list or 404. 
             # Use empty list allows client to handle "no results" gracefully.
             return []
        return leads
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Google Maps Scraper API is running. Use POST /search to find leads."}
