"""
预约服务 - 领域逻辑单元测试（针对性覆盖）
用于提升变异测试分数
"""

import pytest
from datetime import datetime, timedelta
from src.domain import (
    allocate_table,
    detect_conflict,
    can_cancel,
    calculate_price,
    generate_time_slots,
)


class TestAllocateTableUnit:
    """桌位分配 - 全覆盖"""

    def test_exact_capacity_match(self):
        tables = [
            {"id": "t1", "capacity": 4, "area": "center", "cat_friendly": False},
            {"id": "t2", "capacity": 6, "area": "window", "cat_friendly": True},
        ]
        result = allocate_table(4, tables)
        assert result["id"] == "t1"

    def test_window_preference(self):
        tables = [
            {"id": "t1", "capacity": 10, "area": "center", "cat_friendly": False},
            {"id": "t2", "capacity": 10, "area": "window", "cat_friendly": False},
        ]
        result = allocate_table(6, tables, prefer_window=True)
        assert result["area"] == "window"

    def test_cat_friendly_preference(self):
        tables = [
            {"id": "t1", "capacity": 10, "area": "center", "cat_friendly": False},
            {"id": "t2", "capacity": 10, "area": "center", "cat_friendly": True},
        ]
        result = allocate_table(6, tables, prefer_cat_friendly=True)
        assert result["cat_friendly"]

    def test_no_suitable_table(self):
        tables = [{"id": "t1", "capacity": 2}]
        result = allocate_table(10, tables)
        assert result is None

    def test_empty_table_list(self):
        result = allocate_table(2, [])
        assert result is None

    def test_zero_guests_raises(self):
        with pytest.raises(ValueError):
            allocate_table(0, [{"id": "t1", "capacity": 4}])

    def test_negative_guests_raises(self):
        with pytest.raises(ValueError):
            allocate_table(-1, [{"id": "t1", "capacity": 4}])

    def test_single_table_fits(self):
        result = allocate_table(2, [{"id": "only", "capacity": 4}])
        assert result is not None
        assert result["id"] == "only"


class TestDetectConflictUnit:
    """冲突检测 - 全覆盖"""

    def test_exact_overlap(self):
        base = datetime(2026, 6, 15, 18, 0, 0)
        existing = [{
            "id": "r1", "table_id": "t1",
            "reservation_time": base, "duration_minutes": 120,
            "status": "confirmed",
        }]
        has, msg = detect_conflict(base, 60, existing, "t1")
        assert has

    def test_no_overlap_different_table(self):
        base = datetime(2026, 6, 15, 18, 0, 0)
        existing = [{
            "id": "r1", "table_id": "t1",
            "reservation_time": base, "duration_minutes": 120,
            "status": "confirmed",
        }]
        has, msg = detect_conflict(base, 60, existing, "t2")
        assert not has

    def test_back_to_back_no_conflict(self):
        base = datetime(2026, 6, 15, 18, 0, 0)
        existing = [{
            "id": "r1", "table_id": "t1",
            "reservation_time": base, "duration_minutes": 60,
            "status": "confirmed",
        }]
        # 下一场在 60+15 分钟后
        next_time = base + timedelta(minutes=75)
        has, msg = detect_conflict(next_time, 60, existing, "t1")
        assert not has

    def test_cancelled_ignored(self):
        base = datetime(2026, 6, 15, 18, 0, 0)
        existing = [{
            "id": "r1", "table_id": "t1",
            "reservation_time": base, "duration_minutes": 120,
            "status": "cancelled",
        }]
        has, msg = detect_conflict(base, 60, existing, "t1")
        assert not has

    def test_zero_duration_raises(self):
        with pytest.raises(ValueError):
            detect_conflict(datetime(2026, 6, 15, 18, 0, 0), 0, [], "t1")

    def test_empty_existing_no_conflict(self):
        has, msg = detect_conflict(datetime(2026, 6, 15, 18, 0, 0), 60, [], "t1")
        assert not has


