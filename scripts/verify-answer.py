#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify-answer.py — 数学答案可逆验证（2026-07-13 安全修复版）
============================================================
背景：第 4 题不等式性质 a>b，自己算到 (D) b-a>0 与 a>b 矛盾却没发现。
本脚本：让模型在发出答案前，调用本脚本做"等价逆运算验证"。

用法：
  python verify-answer.py --check "a>b" --option "b-a>0"        # 不等式验证
  python verify-answer.py --equation "x-3=5" --answer "x=8"     # 方程代回验证

返回：JSON { "valid": bool, "reason": str, "counter_evidence": str }
exit code: 0=valid 1=invalid（必须看 stderr 才知道为啥失败）

支持题型：
  1. 不等式性质：a>b ↔ 等价变形（如 a+2>b+2、-4*a<-4*b）
  2. 方程代回：解出 x 后代回原式验证

安全说明（2026-07-13 修复）：
  - 所有 eval() 已替换为基于 AST 的安全求值器 safe_eval_math()
  - 表达式字符串经过严格白名单校验 validate_expression()，仅允许
    数字、a/b/x 变量名、+ - * / ** % () < > <= >= == != 及空白
  - AST 节点白名单确保无函数调用、属性访问、导入或任意代码执行
  - 双层防御：regex 白名单（快速拦截）+ AST 节点白名单（精确拦截）
