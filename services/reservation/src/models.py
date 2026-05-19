"""
预约服务数据模型
"""

import enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ReservationStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class ReservationCreate(BaseModel):
    customer_id: str = Field(..., description="会员ID")
    store_id: str = Field(..., description="门店ID")
    table_id: str = Field(..., description="桌位ID")
    reservation_time: datetime = Field(..., description="预约时间")
    guest_count: int = Field(ge=1, le=20, description="用餐人数")
    notes: Optional[str] = Field(None, max_length=500)


class ReservationResponse(BaseModel):
    id: str
    customer_id: str
    store_id: str
    table_id: str
    reservation_time: datetime
    guest_count: int
    status: ReservationStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class TableInfo(BaseModel):
    id: str
    store_id: str
    table_number: str
    capacity: int
    is_available: bool
    area: Optional[str] = None
    cat_friendly: bool = False