class TestCanCancelUnit:
    """取消策略 - 全覆盖"""

    def test_bronze_2h_rule_within_window(self):
        now = datetime(2026, 6, 15, 10, 0, 0)
        res = now + timedelta(hours=5)
        can, msg = can_cancel(res, now, "bronze")
        assert can

    def test_bronze_2h_rule_outside_window(self):
        now = datetime(2026, 6, 15, 10, 0, 0)
        res = now + timedelta(hours=1)
        can, msg = can_cancel(res, now, "bronze")
        assert not can

    def test_silver_1h_rule(self):
        now = datetime(2026, 6, 15, 10, 0, 0)
        res = now + timedelta(hours=2)
        can, msg = can_cancel(res, now, "silver")
        assert can

        res2 = now + timedelta(minutes=30)
        can2, _ = can_cancel(res2, now, "silver")
        assert not can2

    def test_gold_30min_rule(self):
        now = datetime(2026, 6, 15, 10, 0, 0)
        res = now + timedelta(hours=1)
        can, msg = can_cancel(res, now, "gold")
        assert can

        res2 = now + timedelta(minutes=15)
        can2, _ = can_cancel(res2, now, "gold")
        assert not can2

    def test_platinum_always(self):
        now = datetime(2026, 6, 15, 10, 0, 0)
        res = now + timedelta(minutes=1)
        can, msg = can_cancel(res, now, "platinum")
        assert can

    def test_unknown_tier_defaults_to_bronze(self):
        now = datetime(2026, 6, 15, 10, 0, 0)
        res = now + timedelta(hours=3)
        can, msg = can_cancel(res, now, "unknown")
        assert can


class TestCalculatePriceUnit:
    """价格计算 - 全覆盖"""

    def test_base_price(self):
        # 2人 * 88 * 1h = 176
        assert calculate_price(2, 1.0, False, "bronze") == 176.0

    def test_peak_multiplier(self):
        off_peak = calculate_price(2, 1.0, False, "bronze")
        on_peak = calculate_price(2, 1.0, True, "bronze")
        assert on_peak == round(off_peak * 1.3, 2)

    def test_platinum_discount(self):
        bronze = calculate_price(2, 1.0, False, "bronze")
        platinum = calculate_price(2, 1.0, False, "platinum")
        assert platinum == round(bronze * 0.8, 2)

    def test_gold_discount(self):
        gold = calculate_price(2, 1.0, False, "gold")
        assert gold == round(176 * 0.88, 2)

    def test_extra_services(self):
        base = calculate_price(2, 1.0, False, "bronze")
        with_extra = calculate_price(2, 1.0, False, "bronze", ["cat_treat", "birthday_setup"])
        assert with_extra == base + 30 + 128

    def test_zero_guest_raises(self):
        with pytest.raises(ValueError):
            calculate_price(0, 1.0)

    def test_over_20_guests_raises(self):
        with pytest.raises(ValueError):
            calculate_price(21, 1.0)

    def test_zero_duration_raises(self):
        with pytest.raises(ValueError):
            calculate_price(2, 0)

    def test_over_8h_duration_raises(self):
        with pytest.raises(ValueError):
            calculate_price(2, 10)

    def test_duration_multiplier(self):
        p1 = calculate_price(2, 1.0)
        p2 = calculate_price(2, 2.0)
        assert p2 == p1 * 2


class TestGenerateTimeSlotsUnit:
    """时间槽生成 - 全覆盖"""

    def test_default_slots(self):
        slots = generate_time_slots()
        assert len(slots) == 12  # 10:00-22:00, 60min slots
        assert slots[0]["start"] == "10:00"
        assert slots[-1]["end"] == "22:00"

    def test_30min_slots(self):
        slots = generate_time_slots(slot_minutes=30)
        assert len(slots) == 24  # 12h * 2

    def test_120min_slots(self):
        slots = generate_time_slots(slot_minutes=120)
        assert len(slots) == 6

    def test_slots_are_contiguous(self):
        slots = generate_time_slots()
        for i in range(len(slots) - 1):
            assert slots[i]["end"] == slots[i + 1]["start"]

    def test_custom_hours(self):
        slots = generate_time_slots("08:00", "12:00", 60)
        assert len(slots) == 4

    def test_zero_slot_minutes_raises(self):
        with pytest.raises(ValueError):
            generate_time_slots(slot_minutes=0)

    def test_all_slots_available(self):
        slots = generate_time_slots()
        for s in slots:
            assert s["available"] is True
