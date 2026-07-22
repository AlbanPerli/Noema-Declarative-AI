from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable


def value_of(value):
    return getattr(value, "value", value)


def label_of(value):
    identifier = getattr(value, "id", None)
    if identifier:
        return str(identifier)
    name = getattr(value, "name", None)
    if name:
        return str(name)
    return repr(value)


@dataclass(frozen=True)
class Predicate:
    evaluator: Callable[[], bool]
    label: str

    def evaluate(self):
        return bool(self.evaluator())

    def __bool__(self):
        return self.evaluate()

    def __and__(self, other):
        other = ensure_predicate(other)
        return Predicate(
            lambda: self.evaluate() and other.evaluate(),
            f"({self.label}) AND ({other.label})",
        )

    def __or__(self, other):
        other = ensure_predicate(other)
        return Predicate(
            lambda: self.evaluate() or other.evaluate(),
            f"({self.label}) OR ({other.label})",
        )

    def __invert__(self):
        return Predicate(lambda: not self.evaluate(), f"NOT ({self.label})")

    def __repr__(self):
        return f"Predicate({self.label})"


def ensure_predicate(value):
    if isinstance(value, Predicate):
        return value
    if callable(value):
        return Predicate(lambda: bool(value()), getattr(value, "__name__", "callable"))
    return Predicate(lambda: bool(value), str(bool(value)))


def compare_value(left, operator, right):
    labels = {
        "==": "==",
        "!=": "!=",
    }

    def evaluator():
        left_value = value_of(left)
        right_value = value_of(right)
        if operator == "==":
            return left_value == right_value
        if operator == "!=":
            return left_value != right_value
        raise ValueError(f"Unsupported predicate operator: {operator}")

    return Predicate(evaluator, f"{label_of(left)} {labels[operator]} {right!r}")


def contains_value(left, options: Iterable[Any], negate=False):
    options = tuple(options)
    label = f"{label_of(left)} in {list(options)!r}"
    if negate:
        label = f"{label_of(left)} not in {list(options)!r}"

    def evaluator():
        result = value_of(left) in options
        return not result if negate else result

    return Predicate(evaluator, label)
