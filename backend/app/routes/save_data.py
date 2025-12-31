from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.database import get_db
from app.models import PPTData

router = APIRouter(prefix="", tags=["Save Data"])


@router.post("/save_data")
def save_data(keyword: str, object: str, db: Session = Depends(get_db)):

    try:
        object_data = json.loads(object)
    except:
        return JSONResponse(
            content={"error": "Invalid JSON in 'object'"},
            status_code=400
        )

    # Check keyword exists
    record = db.query(PPTData).filter(PPTData.keyword == keyword).first()

    if record:
        record.object = object_data
        record.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(record)

        return {"saved": True, "message": "Updated successfully"}

    new_record = PPTData(
        keyword=keyword,
        object=object_data,
        created_at=datetime.utcnow()
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return {"saved": True, "message": "Inserted successfully"}
