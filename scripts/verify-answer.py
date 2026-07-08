#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify-answer.py — 数学答案可逆验证（2026-07-03 实战新增）
============================================================
背景：第 4 题不等式性质 a>b，自己算到 (D) b-a>0 与 a>b 矛盾却没发现。
本脚本：让模型在发出答案前，调用本脚本做"等价逆运算验证"。

用法：
  python verify-answer.py --check "a>b" --option "b-a>0"        # 不等式验证
  python verify-answer.py --equation "x-3=5" --answer "x=8"     # 方程代回验证

返回：JSON { "valid": bool, "reason": str, "counter_evidence": str }
exit code: 0=valid 1=invalid（必须看 stderr 才知道为啥失败）

支持题型：
  1. 不等式性质：a>b ↔ 等价变形（如 a+2>b+2、-4a<-4b）
  2. 方程代回：解出 x 后代回原式验证

原理（不靠 LLM 推理，靠 Python eval 真算）：
  - 用 Python eval 对具体 (a_val, b_val) 算 stmt/option 的布尔值
  - 7 组测试点覆盖正/负/零/小数/边界
  - 任何点"原命题成立但选项不成立" → valid=False
  - 7 组都成立 → valid=True
"""
import sys
import json
import re
import argparse


def verify_inequality(stmt: str, option: str) -> dict:
    """验证不等式选项：检查 option 是否为 stmt 的等价变形

    策略：用 Python 沙箱 eval 直接对具体数值算 stmt / option 的布尔值。
          避开 sympy Relational 的 __bool__ 限制。
    """
    # 7 组测试点（涵盖 a>b 在正/负/零/小数等所有区间）
    test_cases = [(5, 3), (2, 1), (10, -1), (3.5, 0), (100, 99), (-1, -5), (0.1, 0.01)]

    def eval_bool(expr_str: str, a_val: float, b_val: float) -> bool:
        # 替换 a, b 为具体数值；^ 替换为 **（Python 幂）
        substituted = expr_str.replace('a', f'({a_val})').replace('b', f'({b_val})')
        substituted = substituted.replace('^', '**')
        try:
            return bool(eval(substituted))
        except Exception as e:
            raise ValueError(f"表达式求值失败: '{substituted}' → {e}")

    counter_examples = []
    valid_test_points = 0
    for a_val, b_val in test_cases:
        try:
            stmt_holds = eval_bool(stmt, a_val, b_val)
        except ValueError as e:
            return {"valid": False, "reason": f"stmt 求值失败: {e}", "counter_evidence": ""}
        if not stmt_holds:
            continue
        valid_test_points += 1
        try:
            opt_holds = eval_bool(option, a_val, b_val)
        except ValueError as e:
            return {"valid": False, "reason": f"option 求值失败: {e}", "counter_evidence": ""}
        if not opt_holds:
            counter_examples.append({"a": a_val, "b": b_val})

    if counter_examples:
        return {
            "valid": False,
            "reason": f"选项 '{option}' 不是 '{stmt}' 的等价变形（找到反例）",
            "counter_evidence": f"反例 a={counter_examples[0]['a']}, b={counter_examples[0]['b']}："
                               f"原命题成立但选项不成立"
        }
    if valid_test_points == 0:
        return {
            "valid": False,
            "reason": f"无任何测试点满足 stmt '{stmt}'，无法验证",
            "counter_evidence": ""
        }
    return {
        "valid": True,
        "reason": f"选项 '{option}' 在 {valid_test_points} 组测试点都与 '{stmt}' 一致",
        "counter_evidence": ""
    }


def verify_equation(equation: str, answer: str) -> dict:
    """验证方程解：把解代回原方程检查（用 Python eval）"""
    try:
        lhs, rhs = equation.split('=')
    except ValueError:
        return {"valid": False, "reason": f"无法解析方程 '{equation}'", "counter_evidence": ""}

    sol_match = re.search(r'x\s*=\s*([-\d./]+)', answer)
    if not sol_match:
        return {"valid": False, "reason": f"无法从 '{answer}' 提取 x 的值", "counter_evidence": ""}
    x_val_str = sol_match.group(1)
    try:
        x_val = float(eval(x_val_str))
    except Exception as e:
        return {"valid": False, "reason": f"无法解析 x 值 '{x_val_str}': {e}", "counter_evidence": ""}

    def eval_expr(expr_str: str) -> float:
        substituted = expr_str.replace('x', f'({x_val})').replace('^', '**')
        return float(eval(substituted))

    try:
        lhs_val = eval_expr(lhs)
        rhs_val = eval_expr(rhs)
    except Exception as e:
        return {"valid": False, "reason": f"代回求值失败: {e}", "counter_evidence": ""}

    if abs(lhs_val - rhs_val) < 1e-9:
        return {"valid": True, "reason": f"x={x_val} 代回 '{equation}' 成立", "counter_evidence": ""}
    return {
        "valid": False,
        "reason": f"x={x_val} 代回不成立",
        "counter_evidence": f"lhs = {lhs_val}, rhs = {rhs_val}, 差 = {lhs_val - rhs_val}"
    }


def main():
    parser = argparse.ArgumentParser(description="数学答案可逆验证")
    parser.add_argument('--check', help='原命题不等式，如 "a>b"')
    parser.add_argument('--option', help='待验证的选项，如 "b-a>0"')
    parser.add_argument('--equation', help='原方程，如 "x-3=5"')
    parser.add_argument('--answer', help='求得的解，如 "x=8"')
    args = parser.parse_args()

    if args.check and args.option:
        result = verify_inequality(args.check, args.option)
    elif args.equation and args.answer:
        result = verify_equation(args.equation, args.answer)
    else:
        print(json.dumps({"valid": False, "reason": "必须提供 --check/--option 或 --equation/--answer", "counter_evidence": ""}, ensure_ascii=False))
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['valid'] else 1)


if __name__ == '__main__':
    main()
