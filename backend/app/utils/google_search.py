import requests
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")


def extract_thumbnail(pagemap: dict) -> Optional[str]:
    """Extract thumbnail URL from Google pagemap."""
    if not pagemap:
        return None

    try:
        thumbs = pagemap.get("cse_thumbnail")
        if isinstance(thumbs, list) and thumbs:
            return thumbs[0].get("src")

        images = pagemap.get("cse_image")
        if isinstance(images, list) and images:
            return images[0].get("src")
    except Exception:
        pass

    return None


def fetch_ppt_results(keyword: str) -> List[Dict]:
    """
    Fetch PPT / PPTX results from Google Custom Search.

    ✔ description = Google snippet ONLY
    ✔ No fake or generated text
    ✔ Clean & deduplicated results
    """

    if not GOOGLE_API_KEY or not SEARCH_ENGINE_ID:
        raise RuntimeError("Google API not configured")

    results: List[Dict] = []
    seen_links = set()
    start_index = 1

    while True:
        url = (
            "https://www.googleapis.com/customsearch/v1"
            f"?key={GOOGLE_API_KEY}"
            f"&cx={SEARCH_ENGINE_ID}"
            f"&q={keyword} filetype:ppt OR filetype:pptx"
            f"&start={start_index}"
            f"&safe=active"
        )

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"[ERROR] Google request failed: {e}")
            break

        items = data.get("items", [])
        if not items:
            break

        for item in items:
            link = item.get("link", "").strip()

            # Allow only PPT / PPTX / Google Drive files
            if not (
                link.lower().endswith((".ppt", ".pptx"))
                or "drive.google.com" in link
            ):
                continue

            if link in seen_links:
                continue
            seen_links.add(link)

            pagemap = item.get("pagemap", {})
            thumbnail = extract_thumbnail(pagemap)

            snippet = item.get("snippet") or None

            results.append({
                "title": item.get("title"),
                "snippet": snippet,        
                "description": snippet,    
                "link": link,
                "thumbnail": thumbnail,
                "pagemap": pagemap,
            })

        # Pagination
        next_page = data.get("queries", {}).get("nextPage")
        if not next_page:
            break

        start_index += 10

    print(f"[INFO] Google fetched {len(results)} results for '{keyword}'")
    return results
