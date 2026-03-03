from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

from app.database import get_db
from app.models import PPTData
from app.schemas import SaveDataRequest,SaveDataResponse

router = APIRouter(prefix="", tags=["Save Data"])


# ----------------------------
# API Endpoint
# ----------------------------
@router.post("/save_data", response_model=SaveDataResponse)
def save_data(payload: SaveDataRequest, db: Session = Depends(get_db)):

    try:
        # Check if record exists
        record = db.query(PPTData).filter(PPTData.keyword == payload.keyword).first()

        if record:
            record.object = payload.object
            record.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(record)

            return SaveDataResponse(
                saved=True,
                message="Updated successfully",
                keyword=record.keyword,
                object=record.object
            )

        # Insert new record
        new_record = PPTData(
            keyword=payload.keyword,
            object=payload.object,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(new_record)
        db.commit()
        db.refresh(new_record)

        return SaveDataResponse(
            saved=True,
            message="Inserted successfully",
            keyword=new_record.keyword,
            object=new_record.object
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
