import ast
import operator
from datetime import datetime
from typing import Callable, Dict
from zoneinfo import ZoneInfo


AllowedNumber = int | float

_OPERATORS: Dict[type, Callable[[AllowedNumber, AllowedNumber], AllowedNumber]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}


def _eval_node(node: ast.AST) -> AllowedNumber:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _eval_node(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    raise ValueError("只支持数字和 + - * / // % ** () 运算。")


def calculator(expression: str) -> str:
    tree = ast.parse(expression, mode="eval")
    result = _eval_node(tree)
    return str(result)


def current_time() -> str:
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    return now.strftime("%Y-%m-%d %H:%M:%S %Z")
