#!/usr/bin/env python3
"""
NekoCafé 变异测试报告生成器
对核心业务逻辑函数进行变异测试并计算变异分数

方法: 选取核心业务函数，对其条件表达式进行逐项变异，
     运行完整测试套件检测变异是否被杀死。
"""

import ast
import subprocess
import sys
import os
import json


# ============================================================
# 手动定义测试用例: (函数, 参数, 期望结果)
# ============================================================
MEMBERSHIP_TESTS = {
    "member/calculate_points": [
        ((1, 0.5, False), 12),
        ((5, 2.0, False), 60),
        ((5, 2.0, True), 110),
        ((1, 0.1, False), 10),
        ((100, 100, True), 5000),
    ],
    "member/determine_tier": [
        ((0,), "bronze"),
        ((499,), "bronze"),
        ((500,), "silver"),
        ((1999,), "silver"),
        ((2000,), "gold"),
        ((4999,), "gold"),
        ((5000,), "platinum"),
        ((10000,), "platinum"),
    ],
    "member/should_upgrade": [
        (("bronze", 600), (True, "silver")),
        (("silver", 600), (False, None)),
        (("bronze", 3000), (True, "gold")),
        (("gold", 6000), (True, "platinum")),
        (("platinum", 10000), (False, None)),
    ],
    "member/mask_phone": [
        (("13800138001",), "138****8001"),
        (("12345678901",), "123****8901"),
        (("1234567",), "123****4567"),
    ],
    "member/validate_display_name": [
        (("张三",), (True, None)),
        (("",), (False, "名称长度必须在1-50字符之间")),
        (("12345",), (False, "名称不能全为数字")),
        (("a" * 51,), (False, "名称长度必须在1-50字符之间")),
    ],
    "member/calculate_age": [
        ((("2000-01-01", "2026-06-15"),), 26),
        ((("2000-12-31", "2026-06-15"),), 25),
    ],
}

RESERVATION_TESTS = {
    "reservation/allocate_table": [
        ({"guest_count": 4, "tables": [{"id": "t1", "capacity": 6, "area": "center", "cat_friendly": False}]}, "t1"),
        ({"guest_count": 10, "tables": [{"id": "t1", "capacity": 4}]}, None),
        ({"guest_count": 0, "tables": []}, ValueError),
    ],
    "reservation/detect_conflict": [
        ({"overlap": 60}, True),
        ({"gap": 100}, False),
        ({"status": "cancelled"}, False),
    ],
    "reservation/can_cancel": [
        ({"hours_ahead": 5, "tier": "bronze"}, True),
        ({"hours_ahead": 1, "tier": "bronze"}, False),
        ({"hours_ahead": 2, "tier": "silver"}, True),
        ({"hours_ahead": 0.5, "tier": "silver"}, False),
        ({"hours_ahead": 1, "tier": "gold"}, True),
        ({"hours_ahead": 0.1, "tier": "platinum"}, True),
    ],
    "reservation/calculate_price": [
        ({"guest_count": 2, "duration": 1.0, "peak": False, "tier": "bronze"}, 176.0),
        ({"guest_count": 2, "duration": 1.0, "peak": True, "tier": "bronze"}, 228.8),
        ({"guest_count": 2, "duration": 1.0, "peak": False, "tier": "platinum"}, 140.8),
        ({"guest_count": 0, "duration": 1.0}, ValueError),
        ({"guest_count": 21, "duration": 1.0}, ValueError),
    ],
    "reservation/generate_time_slots": [
        ({"slot_minutes": 60}, 12),
        ({"slot_minutes": 30}, 24),
        ({"slot_minutes": 120}, 6),
        ({"slot_minutes": 0}, ValueError),
    ],
}


def run_mutation_test() -> dict:
    """运行变异测试并计算分数"""

    report = {
        "service": "all",
        "mutants": [],
        "total": 0,
        "killed": 0,
        "survived": 0,
    }

    # 测试 Member 服务
    _test_member_functions(report)
    _test_reservation_functions(report)

    report["score"] = round(report["killed"] / max(report["total"], 1) * 100, 1)
    return report


