#!/usr/bin/env python3
import os
import time
import json
import math
import requests
from typing import Dict, Any, List, Optional

# Load .env file automatically
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Get the Google API key from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Google Places API endpoints
TEXT_SEARCH_ENDPOINT = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_ENDPOINT = "https://maps.googleapis.com/maps/api/place/details/json"

def composite_score(rating: Optional[float], review_count: Optional[int]) -> float:
    r = rating or 0.0
    v = float(review_count or 0)
    return r * (1.0 + math.log10(1.0 + v))

def text_search_restaurants(city: str, api_key: str) -> List[Dict[str, Any]]:
    query = f"best food restaurants in {city}"
    params = {"query": query, "type": "restaurant", "key": api_key}
    try:
        resp = requests.get(TEXT_SEARCH_ENDPOINT, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
    except requests.RequestException as e:
        print(f"Failed to fetch restaurants for {city}: {e}")
        return []

def fetch_place_details(place_id: str, api_key: str) -> Dict[str, Any]:
    fields = [
        "name", "rating", "user_ratings_total", "formatted_address",
        "price_level", "url", "website", "reviews"
    ]
    params = {"place_id": place_id, "fields": ",".join(fields), "key": api_key}
    try:
        resp = requests.get(DETAILS_ENDPOINT, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("result", {}) if data.get("status") == "OK" else {}
    except requests.RequestException:
        return {}

def build_output(top_places: List[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for p in top_places:
        out[p.get("name", "Unknown")] = {
            "rating": p.get("rating"),
            "user_ratings_total": p.get("user_ratings_total"),
            "address": p.get("formatted_address"),
            "price_level": p.get("price_level"),
            "google_maps_url": p.get("url"),
            "website": p.get("website"),
            "review_snippets": [
                (rev.get("text") or "").strip()
                for rev in (p.get("reviews") or [])[:3]
                if isinstance(rev, dict)
            ],
        }
    return out

def main() -> None:
    if not GOOGLE_API_KEY:
        print("\nError: GOOGLE_API_KEY is not set.")
        print("To fix this, do one of the following:\n")
        print("1. Create a .env file in the same folder as this script with:")
        print("   GOOGLE_API_KEY=your_actual_api_key_here\n")
        print("OR\n")
        print("2. Set the environment variable in your terminal:")
        print("   export GOOGLE_API_KEY=\"your_actual_api_key_here\"")
        print("   source ~/.zshrc\n")
        print("You can also verify by running: echo $GOOGLE_API_KEY\n")
        return

    city = input("Enter a city name: ").strip()
    if not city:
        print("No city entered.")
        return

    print(f"\nSearching for top restaurants in {city}...\n")
    raw_results = text_search_restaurants(city, GOOGLE_API_KEY)

    if not raw_results:
        print("No results found.")
        return

    for p in raw_results:
        p["_score"] = composite_score(p.get("rating"), p.get("user_ratings_total"))

    sorted_places = sorted(raw_results, key=lambda d: d.get("_score", 0.0), reverse=True)
    top_candidates = sorted_places[:10]

    enriched: List[Dict[str, Any]] = []
    for p in top_candidates:
        details = fetch_place_details(p.get("place_id"), GOOGLE_API_KEY)
        if details:
            enriched.append({**p, **details})
        time.sleep(0.2)

    if not enriched:
        print("No detailed restaurant data could be retrieved.")
        return

    output_mapping = build_output(enriched)
    filename = f"top-10-restaurants-{city.replace(' ', '_').lower()}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output_mapping, f, ensure_ascii=False, indent=2)

    print(f"\nSaved Top 10 restaurants to {filename}\n")
    print(f"(Tip: to pretty-print the file, run: python3 -m json.tool {filename})\n")

    for i, p in enumerate(enriched, 1):
        print(f"{i}. {p.get('name')} — Rating: {p.get('rating')} ({p.get('user_ratings_total')} reviews)")

if __name__ == "__main__":
    main()