from app.models import SearchInput
import urllib.parse

def build_maps_url(input: SearchInput) -> str:
    # Build the search query with location
    # Format: "pizzaria em São Paulo, SP, Brasil"
    search_term = f"{input.query} em {input.city}, {input.state}, {input.country}"
    
    # Use the Google Maps search URL format
    # This format is more reliable for location-based searches
    encoded_search = urllib.parse.quote(search_term)
    
    url = f"https://www.google.com/maps/search/{encoded_search}?hl=pt-BR"
    return url
