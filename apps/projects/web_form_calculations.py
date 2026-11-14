"""Compile a restricted calculation syntax into a shared Python/browser plan."""

import ast
import json
import math
import re


class CalculationError(ValueError):
    pass


OPERATORS = {
    ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.Mod: "%",
    ast.USub: "neg", ast.UAdd: "pos", ast.Not: "not",
    ast.Eq: "=", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=",
    ast.Gt: ">", ast.GtE: ">=", ast.And: "and", ast.Or: "or",
}
FUNCTIONS = {
    "int", "number", "string", "substr", "concat", "round", "floor",
    "ceiling", "abs", "choose", "coalesce", "selected", "true", "false",
}
TOKENS = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|\$\{([^}]+)\}|\b(?:div|mod|if)\b|(?<![<>=!])=(?!=)")


def compile_expression(expression, allow_attributes=False):
    def translate(match):
        token = match.group()
        if match.group(1) is not None:
            return f"ref({json.dumps(match.group(1))})"
        return {"div": "/", "mod": "%", "if": "choose", "=": "=="}.get(token, token)

    def convert(node):
        if allow_attributes and isinstance(node, ast.Name):
            return ["attribute", node.id]
        if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, float, bool)):
            return ["literal", node.value]
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            name = node.func.id
            if name == "ref" and len(node.args) == 1 and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                return ["ref", node.args[0].value]
            if name in FUNCTIONS:
                return ["call", name, [convert(arg) for arg in node.args]]
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            return ["op", OPERATORS[type(node.op)], [convert(node.left), convert(node.right)]]
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
            return ["op", OPERATORS[type(node.op)], [convert(node.operand)]]
        if isinstance(node, ast.BoolOp):
            return ["op", OPERATORS[type(node.op)], [convert(value) for value in node.values]]
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in OPERATORS:
            return ["op", OPERATORS[type(node.ops[0])], [convert(node.left), convert(node.comparators[0])]]
        raise CalculationError("Unsupported calculation expression.")

    try:
        return convert(ast.parse(TOKENS.sub(translate, str(expression).strip()), mode="eval").body)
    except (SyntaxError, RecursionError) as exc:
        raise CalculationError("Invalid calculation expression.") from exc


def calculation_plan(fields):
    fields = list(fields)
    source_references = {
        field["name"]: set(re.findall(r"\$\{([^}]+)\}", field["relevant"]))
        for field in fields
    }
    pending = {}
    for field in fields:
        if not field["calculation"] and field["type"] != "calculate":
            continue
        item = {"name": field["name"], "relevant": field["relevant"], "tree": None, "error": ""}
        try:
            item["tree"] = compile_expression(field["calculation"])
        except CalculationError as exc:
            item["error"] = str(exc)
        pending[item["name"]] = item

    def references(tree):
        if not tree:
            return set()
        if tree[0] == "ref":
            return {tree[1]}
        if tree[0] in {"call", "op"}:
            return set().union(*(references(arg) for arg in tree[2]))
        return set()

    result = []
    dependencies = {}
    for name, item in pending.items():
        sources = references(item["tree"]) | source_references[name]
        while True:
            expanded = sources | set().union(*(source_references.get(source, set()) for source in sources))
            if expanded == sources:
                break
            sources = expanded
        dependencies[name] = sources
    while pending:
        ready = [name for name in pending if not dependencies[name] & pending.keys()]
        if not ready:
            for item in pending.values():
                item["error"] = "Circular calculation dependency."
            result.extend(pending.values())
            break
        result.extend(pending.pop(name) for name in ready)
    return result


def numeric(value):
    if value is None or value == "" or isinstance(value, list):
        return float("nan")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def text(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return " ".join(map(text, value))
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def boolean(value):
    if isinstance(value, (int, float)):
        return value != 0 and (not isinstance(value, float) or not math.isnan(value))
    return bool(value)


def equal_values(left, right):
    if isinstance(left, bool) or isinstance(right, bool):
        return boolean(left) == boolean(right)
    if isinstance(left, (int, float)) or isinstance(right, (int, float)):
        return numeric(left) == numeric(right)
    return text(left) == text(right)


def evaluate_calculation(tree, values, attributes=None):
    kind, name = tree[:2]
    if kind == "literal":
        return name
    if kind == "ref":
        return values.get(name, "")
    if kind == "attribute":
        return (attributes or {}).get(name, "")
    args = tree[2]
    if kind == "call" and name == "choose":
        if len(args) != 3:
            raise CalculationError("if() requires three arguments.")
        condition = boolean(evaluate_calculation(args[0], values, attributes))
        return evaluate_calculation(args[1 if condition else 2], values, attributes)
    if kind == "op" and name in {"and", "or"}:
        operands = (boolean(evaluate_calculation(arg, values, attributes)) for arg in args)
        return all(operands) if name == "and" else any(operands)
    resolved = [evaluate_calculation(arg, values, attributes) for arg in args]
    try:
        if kind == "op":
            if name == "not":
                return not boolean(resolved[0])
            if name in {"=", "!="}:
                equal = equal_values(resolved[0], resolved[1])
                return equal if name == "=" else not equal
            a = numeric(resolved[0])
            b = numeric(resolved[1]) if len(resolved) > 1 else 0
            if name == "neg": return -a
            if name == "pos": return a
            if name == "+": return a + b
            if name == "-": return a - b
            if name == "*": return a * b
            if name == "/": return a / b
            if name == "%": return math.fmod(a, b)
            if name == "<": return a < b
            if name == "<=": return a <= b
            if name == ">": return a > b
            if name == ">=": return a >= b
        if name == "true": return True
        if name == "false": return False
        if name == "number": return numeric(resolved[0])
        if name == "int": return math.trunc(numeric(resolved[0]))
        if name == "string": return text(resolved[0])
        if name == "substr":
            return text(resolved[0])[int(numeric(resolved[1])):int(numeric(resolved[2])) if len(resolved) > 2 else None]
        if name == "concat": return "".join(map(text, resolved))
        if name == "coalesce": return next((v for v in resolved if v not in ("", None)), "")
        if name == "selected": return text(resolved[1]) in text(resolved[0]).split()
        if name == "abs": return abs(numeric(resolved[0]))
        if name == "floor": return math.floor(numeric(resolved[0]))
        if name == "ceiling": return math.ceil(numeric(resolved[0]))
        if name == "round":
            factor = 10 ** (numeric(resolved[1]) if len(resolved) > 1 else 0)
            return math.floor(numeric(resolved[0]) * factor + 0.5) / factor
    except (ValueError, OverflowError, ZeroDivisionError):
        return float("nan")
    except (IndexError, TypeError) as exc:
        raise CalculationError("Invalid calculation arguments.") from exc
    raise CalculationError("Unsupported calculation expression.")


def calculation_value(tree, values):
    result = evaluate_calculation(tree, values)
    if isinstance(result, float):
        if not math.isfinite(result):
            return ""
        if result.is_integer():
            return int(result)
    return result
