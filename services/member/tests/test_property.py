"""
会员服务 - 基于属性的测试 (Property-Based Testing)
覆盖5个核心领域类/函数
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, Phase
from datetime import date, timedelta
from src.domain import (
    calculate_points,
    determine_tier,
    should_upgrade,
    mask_phone,
    validate_display_name,
    calculate_age,
    TIER_THRESHOLDS,
)
from src.models import MembershipTier


# ============================================================
# 1. calculate_points — PBT
# ============================================================
class TestCalculatePointsPBT:
    """积分计算器 PBT: 输出始终在 [10, 5000] 区间内"""

    @given(
        guest_count=st.integers(min_value=1, max_value=100),
        duration_hours=st.floats(min_value=0.5, max_value=24.0),
        is_first_visit=st.booleans(),
    )
    @settings(max_examples=200, phases=[Phase.generate, Phase.shrink])
    def test_points_always_in_range(self, guest_count, duration_hours, is_first_visit):
        result = calculate_points(guest_count, duration_hours, is_first_visit)
        assert 10 <= result <= 5000

    @given(
        guest_count=st.integers(min_value=1, max_value=50),
        duration_hours=st.floats(min_value=0.5, max_value=10.0),
    )
    @settings(max_examples=100)
    def test_first_visit_gives_more_or_equal_points(self, guest_count, duration_hours):
        regular = calculate_points(guest_count, duration_hours, False)
        first = calculate_points(guest_count, duration_hours, True)
        assert first >= regular

    @given(
        g1=st.integers(min_value=1, max_value=50),
        g2=st.integers(min_value=1, max_value=50),
        hours=st.floats(min_value=0.5, max_value=10.0),
    )
    @settings(max_examples=100)
    def test_more_guests_gives_more_points(self, g1, g2, hours):
        assume(g1 < g2)
        p1 = calculate_points(g1, hours, False)
        p2 = calculate_points(g2, hours, False)
        assert p2 >= p1


# ============================================================
# 2. determine_tier — PBT
# ============================================================
class TestDetermineTierPBT:
    """等级判断 PBT: 积分单调 → 等级单调"""

    @given(total_points=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=200)
    def test_tier_matches_thresholds(self, total_points):
        tier = determine_tier(total_points)
        if total_points >= 5000:
            assert tier == MembershipTier.PLATINUM
        elif total_points >= 2000:
            assert tier == MembershipTier.GOLD
        elif total_points >= 500:
            assert tier == MembershipTier.SILVER
        else:
            assert tier == MembershipTier.BRONZE

    @given(
        p1=st.integers(min_value=0, max_value=9000),
        delta=st.integers(min_value=0, max_value=1000),
    )
    @settings(max_examples=100)
    def test_more_points_never_lowers_tier(self, p1, delta):
        t1 = determine_tier(p1)
        t2 = determine_tier(p1 + delta)
        tier_order = ["bronze", "silver", "gold", "platinum"]
        assert tier_order.index(t2.value) >= tier_order.index(t1.value)

    @given(
        points=st.integers(min_value=0, max_value=10000),
        current_tier=st.sampled_from(list(MembershipTier)),
    )
    @settings(max_examples=100)
    def test_should_upgrade_consistency(self, points, current_tier):
        upgraded, new_tier = should_upgrade(current_tier, points)
        expected = determine_tier(points)
        if upgraded:
            assert new_tier is not None
            tier_order = ["bronze", "silver", "gold", "platinum"]
            assert tier_order.index(new_tier.value) > tier_order.index(current_tier.value)


# ============================================================
# 3. mask_phone — PBT
# ============================================================
class TestMaskPhonePBT:
    """手机号脱敏 PBT: 输出格式始终为 3+****+4"""

    @given(
        prefix=st.text(min_size=3, max_size=3, alphabet="0123456789"),
        suffix=st.text(min_size=4, max_size=4, alphabet="0123456789"),
    )
    @settings(max_examples=100)
    def test_mask_preserves_prefix_and_suffix(self, prefix, suffix):
        phone = prefix + "5678" + suffix[-4:]
        phone = phone[:11]  # 标准11位
        if len(phone) >= 7:
            result = mask_phone(phone)
            assert result[:3] == phone[:3]
            assert result[-4:] == phone[-4:]
            assert "****" in result

    @given(phone=st.text(min_size=7, max_size=15, alphabet="0123456789"))
    @settings(max_examples=100)
    def test_masked_shorter_than_original(self, phone):
        result = mask_phone(phone)
        assert len(result) >= len(phone) - 4  # **** 替代中间部分

    @given(phone=st.text(min_size=7, max_size=11, alphabet="0123456789"))
    @settings(max_examples=100)
    def test_masked_not_equal_original(self, phone):
        result = mask_phone(phone)
        assert result != phone  # 脱敏后一定不等


# ============================================================
# 4. validate_display_name — PBT
# ============================================================
class TestValidateDisplayNamePBT:
    """名称验证 PBT"""

    @given(
        name=st.text(
            alphabet=st.characters(
                whitelist_categories=["L", "N", "Zs"],
                whitelist_characters=["·"],
            ),
            min_size=1,
            max_size=30,
        )
    )
    @settings(max_examples=100)
    def test_alphanumeric_names_are_valid(self, name):
        name = name.strip()
        assume(len(name) > 0 and not name.isdigit() and len(name) <= 50)
        valid, _ = validate_display_name(name)
        assert valid

    @given(name=st.text(min_size=51))
    @settings(max_examples=50)
    def test_too_long_names_are_invalid(self, name):
        valid, msg = validate_display_name(name)
        assert not valid

    @given(name=st.text(min_size=1, max_size=10, alphabet="0123456789"))
    @settings(max_examples=30)
    def test_digit_only_names_are_invalid(self, name):
        assume(len(name) > 0)
        valid, _ = validate_display_name(name)
        assert not valid


# ============================================================
# 5. calculate_age — PBT
# ============================================================
class TestCalculateAgePBT:
    """年龄计算 PBT"""

    @given(
        days_ago=st.integers(min_value=0, max_value=36500),
    )
    @settings(max_examples=100)
    def test_age_increases_with_time(self, days_ago):
        today = date.today()
        birthday = today - timedelta(days=days_ago)
        if birthday > today.replace(year=today.year - 150):
            age = calculate_age(birthday, today)
            next_year = calculate_age(birthday, today.replace(year=today.year + 1))
            assert next_year >= age

    @given(days_ago=st.integers(min_value=365, max_value=36500))
    @settings(max_examples=100)
    def test_age_at_least_zero(self, days_ago):
        today = date.today()
        birthday = today - timedelta(days=days_ago)
        age = calculate_age(birthday, today)
        assert age >= 0
