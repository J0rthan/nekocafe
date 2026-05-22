"""
会员服务 - 领域逻辑单元测试（针对性覆盖）
用于提升变异测试分数
"""

import pytest
from datetime import date, datetime
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


class TestCalculatePointsUnit:
    """积分计算 - 全覆盖"""

    def test_min_points_clamped(self):
        # 1*10 + int(0.5*5) = 12, well above min of 10
        # With tiny values, result should be clamped to 10
        assert calculate_points(1, 0.1, False) == 10

    def test_max_points_clamped(self):
        assert calculate_points(500, 100, True) == 5000

    def test_first_visit_bonus(self):
        normal = calculate_points(5, 2.0, False)
        first = calculate_points(5, 2.0, True)
        assert first == normal + 50

    def test_guest_count_zero_raises(self):
        with pytest.raises(ValueError):
            calculate_points(0, 1.0, False)

    def test_duration_zero_raises(self):
        with pytest.raises(ValueError):
            calculate_points(1, 0, False)

    def test_negative_duration_raises(self):
        with pytest.raises(ValueError):
            calculate_points(1, -1.0, False)

    def test_typical_calculation(self):
        # 2人 * 10 + 3h * 5 = 20 + 15 = 35
        assert calculate_points(2, 3.0, False) == 35


class TestDetermineTierUnit:
    """等级判断 - 全覆盖"""

    def test_bronze_at_zero(self):
        assert determine_tier(0) == MembershipTier.BRONZE

    def test_bronze_at_499(self):
        assert determine_tier(499) == MembershipTier.BRONZE

    def test_silver_at_500(self):
        assert determine_tier(500) == MembershipTier.SILVER

    def test_silver_at_1999(self):
        assert determine_tier(1999) == MembershipTier.SILVER

    def test_gold_at_2000(self):
        assert determine_tier(2000) == MembershipTier.GOLD

    def test_gold_at_4999(self):
        assert determine_tier(4999) == MembershipTier.GOLD

    def test_platinum_at_5000(self):
        assert determine_tier(5000) == MembershipTier.PLATINUM

    def test_platinum_at_10000(self):
        assert determine_tier(10000) == MembershipTier.PLATINUM

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            determine_tier(-1)

    def test_upgrade_bronze_to_silver(self):
        upgraded, tier = should_upgrade(MembershipTier.BRONZE, 600)
        assert upgraded
        assert tier == MembershipTier.SILVER

    def test_no_upgrade_when_same(self):
        upgraded, tier = should_upgrade(MembershipTier.SILVER, 600)
        assert not upgraded

    def test_no_upgrade_when_lower(self):
        upgraded, tier = should_upgrade(MembershipTier.GOLD, 600)
        assert not upgraded

    def test_skip_multiple_tiers(self):
        upgraded, tier = should_upgrade(MembershipTier.BRONZE, 6000)
        assert upgraded
        assert tier == MembershipTier.PLATINUM


class TestMaskPhoneUnit:
    """手机号脱敏 - 全覆盖"""

    def test_standard_11_digit(self):
        result = mask_phone("13800138001")
        assert result == "138****8001"

    def test_7_digit_minimum(self):
        result = mask_phone("1234567")
        assert result == "123****4567"
        assert len(result) == 11

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            mask_phone("")

    def test_too_short_raises(self):
        with pytest.raises(ValueError):
            mask_phone("12345")


class TestValidateDisplayNameUnit:
    """名称验证 - 全覆盖"""

    def test_valid_chinese_name(self):
        valid, msg = validate_display_name("张三")
        assert valid

    def test_valid_english_name(self):
        valid, msg = validate_display_name("John")
        assert valid

    def test_valid_mixed(self):
        valid, msg = validate_display_name("猫咪Lover123")
        assert valid

    def test_empty_name(self):
        valid, msg = validate_display_name("")
        assert not valid

    def test_too_long_name(self):
        valid, msg = validate_display_name("a" * 51)
        assert not valid

    def test_digit_only(self):
        valid, msg = validate_display_name("12345")
        assert not valid

    def test_only_spaces(self):
        valid, msg = validate_display_name("   ")
        assert valid  # spaces are in allowed categories


class TestCalculateAgeUnit:
    """年龄计算 - 全覆盖"""

    def test_exact_birthday_today(self):
        today = date.today()
        age = calculate_age(date(today.year - 20, today.month, today.day))
        assert age == 20

    def test_birthday_yesterday(self):
        today = date.today()
        yesterday = date.today()
        # Use a date where birthday just passed
        birthday = date(2000, 1, 1)
        # reference date after birthday
        age = calculate_age(birthday, date(2026, 6, 15))
        assert age == 26

    def test_birthday_not_yet_this_year(self):
        birthday = date(2000, 12, 31)
        age = calculate_age(birthday, date(2026, 6, 15))
        assert age == 25  # hasn't had birthday yet in 2026

    def test_newborn(self):
        today = date.today()
        age = calculate_age(today, today)
        assert age == 0
