from pydantic import BaseModel, EmailStr
from typing import Any, List, Optional

# =====================================================
# CHECK KEYWORD API
# =====================================================

class CheckKeywordRequest(BaseModel):
    keyword: str


class CheckKeywordResponse(BaseModel):
    exists: bool
    object: Optional[Any] = None

    model_config = {
        "from_attributes": True
    }


# =====================================================
# SAVE DATA API
# =====================================================

class SaveDataItem(BaseModel):
    title: Optional[str] = None
    link: Optional[str] = None
    displayLink: Optional[str] = None
    mime: Optional[str] = None
    fileFormat: Optional[str] = None
    snippet: Optional[str] = None


class SaveDataRequest(BaseModel):
    keyword: str
    results: List[SaveDataItem]


class SaveDataResponse(BaseModel):
    message: str
    saved: bool


# =====================================================
# CATEGORY API
# =====================================================

class CategoryItem(BaseModel):
    id: int
    category: str


class CategoryResponse(BaseModel):
    status: str
    data: List[CategoryItem]
