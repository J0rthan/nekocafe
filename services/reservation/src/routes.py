"""
预约服务路由
"""
import uuid
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from .models import ReservationCreate, ReservationResponse, TableInfo, ReservationStatus

router = APIRouter(prefix="/api/v1/reservations", tags=["reservations"])
logger = logging.getLogger("reservation")

# 模拟数据存储（实际使用 PostgreSQL）
_fake_db: dict = {}
_fake_tables: dict = {}


@router.get("/tables", response_model=List[TableInfo])
async def list_tables(store_id: Optional[str] = Query(None), available_only: bool = Query(False)):
    """查询可用桌位"""
    tables = [
        TableInfo(
            id=f"tbl-{i:03d}",
            store_id=store_id or "store-001",
            table_number=f"A-{i:02d}",
            capacity=2 + (i % 6),
            is_available=(i % 3 != 0),
            area="window" if i % 2 == 0 else "center",
            cat_friendly=(i % 2 == 0),
        )
        for i in range(1, 11)
    ]
    if store_id:
        tables = [t for t in tables if t.store_id == store_id]
    if available_only:
        tables = [t for t in tables if t.is_available]
    return tables


@router.post("", response_model=ReservationResponse, status_code=201)
async def create_reservation(data: ReservationCreate):
    """创建预约"""
    reservation_id = str(uuid.uuid4())
    now = datetime.utcnow()
    reservation = ReservationResponse(
        id=reservation_id,
        customer_id=data.customer_id,
        store_id=data.store_id,
        table_id=data.table_id,
        reservation_time=data.reservation_time,
        guest_count=data.guest_count,
        status=ReservationStatus.PENDING,
        notes=data.notes,
        created_at=now,
        updated_at=now,
    )
    _fake_db[reservation_id] = reservation
    logger.info(f"Reservation created: {reservation_id}")
    return reservation


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(reservation_id: str):
    """查询预约详情"""
    if reservation_id not in _fake_db:
        raise HTTPException(status_code=404, detail="预约不存在")
    return _fake_db[reservation_id]


@router.patch("/{reservation_id}/cancel", response_model=ReservationResponse)
async def cancel_reservation(reservation_id: str):
    """取消预约"""
    if reservation_id not in _fake_db:
        raise HTTPException(status_code=404, detail="预约不存在")
    reservation = _fake_db[reservation_id]
    if reservation.status == ReservationStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="预约已取消")
    reservation.status = ReservationStatus.CANCELLED
    reservation.updated_at = datetime.utcnow()
    logger.info(f"Reservation cancelled: {reservation_id}")
    return reservation


@router.get("", response_model=List[ReservationResponse])
async def list_reservations(
    customer_id: Optional[str] = Query(None),
    status: Optional[ReservationStatus] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """查询预约列表"""
    results = list(_fake_db.values())
    if customer_id:
        results = [r for r in results if r.customer_id == customer_id]
    if status:
        results = [r for r in results if r.status == status]
    return results[:limit]
