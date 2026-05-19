"""
会员服务数据模型
"""

import enum
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class MembershipTier(str, enum.Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class MemberCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    email: Optional[str] = Field(None, max_length=100)
    birthday: Optional[date] = None
    favorite_cat_breeds: Optional[List[str]] = Field(default_factory=list)


class MemberResponse(BaseModel):
    id: str
    name: str
    phone: str
    email: Optional[str]
    birthday: Optional[date]
    tier: MembershipTier
    points: int
    favorite_cat_breeds: List[str]
    created_at: datetime
    updated_at: datetime


class MemberUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    birthday: Optional[date] = None
    favorite_cat_breeds: Optional[List[str]] = None
