"""
预约领域逻辑 - 核心业务规则（纯函数，便于测试）
"""

from datetime import datetime, timedelta
from typing import Optional


# ============================================================
# 桌位分配器 — 纯函数，适合 PBT
# ============================================================
def allocate_table(
    guest_count: int,
    available_tables: list[dict],
    prefer_window: bool = False,
    prefer_cat_friendly: bool = False,
) -> Optional[dict]:
    """
    根据人数和偏好分配最佳桌位。
    规则: 桌位容量必须 >= guest_count
          在满足条件的桌位中，优先选择 window > cat_friendly > 最小容量
    """
    if guest_count <= 0:
        raise ValueError("guest_count must be >= 1")

    candidates = [t for t in available_tables if t.get("capacity", 0) >= guest_count]
    if not candidates:
        return None

    # 排序：window 优先，cat_friendly 次之，按容量升序
    def sort_key(t):
        return (
            0 if t.get("area") == "window" and prefer_window else 1,
            0 if t.get("cat_friendly") and prefer_cat_friendly else 1,
            t.get("capacity", 999),
        )

    candidates.sort(key=sort_key)
    return candidates[0]


# ============================================================
# 预约冲突检测器 — 纯函数，适合 PBT
# ============================================================
def detect_conflict(
    requested_time: datetime,
    requested_duration_minutes: int,
    existing_reservations: list[dict],
    table_id: str,
    buffer_minutes: int = 15,
) -> tuple[bool, Optional[str]]:
    """
    检测预约时间冲突。
    返回 (has_conflict, conflict_detail)
    """
    if requested_duration_minutes <= 0:
        raise ValueError("duration must be positive")

    requested_end = requested_time + timedelta(minutes=requested_duration_minutes + buffer_minutes)

    for existing in existing_reservations:
        if existing.get("table_id") != table_id:
            continue
        if existing.get("status") in ("cancelled",):
            continue

        ex_start = existing.get("reservation_time")
        if not ex_start or isinstance(ex_start, str):
            continue

        ex_end = ex_start + timedelta(minutes=existing.get("duration_minutes", 120) + buffer_minutes)

        # 时间重叠检测
        if requested_time < ex_end and requested_end > ex_start:
            return True, f"与预约 {existing.get('id')} 时间冲突"
    return False, None


# ============================================================
# 取消策略 — 纯函数，适合 PBT
# ============================================================
def can_cancel(
    reservation_time: datetime,
    reference_time: Optional[datetime] = None,
    tier: str = "bronze",
) -> tuple[bool, Optional[str]]:
    """
    判断预约是否可以取消。
    - BRONZE: 提前2小时
    - SILVER: 提前1小时
    - GOLD: 提前30分钟
    - PLATINUM: 随时可取消
    """
    if reference_time is None:
        reference_time = datetime.utcnow()

    cancel_hours = {"bronze": 2.0, "silver": 1.0, "gold": 0.5, "platinum": 0.0}
    required_hours = cancel_hours.get(tier, 2.0)

    if required_hours == 0:
        return True, None

    hours_until = (reservation_time - reference_time).total_seconds() / 3600
    if hours_until < required_hours:
        return False, f"{tier}等级需提前{required_hours}小时取消，当前仅剩{hours_until:.1f}小时"
    return True, None


# ============================================================
# 价格计算器 — 纯函数，适合 PBT
# ============================================================
PRICE_PER_GUEST = 88  # 基础每人
PEAK_HOUR_MULTIPLIER = 1.3  # 高峰期加价
TIER_DISCOUNT = {
    "bronze": 1.0,
    "silver": 0.95,
    "gold": 0.88,
    "platinum": 0.80,
}


def calculate_price(
    guest_count: int,
    duration_hours: float,
    is_peak_hour: bool = False,
    tier: str = "bronze",
    extra_services: Optional[list[str]] = None,
) -> float:
    """
    计算预约总价。
    公式: guest_count * PRICE * peak_multiplier * tier_discount + extra_services
    """
    if guest_count <= 0 or guest_count > 20:
        raise ValueError("guest_count must be 1-20")
    if duration_hours <= 0 or duration_hours > 8:
        raise ValueError("duration_hours must be 0.5-8")

    base = guest_count * PRICE_PER_GUEST * duration_hours
    if is_peak_hour:
        base *= PEAK_HOUR_MULTIPLIER
    base *= TIER_DISCOUNT.get(tier, 1.0)

    extra_cost = 0.0
    if extra_services:
        SERVICE_PRICES = {"cat_treat": 30, "photo_package": 68, "birthday_setup": 128, "premium_tea": 58}
        for svc in extra_services:
            extra_cost += SERVICE_PRICES.get(svc, 0)

    return round(base + extra_cost, 2)


# ============================================================
# 时间槽生成器 — 纯函数，适合 PBT
# ============================================================
def generate_time_slots(
    opening_time: str = "10:00",
    closing_time: str = "22:00",
    slot_minutes: int = 60,
    date: Optional[str] = None,
) -> list[dict]:
    """
    生成可预约时间槽。
    """
    if slot_minutes <= 0:
        raise ValueError("slot_minutes must be positive")

    fmt = "%H:%M"
    open_t = datetime.strptime(opening_time, fmt)
    close_t = datetime.strptime(closing_time, fmt)

    slots = []
    current = open_t
    while current + timedelta(minutes=slot_minutes) <= close_t:
        end = current + timedelta(minutes=slot_minutes)
        slots.append({
            "start": current.strftime(fmt),
            "end": end.strftime(fmt),
            "available": True,
        })
        current = end
    return slots
