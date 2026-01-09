"""
Standalone Playwright scraper script.
This runs in its own subprocess to avoid asyncio event loop conflicts.
"""
import sys
import json
import os
import re
import urllib.request
import urllib.parse

# Get the project root to fix imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from playwright.sync_api import sync_playwright

HEADLESS = os.getenv("HEADLESS", "True").lower() == "true"


def get_coordinates_from_nominatim(city: str, state: str, country: str) -> dict | None:
    """Get coordinates from Nominatim (OpenStreetMap) API for any location."""
    try:
        query = f"{city}, {state}, {country}"
        encoded_query = urllib.parse.quote(query)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded_query}&format=json&limit=1"
        
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "GoogleMapsScraperAPI/1.0"}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data and len(data) > 0:
                return {
                    "latitude": float(data[0]["lat"]),
                    "longitude": float(data[0]["lon"])
                }
    except Exception as e:
        print(f"Nominatim error: {e}", file=sys.stderr)
    
    return None


def extract_phone(text: str) -> str | None:
    """Extract phone number from text using regex patterns."""
    patterns = [
        r'\+?\d{2,3}[\s\-]?\(?\d{2,3}\)?[\s\-]?\d{4,5}[\s\-]?\d{4}',
        r'\(?\d{2,3}\)?[\s\-]?\d{4,5}[\s\-]?\d{4}',
        r'\d{10,11}',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def scrape(query: str, city: str, state: str, country: str) -> list[dict]:
    """Scrape Google Maps for leads with dynamic geolocation."""
    leads_data = []
    
    # Get coordinates dynamically
    coords = get_coordinates_from_nominatim(city, state, country)
    if not coords:
        print(f"Could not get coordinates for {city}, {state}, {country}", file=sys.stderr)
        # Default to São Paulo if geocoding fails
        coords = {"latitude": -23.5505, "longitude": -46.6333}
    
    print(f"Using coordinates: {coords}", file=sys.stderr)
    
    # Build URL with coordinates to force viewport
    search_term = f"{query} em {city}, {state}"
    encoded_search = urllib.parse.quote(search_term)
    
    # Use @lat,lng,zoom format to center the map
    url = f"https://www.google.com/maps/search/{encoded_search}/@{coords['latitude']},{coords['longitude']},14z?hl=pt-BR"
    
    print(f"URL: {url}", file=sys.stderr)
    
    with sync_playwright() as p:
        # Argumentos extras necessários para rodar em containers Docker
        browser = p.chromium.launch(
            headless=HEADLESS,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',  # Evita problemas de memória compartilhada em containers
                '--disable-gpu',
                '--disable-software-rasterizer'
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            geolocation=coords,
            permissions=["geolocation"],
            locale="pt-BR"
        )
        
        page = context.new_page()
        
        try:
            print(f"[LOG] Abrindo URL...", file=sys.stderr)
            page.goto(url, timeout=60000)
            print(f"[LOG] Página carregada com sucesso", file=sys.stderr)
            
            # Wait for results to load
            try:
                print(f"[LOG] Aguardando feed de resultados...", file=sys.stderr)
                page.wait_for_selector('div[role="feed"]', timeout=20000)
                print(f"[LOG] Feed encontrado", file=sys.stderr)
            except:
                try:
                    print(f"[LOG] Feed não encontrado, tentando seletor alternativo...", file=sys.stderr)
                    page.wait_for_selector('a[href*="/maps/place/"]', timeout=10000)
                except:
                    print(f"[LOG] Nenhum resultado encontrado", file=sys.stderr)
                    browser.close()
                    return []

            # Scroll to load more results
            print(f"[LOG] Fazendo scroll para carregar mais resultados...", file=sys.stderr)
            try:
                feed = page.locator('div[role="feed"]')
                if feed.count() > 0:
                    for scroll_num in range(10):  # More scrolls for 400 items
                        feed.evaluate("el => el.scrollTop = el.scrollHeight")
                        page.wait_for_timeout(1500)
                        current_cards = page.locator('a[href*="/maps/place/"]').count()
                        print(f"[LOG] Scroll {scroll_num + 1}/10 - Cards carregados: {current_cards}", file=sys.stderr)
            except Exception as e:
                print(f"[LOG] Erro no scroll: {e}", file=sys.stderr)

            # Find all result cards
            cards = page.locator('a[href*="/maps/place/"]').all()
            print(f"Found {len(cards)} cards", file=sys.stderr)
            
            seen_names = set()
            target_location = city.lower()
            
            for i, card in enumerate(cards[:200]):
                try:
                    aria_label = card.get_attribute("aria-label")
                    if not aria_label or aria_label in seen_names:
                        continue
                    seen_names.add(aria_label)
                    
                    print(f"[LOG] Processando {i + 1}/{min(len(cards), 200)}: {aria_label[:50]}...", file=sys.stderr)
                    name = aria_label
                    category = ""
                    phone = None
                    address = None
                    
                    card.click()
                    page.wait_for_timeout(2500)
                    
                    # Extract category
                    try:
                        cat_btn = page.locator('button[jsaction*="category"]').first
                        if cat_btn.count() > 0:
                            category = cat_btn.inner_text()
                        else:
                            cat_el = page.locator('.DkEaL').first
                            if cat_el.count() > 0:
                                category = cat_el.inner_text()
                    except:
                        pass
                    
                    # Extract phone
                    try:
                        phone_btn = page.locator('button[data-item-id*="phone"]').first
                        if phone_btn.count() > 0:
                            phone_text = phone_btn.get_attribute("aria-label") or phone_btn.inner_text()
                            phone = phone_text.replace("Phone:", "").replace("Telefone:", "").strip()
                    except:
                        pass
                    
                    if not phone:
                        try:
                            info_items = page.locator('.Io6YTe.fontBodyMedium').all_inner_texts()
                            for item in info_items:
                                extracted = extract_phone(item)
                                if extracted:
                                    phone = extracted
                                    break
                        except:
                            pass
                    
                    # Extract address
                    try:
                        addr_btn = page.locator('button[data-item-id="address"]').first
                        if addr_btn.count() > 0:
                            address = addr_btn.get_attribute("aria-label") or addr_btn.inner_text()
                            address = address.replace("Address:", "").replace("Endereço:", "").strip()
                    except:
                        pass
                    
                    if not address:
                        try:
                            addr_el = page.locator('[data-item-id="address"] .Io6YTe').first
                            if addr_el.count() > 0:
                                address = addr_el.inner_text()
                        except:
                            pass
                    
                    # Filter: only include results from the target location
                    if address:
                        addr_lower = address.lower()
                        # Check if address contains the target city or state
                        if target_location in addr_lower or state.lower() in addr_lower:
                            leads_data.append({
                                "name": name,
                                "category": category,
                                "phone": phone,
                                "address": address,
                                "url": None
                            })
                            print(f"[LOG] ✓ Lead adicionado: {name[:40]} | Tel: {phone or 'N/A'} | Total: {len(leads_data)}", file=sys.stderr)
                        else:
                            print(f"[LOG] ✗ Ignorado (fora da localização): {name[:40]}", file=sys.stderr)
                        # If no address, include anyway but it might be filtered later
                        leads_data.append({
                            "name": name,
                            "category": category,
                            "phone": phone,
                            "address": address,
                            "url": None
                        })
                    
                except Exception as e:
                    print(f"Error on card {i}: {e}", file=sys.stderr)
                    continue

        except Exception as e:
            print(f"[LOG] ERRO GLOBAL: {e}", file=sys.stderr)
        finally:
            print(f"[LOG] Finalizando... Total de leads extraídos: {len(leads_data)}", file=sys.stderr)
            browser.close()
            
    return leads_data


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(json.dumps([]))
        sys.exit(0)
    
    query = sys.argv[1]
    city = sys.argv[2]
    state = sys.argv[3]
    country = sys.argv[4]
    
    results = scrape(query, city, state, country)
    print(json.dumps(results, ensure_ascii=False))
