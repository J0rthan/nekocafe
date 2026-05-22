"""
预约服务 - 基于属性的测试 (Property-Based Testing)
覆盖5个核心领域函数
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, Phase
from datetime import datetime, timedelta
from src.domain import (
    allocate_table,
    detect_conflict,
    can_cancel,
    calculate_price,
    generate_time_slots,
)


# ============================================================
# 1. allocate_table — PBT
# ============================================================
class TestAllocateTablePBT:
    """桌位分配 PBT"""

    @given(
        guest_count=st.integers(min_value=1, max_value=20),
        n_tables=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100)
    def test_allocated_table_capacity_sufficient(self, guest_count, n_tables):
        tables = [
            {"id": f"t{i}", "capacity": i + 1, "area": "center", "cat_friendly": False}
            for i in range(n_tables)
        ]
        result = allocate_table(guest_count, tables)
        if result:
            assert result["capacity"] >= guest_count

    @given(
        guest_count=st.integers(min_value=100, max_value=200),
    )
    @settings(max_examples=30)
    def test_oversized_party_returns_none(self, guest_count):
        tables = [{"id": "t1", "capacity": 4}]
        result = allocate_table(guest_count, tables)
        assert result is None

    @given(
        guest_count=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=50)
    def test_window_preference_respected(self, guest_count):
        tables = [
            {"id": "center", "capacity": 20, "area": "center", "cat_friendly": False},
            {"id": "window", "capacity": 20, "area": "window", "cat_friendly": False},
        ]
        result = allocate_table(guest_count, tables, prefer_window=True)
        assert result is not None
        assert result["area"] == "window"


# ============================================================
# 2. detect_conflict — PBT
# ============================================================
class TestDetectConflictPBT:
    """冲突检测 PBT"""

    @given(
        overlap_minutes=st.integers(min_value=0, max_value=120),
    )
    @settings(max_examples=50)
    def test_overlapping_times_detect_conflict(self, overlap_minutes):
        base_time = datetime(2026, 6, 15, 18, 0, 0)
        existing = [
            {
                "id": "r1",
                "table_id": "t1",
                "reservation_time": base_time,
                "duration_minutes": 120,
                "status": "confirmed",
            }
        ]
        requested = base_time + timedelta(minutes=120 - overlap_minutes)
        has_conflict, _ = detect_conflict(requested, 120, existing, "t1")
        if overlap_minutes > 15:  # overlap > buffer
            assert has_conflict

    @given(
        gap_minutes=st.integers(min_value=16, max_value=300),
    )
    @settings(max_examples=50)
    def test_non_overlapping_times_no_conflict(self, gap_minutes):
        base_time = datetime(2026, 6, 15, 18, 0, 0)
        existing = [
            {
                "id": "r1",
                "table_id": "t1",
                "reservation_time": base_time,
                "duration_minutes": 60,
                "status": "confirmed",
            }
        ]
        # 请求时间在结束+缓冲之后
        requested = base_time + timedelta(minutes=60 + 15 + gap_minutes)
        has_conflict, _ = detect_conflict(requested, 60, existing, "t1")
        assert not has_conflict

    @given(
        existing_status=st.sampled_from(["confirmed", "pending", "completed", "cancelled"]),
    )
    @settings(max_examples=50)
    def test_cancelled_reservations_ignored(self, existing_status):
        base_time = datetime(2026, 6, 15, 18, 0, 0)
        existing = [
            {
                "id": "r1",
                "table_id": "t1",
                "reservation_time": base_time,
                "duration_minutes": 120,
                "status": existing_status,
            }
        ]
        has_conflict, _ = detect_conflict(base_time, 60, existing, "t1")
        if existing_status == "cancelled":
            assert not has_conflict


# ============================================================
# 3. can_cancel — PBT
# ============================================================
class TestCanCancelPBT:
    """取消策略 PBT"""

    @given(
        hours_ahead=st.floats(min_value=0.1, max_value=48.0),
        tier=st.sampled_from(["bronze", "silver", "gold", "platinum"]),
    )
    @settings(max_examples=100)
    def test_cancel_rules_by_tier(self, hours_ahead, tier):
        now = datetime(2026, 6, 15, 10, 0, 0)
        res_time = now + timedelta(hours=hours_ahead)
        can, msg = can_cancel(res_time, now, tier)

        thresholds = {"bronze": 2, "silver": 1, "gold": 0.5, "platinum": 0}
        required = thresholds[tier]
        if required == 0:
            assert can
        elif hours_ahead >= required:
            assert can
        else:
            assert not can

    @given(tier=st.sampled_from(["bronze", "silver", "gold", "platinum"]))
    @settings(max_examples=20)
    def test_platinum_always_can_cancel(self, tier):
        now = datetime(2026, 6, 15, 10, 0, 0)
        res_time = now + timedelta(minutes=5)
        can, _ = can_cancel(res_time, now, "platinum")
        assert can


# ============================================================
# 4. calculate_price — PBT
# ============================================================
class TestCalculatePricePBT:
    """价格计算 PBT"""

    @given(
        guest_count=st.integers(min_value=1, max_value=20),
        duration=st.floats(min_value=0.5, max_value=8.0),
        is_peak=st.booleans(),
        tier=st.sampled_from(["bronze", "silver", "gold", "platinum"]),
    )
    @settings(max_examples=100)
    def test_price_is_positive(self, guest_count, duration, is_peak, tier):
        price = calculate_price(guest_count, duration, is_peak, tier)
        assert price > 0

    @given(
        guest_count=st.integers(min_value=1, max_value=20),
        duration=st.floats(min_value=0.5, max_value=8.0),
    )
    @settings(max_examples=50)
    def test_peak_more_expensive_than_off_peak(self, guest_count, duration):
        off_peak = calculate_price(guest_count, duration, False, "bronze")
        on_peak = calculate_price(guest_count, duration, True, "bronze")
        assert on_peak >= off_peak

    @given(
        guest_count=st.integers(min_value=1, max_value=20),
        duration=st.floats(min_value=0.5, max_value=8.0),
    )
    @settings(max_examples=50)
    def test_higher_tier_pays_less_or_equal(self, guest_count, duration):
        bronze = calculate_price(guest_count, duration, False, "bronze")
        platinum = calculate_price(guest_count, duration, False, "platinum")
        assert platinum <= bronze

    @given(
        guest_count=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=30)
    def test_extra_services_increase_price(self, guest_count):
        base = calculate_price(guest_count, 1.0, False, "bronze")
        with_extras = calculate_price(
            guest_count, 1.0, False, "bronze",
            extra_services=["cat_treat", "photo_package"]
        )
        assert with_extras > base


# ============================================================
# 5. generate_time_slots — PBT
# ============================================================
class TestGenerateTimeSlotsPBT:
    """时间槽生成 PBT"""

    @given(
        slot_minutes=st.integers(min_value=30, max_value=240),
    )
    @settings(max_examples=50)
    def test_slots_dont_overlap(self, slot_minutes):
        slots = generate_time_slots(slot_minutes=slot_minutes)
        for i in range(len(slots) - 1):
            assert slots[i]["end"] <= slots[i + 1]["start"]

    @given(
        slot_minutes=st.integers(min_value=30, max_value=240),
    )
    @settings(max_examples=50)
    def test_all_slots_within_hours(self, slot_minutes):
        slots = generate_time_slots("10:00", "22:00", slot_minutes)
        for s in slots:
            assert s["start"] >= "10:00"
            assert s["end"] <= "22:00"

    @given(
        slot_minutes=st.integers(min_value=30, max_value=120),
    )
    @settings(max_examples=30)
    def test_slots_have_exact_duration(self, slot_minutes):
        slots = generate_time_slots(slot_minutes=slot_minutes)
        for s in slots:
            start_h, start_m = map(int, s["start"].split(":"))
            end_h, end_m = map(int, s["end"].split(":"))
            duration = (end_h * 60 + end_m) - (start_h * 60 + start_m)
            assert duration == slot_minutes