def _test_member_functions(report):
    """手动注入变异并测试 Member 服务函数"""
    domain_path = "/tmp/nekocafe/services/member/src/domain.py"
    with open(domain_path, "r") as f:
        original = f.read()

    # 定义变异点 (行号, 原始代码, 变异代码, 描述)
    mutations = [
        # calculate_points 边界
        ("min(10, max(5000, base))", "min(10, max(5000, base))".replace("5000", "4999"), "降低积分上限"),
        ("min(10, max(5000, base))", "min(10, max(5000, base))".replace("10", "9"), "降低积分下限"),
        ("+ 50", "+ 49", "减少首访奖励"),
        # determine_tier 边界
        ("total_points >= 5000", "total_points > 5000", "白金阈值: >= 改为 >"),
        ("total_points >= 2000", "total_points > 2000", "金卡阈值: >= 改为 >"),
        ("total_points >= 500", "total_points > 500", "银卡阈值: >= 改为 >"),
        # should_upgrade 逻辑
        ("target_idx > current_idx", "target_idx >= current_idx", "升级判断: > 改为 >="),
        # mask_phone
        ("phone[:3] + \"****\" + phone[-4:]", "phone[:3] + \"***\" + phone[-3:]", "脱敏格式错误"),
        # validate_display_name
        ("len(name) > 50", "len(name) >= 50", "长度检查: > 改为 >="),
    ]

    for orig, mutated, desc in mutations:
        report["total"] += 1
        mutant_code = original.replace(orig, mutated)
        killed = _test_mutant(domain_path, mutant_code)
        report["killed" if killed else "survived"] += 1
        status = "KILLED" if killed else "SURVIVED"
        report["mutants"].append({
            "desc": desc,
            "status": status,
            "function": "member/domain",
        })

    # 恢复原始代码
    with open(domain_path, "w") as f:
        f.write(original)


def _test_reservation_functions(report):
    """手动注入变异并测试 Reservation 服务函数"""
    domain_path = "/tmp/nekocafe/services/reservation/src/domain.py"
    with open(domain_path, "r") as f:
        original = f.read()

    mutations = [
        # allocate_table
        ('t.get("capacity", 0) >= guest_count', 't.get("capacity", 0) > guest_count', "容量检查: >= 改为 >"),
        # detect_conflict
        ('requested_time < ex_end and requested_end > ex_start',
         'requested_time <= ex_end and requested_end > ex_start', "冲突检测: < 改为 <="),
        # can_cancel
        ('hours_until < required_hours', 'hours_until <= required_hours', "取消判断: < 改为 <="),
        # calculate_price
        ("88", "87", "基础价格降低"),
        ("1.3", "1.29", "高峰期倍率降低"),
        ("0.80", "0.79", "白金折扣变更"),
    ]

    for orig, mutated, desc in mutations:
        report["total"] += 1
        mutant_code = original.replace(orig, mutated)
        killed = _test_mutant(domain_path, mutant_code)
        report["killed" if killed else "survived"] += 1
        status = "KILLED" if killed else "SURVIVED"
        report["mutants"].append({
            "desc": desc,
            "status": status,
            "function": "reservation/domain",
        })

    with open(domain_path, "w") as f:
        f.write(original)


def _test_mutant(filepath, mutant_code):
    """测试变异体: 写入变异代码 → 运行测试 → 返回是否杀死"""
    # 写入变异
    with open(filepath, "r") as f:
        backup = f.read()
    with open(filepath, "w") as f:
        f.write(mutant_code)

    # 确定服务目录
    service_dir = os.path.dirname(os.path.dirname(filepath))
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "-q", "--tb=line"],
        cwd=service_dir,
        capture_output=True,
        timeout=30,
        env={**os.environ, "PYTHONPATH": f"src:{os.environ.get('PYTHONPATH', '')}"},
    )

    # 恢复原始代码
    with open(filepath, "w") as f:
        f.write(backup)

    # 测试失败 = 变异被杀死
    return result.returncode != 0


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("NekoCafé 变异测试 (Mutation Testing)")
    print("" + "=" * 60)
    print("变异算子: 边界值变异, 算术变异, 常量变异, 逻辑变异")
    print()

    report = run_mutation_test()

    for m in report["mutants"]:
        icon = "✅" if m["status"] == "KILLED" else "⚠️"
        print(f"  {icon} [{m['status']:8s}] [{m['function']}] {m['desc']}")

    print(f"\n{'=' * 60}")
    print(f"变异测试结果:")
    print(f"  总计变异体: {report['total']}")
    print(f"  杀死 (Killed): {report['killed']}")
    print(f"  存活 (Survived): {report['survived']}")
    print(f"  变异分数: {report['score']:.1f}%")
    status = "✅ 达标" if report['score'] >= 60 else "❌ 未达标"
    print(f"  判定: {status} (阈值 ≥60%)")
    print(f"{'=' * 60}")

    # 输出 JSON 报告
    report_path = "/tmp/nekocafe/quality-assets/reports/mutation-report.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n报告已保存: {report_path}")
