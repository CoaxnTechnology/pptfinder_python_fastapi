# app/routers/check_keyword.py

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any
import os
import urllib.parse

from app.database import get_db
from app.models import PPTData
from app.utils.google_search import fetch_ppt_results

router = APIRouter(prefix="", tags=["Check Keyword"])

STATIC_FOLDER = "static"


# =====================================================
# HELPERS
# =====================================================
def extract_thumbnail(pagemap: dict) -> str | None:
    if not pagemap:
        return None

    if "cse_thumbnail" in pagemap:
        thumbs = pagemap.get("cse_thumbnail", [])
        if thumbs:
            return thumbs[0].get("src")

    if "cse_image" in pagemap:
        images = pagemap.get("cse_image", [])
        if images:
            return images[0].get("src")

    return None


def normalize_thumbnail(path: str | None) -> str | None:
    if not path:
        return None

    if path.startswith("http"):
        return path

    return f"/serve_png/{os.path.basename(path)}"


def generate_description(item: dict, keyword: str) -> str:
    """
    Fallback description when Google snippet is missing
    """
    if item.get("snippet"):
        return item["snippet"]

    title = item.get("title", "PowerPoint Presentation")
    link = item.get("link", "")

    filename = os.path.basename(urllib.parse.urlparse(link).path)
    filename = filename.replace("-", " ").replace("_", " ").replace(".pptx", "").replace(".ppt", "")

    return f"{title} – Downloadable {keyword.title()} PowerPoint presentation ({filename})"


# =====================================================
# CHECK KEYWORD
# =====================================================
@router.get("/check_keyword", summary="Check or fetch PPT for a keyword")
def check_keyword(
    keyword: str = Query(...),
    db: Session = Depends(get_db)
):
    keyword = keyword.strip().lower()

    # ================= CACHE =================
    record = db.query(PPTData).filter(PPTData.keyword == keyword).first()

    if record:
        results = []
        for item in record.object:
            thumb = item.get("thumbnail") or extract_thumbnail(item.get("pagemap", {}))
            results.append({
                "title": item.get("title"),
                "snippet": item.get("snippet"),
                "description": generate_description(item, keyword),
                "link": item.get("link"),
                "thumbnail": normalize_thumbnail(thumb),
            })

        return {
            "exists": True,
            "keyword": keyword,
            "source": "cache",
            "count": len(results),
            "object": results,
        }

    # ================= GOOGLE =================
    google_results = fetch_ppt_results(keyword)

    if not google_results:
        return {
            "exists": False,
            "keyword": keyword,
            "source": "google",
            "count": 0,
            "object": [],
        }

    db_items = []
    response_items = []

    for item in google_results:
        thumb = item.get("thumbnail") or extract_thumbnail(item.get("pagemap", {}))
        description = generate_description(item, keyword)

        db_items.append({
            "title": item.get("title"),
            "snippet": item.get("snippet"),
            "description": description,
            "link": item.get("link"),
            "thumbnail": normalize_thumbnail(thumb),
            "pagemap": item.get("pagemap", {}),
        })

        response_items.append({
            "title": item.get("title"),
            "snippet": item.get("snippet"),
            "description": description,
            "link": item.get("link"),
            "thumbnail": normalize_thumbnail(thumb),
        })

    db.add(PPTData(
        keyword=keyword,
        object=db_items,
        created_at=datetime.utcnow()
    ))
    db.commit()

    return {
        "exists": True,
        "keyword": keyword,
        "source": "google",
        "count": len(response_items),
        "object": response_items,
    }


# =====================================================
# SERVE PNG
# =====================================================
@router.get("/serve_png/{filename}", response_class=FileResponse)
def serve_png(filename: str):
    if ".." in filename:
        raise HTTPException(404)

    path = os.path.join(STATIC_FOLDER, filename)
    if os.path.isfile(path):
        return FileResponse(path, media_type="image/png")

    raise HTTPException(404)
