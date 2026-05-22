"""
会员服务路由
"""

import uuid
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from .models import MemberCreate, MemberResponse, MemberUpdate, MembershipTier

router = APIRouter(prefix="/api/v1/members", tags=["members"])
logger = logging.getLogger("member")

_fake_db: dict = {}


@router.post("", response_model=MemberResponse, status_code=201)
async def create_member(data: MemberCreate):
    """注册会员"""
    member_id = str(uuid.uuid4())
    now = datetime.utcnow()
    member = MemberResponse(
        id=member_id,
        name=data.name,
        phone=data.phone,
        email=data.email,
        birthday=data.birthday,
        tier=MembershipTier.BRONZE,
        points=0,
        favorite_cat_breeds=data.favorite_cat_breeds or [],
        created_at=now,
        updated_at=now,
    )
    _fake_db[member_id] = member
    logger.info(f"Member created: {member_id}")
    return member


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(member_id: str):
    """查询会员详情"""
    if member_id not in _fake_db:
        raise HTTPException(status_code=404, detail="会员不存在")
    return _fake_db[member_id]


@router.patch("/{member_id}", response_model=MemberResponse)
async def update_member(member_id: str, data: MemberUpdate):
    """更新会员信息"""
    if member_id not in _fake_db:
        raise HTTPException(status_code=404, detail="会员不存在")
    member = _fake_db[member_id]
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(member, key, value)
    member.updated_at = datetime.utcnow()
    logger.info(f"Member updated: {member_id}")
    return member


@router.get("", response_model=List[MemberResponse])
async def list_members(
    tier: Optional[MembershipTier] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """查询会员列表"""
    results = list(_fake_db.values())
    if tier:
        results = [m for m in results if m.tier == tier]
    return results[:limit]


@router.get("/{member_id}/reservation-history")
async def get_reservation_history(member_id: str):
    """查询会员预约历史（调用预约服务）"""
    if member_id not in _fake_db:
        raise HTTPException(status_code=404, detail="会员不存在")
    return {
        "member_id": member_id,
        "total_reservations": 0,
        "reservations": [],
    }

# CI test