"""
import sys
import json
import re
import ast
import operator
import argparse


# ═══════════════════════════════════════════════════════════
# 安全求值器（替代 eval）—— 双层防御架构
# ═══════════════════════════════════════════════════════════

# 第一层：字符级白名单正则
# 允许：数字、字母（仅 a/b/x/and/or/not 会被 AST 层放行）、
#        算术运算符 + - * / ** %、比较运算符 < > = !、括号 ()、点号、空白
_EXPR_WHITELIST_RE = re.compile(r'^[\s\d.+\-*/%()<>=!a-zA-Z]+$')

# 第二层：AST 节点白名单
_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

_ALLOWED_CMPOPS = {
    ast.Gt: operator.gt,
    ast.Lt: operator.lt,
    ast.GtE: operator.ge,
    ast.LtE: operator.le,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}

_ALLOWED_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_ALLOWED_VARS = frozenset({'a', 'b', 'x'})


def validate_expression(expr_str: str) -> None:
    """严格白名单校验：拒绝任何不在允许列表中的字符。

    允许：数字、a/b/x 变量名、+ - * / ** % () < > <= >= == != 及空白
    拒绝：下划线、引号、方括号、花括号、分号、反斜杠、冒号等一切其他字符

    这是第一层防御。即使通过此校验，safe_eval_math() 的 AST 节点
    白名单仍会拦截任何危险构造（函数调用、属性访问等）。
    """
    if not expr_str or not expr_str.strip():
        raise ValueError("表达式为空")
    if not _EXPR_WHITELIST_RE.match(expr_str):
        raise ValueError(
            f"表达式包含非法字符: '{expr_str}'。"
            f"仅允许数字、a/b/x、+ - * / ** % () < > = ! 及空白"
        )


def safe_eval_math(expr_str: str, variables: dict = None):
    """基于 AST 的安全数学表达式求值器（替代 eval）。

    仅允许以下 AST 节点：
      - ast.Constant    → int/float 字面量
      - ast.Name        → 变量 a/b/x（需在 variables 中赋值）
      - ast.BinOp       → + - * / ** %
      - ast.UnaryOp     → + -（正负号）
      - ast.Compare     → > < >= <= == !=
      - ast.BoolOp      → and / or

    严禁（均会抛出 ValueError）：
      - 函数调用 (ast.Call)
      - 属性访问 (ast.Attribute)
      - 导入 (ast.Import)
      - lambda (ast.Lambda)
      - 列表/字典/集合推导 (ast.ListComp 等)
      - 下标访问 (ast.Subscript)
      - 赋值 (ast.Assign —— mode='eval' 本身已拒绝)
    """
    if variables is None:
        variables = {}

    try:
        tree = ast.parse(expr_str, mode='eval')
    except SyntaxError as e:
        raise ValueError(f"表达式语法错误: '{expr_str}' -> {e}")

    def _eval(node):
        # 表达式根节点
        if isinstance(node, ast.Expression):
            return _eval(node.body)

        # 数字字面量
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(
                f"不允许的常量类型: {type(node.value).__name__}"
            )

        # 变量引用（仅 a/b/x）
        if isinstance(node, ast.Name):
            if node.id not in _ALLOWED_VARS:
                raise ValueError(
                    f"不允许的标识符: '{node.id}'（仅允许 a, b, x）"
                )
            if node.id not in variables:
                raise ValueError(f"变量 '{node.id}' 未赋值")
            return variables[node.id]

        # 二元运算（+ - * / ** %）
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _ALLOWED_BINOPS:
                raise ValueError(
                    f"不允许的运算符: {op_type.__name__}"
                )
            left = _eval(node.left)
            right = _eval(node.right)
            return _ALLOWED_BINOPS[op_type](left, right)

        # 一元运算（正负号）
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _ALLOWED_UNARYOPS:
                raise ValueError(
                    f"不允许的一元运算符: {op_type.__name__}"
                )
            return _ALLOWED_UNARYOPS[op_type](_eval(node.operand))

        # 比较运算（> < >= <= == !=）
        if isinstance(node, ast.Compare):
            left = _eval(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                op_type = type(op)
                if op_type not in _ALLOWED_CMPOPS:
                    raise ValueError(
                        f"不允许的比较运算符: {op_type.__name__}"
                    )
                right = _eval(comparator)
                if not _ALLOWED_CMPOPS[op_type](left, right):
                    return False
                left = right
            return True

        # 布尔运算（and / or）
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return all(_eval(v) for v in node.values)
            if isinstance(node.op, ast.Or):
                return any(_eval(v) for v in node.values)
            raise ValueError(
                f"不允许的布尔运算符: {type(node.op).__name__}"
            )

        # 兜底：任何其他 AST 节点类型均拒绝
        raise ValueError(
            f"不允许的 AST 节点: {type(node).__name__}"
        )

    return _eval(tree)


# ═══════════════════════════════════════════════════════════
# 验证逻辑
# ═══════════════════════════════════════════════════════════

def verify_inequality(stmt: str, option: str) -> dict:
    """验证不等式选项：检查 option 是否为 stmt 的等价变形

    策略：用 safe_eval_math 对具体数值算 stmt / option 的布尔值。
          7 组测试点覆盖正/负/零/小数/边界。
    """
    # 预处理：^ → **（数学幂运算符，Python 中 ^ 是异或）
    stmt = stmt.replace('^', '**')
    option = option.replace('^', '**')

    # 第一层防御：白名单校验
    try:
        validate_expression(stmt)
        validate_expression(option)
    except ValueError as e:
        return {
            "valid": False,
            "reason": f"表达式校验失败: {e}",
            "counter_evidence": ""
        }

    # 7 组测试点（涵盖 a>b 在正/负/零/小数等所有区间）
    test_cases = [
        (5, 3), (2, 1), (10, -1), (3.5, 0),
        (100, 99), (-1, -5), (0.1, 0.01)
    ]

    counter_examples = []
    valid_test_points = 0
    for a_val, b_val in test_cases:
        try:
            stmt_holds = safe_eval_math(stmt, {'a': a_val, 'b': b_val})
        except (ValueError, ArithmeticError, TypeError) as e:
            return {
                "valid": False,
                "reason": f"stmt 求值失败: {e}",
                "counter_evidence": ""
            }
        if not stmt_holds:
            continue
        valid_test_points += 1
        try:
            opt_holds = safe_eval_math(option, {'a': a_val, 'b': b_val})
        except (ValueError, ArithmeticError, TypeError) as e:
            return {
                "valid": False,
                "reason": f"option 求值失败: {e}",
                "counter_evidence": ""
            }
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
    """验证方程解：把解代回原方程检查（用 safe_eval_math）"""
    try:
        lhs, rhs = equation.split('=')
    except ValueError:
        return {
            "valid": False,
            "reason": f"无法解析方程 '{equation}'",
            "counter_evidence": ""
        }

    sol_match = re.search(r'x\s*=\s*([-\d./]+)', answer)
    if not sol_match:
        return {
            "valid": False,
            "reason": f"无法从 '{answer}' 提取 x 的值",
            "counter_evidence": ""
        }
    x_val_str = sol_match.group(1)

    # 安全解析 x 值（替代 eval）
    try:
        validate_expression(x_val_str)
        x_val = float(safe_eval_math(x_val_str))
    except (ValueError, ArithmeticError, TypeError, RecursionError) as e:
        return {
            "valid": False,
            "reason": f"无法解析 x 值 '{x_val_str}': {e}",
            "counter_evidence": ""
        }

    # 预处理 + 白名单校验
    lhs = lhs.replace('^', '**')
    rhs = rhs.replace('^', '**')
    try:
        validate_expression(lhs)
        validate_expression(rhs)
    except ValueError as e:
        return {
            "valid": False,
            "reason": f"表达式校验失败: {e}",
            "counter_evidence": ""
        }

    try:
        lhs_val = float(safe_eval_math(lhs, {'x': x_val}))
        rhs_val = float(safe_eval_math(rhs, {'x': x_val}))
    except (ValueError, ArithmeticError, TypeError, RecursionError) as e:
        return {
            "valid": False,
            "reason": f"代回求值失败: {e}",
            "counter_evidence": ""
        }

    if abs(lhs_val - rhs_val) < 1e-9:
        return {
            "valid": True,
            "reason": f"x={x_val} 代回 '{equation}' 成立",
            "counter_evidence": ""
        }
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
        print(json.dumps({
            "valid": False,
            "reason": "必须提供 --check/--option 或 --equation/--answer",
            "counter_evidence": ""
        }, ensure_ascii=False))
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['valid'] else 1)


if __name__ == '__main__':
    main()
