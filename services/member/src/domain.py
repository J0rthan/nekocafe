"""
会员领域逻辑 - 核心业务规则（纯函数，便于测试）
"""

import unicodedata
from datetime import datetime, date
from typing import Optional
from .models import MembershipTier


# ============================================================
# 积分计算器 — 纯函数，适合 PBT
# ============================================================
def calculate_points(guest_count: int, duration_hours: float, is_first_visit: bool) -> int:
    """
    根据消费计算积分。
    规则: 基础分 = guest_count * 10 + duration_hours * 5
          首访额外 +50
    最低 10 分，最高 5000 分
    """
    if guest_count <= 0:
        raise ValueError("guest_count must be >= 1")
    if duration_hours <= 0:
        raise ValueError("duration_hours must be >= 0.5")

    base = guest_count * 10 + int(duration_hours * 5)
    if is_first_visit:
        base += 50
    return max(10, min(5000, base))


# ============================================================
# 等级升级引擎 — 纯函数，适合 PBT
# ============================================================
TIER_THRESHOLDS = {
    MembershipTier.BRONZE: 0,
    MembershipTier.SILVER: 500,
    MembershipTier.GOLD: 2000,
    MembershipTier.PLATINUM: 5000,
}


def determine_tier(total_points: int) -> MembershipTier:
    """
    根据累计积分决定会员等级。
    BRONZE: 0-499
    SILVER: 500-1999
    GOLD: 2000-4999
    PLATINUM: 5000+
    """
    if total_points < 0:
        raise ValueError("total_points cannot be negative")
    if total_points >= 5000:
        return MembershipTier.PLATINUM
    if total_points >= 2000:
        return MembershipTier.GOLD
    if total_points >= 500:
        return MembershipTier.SILVER
    return MembershipTier.BRONZE


def should_upgrade(current_tier: MembershipTier, total_points: int) -> tuple[bool, Optional[MembershipTier]]:
    """
    判断是否可以升级。
    返回 (should_upgrade, new_tier)
    """
    target_tier = determine_tier(total_points)
    tier_order = ["bronze", "silver", "gold", "platinum"]
    current_idx = tier_order.index(current_tier.value)
    target_idx = tier_order.index(target_tier.value)
    if target_idx > current_idx:
        return True, target_tier
    return False, None


# ============================================================
# 手机号脱敏 — 纯函数，适合 PBT
# ============================================================
def mask_phone(phone: str) -> str:
    """
    手机号脱敏: 138****8001
    """
    if not phone or len(phone) < 7:
        raise ValueError("invalid phone number")
    return phone[:3] + "****" + phone[-4:]


# ============================================================
# 用户名验证 — 纯函数，适合 PBT
# ============================================================
def validate_display_name(name: str) -> tuple[bool, Optional[str]]:
    """
    验证显示名称。
    规则: 1-50字符，不能全为数字，不能包含特殊字符
    """
    if not name or len(name) > 50:
        return False, "名称长度必须在1-50字符之间"
    if name.isdigit():
        return False, "名称不能全为数字"
    # 允许中英文、空格、数字、常见标点
    for ch in name:
        cat = unicodedata.category(ch)
        if not (cat.startswith('L') or cat.startswith('N') or cat.startswith('Z') or cat in ('Pd', 'Po', 'Pc')):
            return False, "名称包含不允许的特殊字符"
    return True, None


# ============================================================
# 年龄计算（根据生日）— 纯函数，适合 PBT
# ============================================================
def calculate_age(birthday: date, reference_date: Optional[date] = None) -> int:
    """
    根据生日计算年龄。
    """
    if reference_date is None:
        reference_date = date.today()
    age = reference_date.year - birthday.year
    if (reference_date.month, reference_date.day) < (birthday.month, birthday.day):
        age -= 1
    return age
