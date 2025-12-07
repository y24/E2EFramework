import pytest

from src.core.context import Context
from src.core.execution.actions.verify_actions import VerifyAction
from src.core.execution.condition import ConditionEvaluator


def _make_action():
    # Context is unused for these unit-level checks
    return VerifyAction(context=None)


class StubElement:
    def __init__(self, exists=True, enabled=True, visible=True, text=""):
        self._exists = exists
        self._enabled = enabled
        self._visible = visible
        self._text = text

    def exists(self):
        return self._exists

    def is_enabled(self):
        return self._enabled

    def is_visible(self):
        return self._visible

    def get_value(self):
        return self._text

    def window_text(self):
        return self._text


def test_equals_assertion_pass_and_fail():
    action = _make_action()

    # Pass
    action.execute({"type": "equals", "actual": 1, "expected": 1})

    # Fail
    with pytest.raises(AssertionError):
        action.execute({"type": "equals", "actual": 1, "expected": 2})


def test_contains_plain_and_regex():
    action = _make_action()

    action.execute({"type": "contains", "actual": "hello world", "contains": "world"})
    action.execute({"type": "contains", "actual": "abc123", "contains": r"abc\d+", "regex": True})
    action.execute({"type": "contains", "actual": "abc123", "contains": r"abc\d+", "regex": "true"})

    with pytest.raises(AssertionError):
        action.execute({"type": "contains", "actual": "hello", "contains": "world"})

    with pytest.raises(AssertionError):
        action.execute({"type": "contains", "actual": "abc", "contains": r"\d+", "regex": True})


def test_not_contains_plain_and_regex():
    action = _make_action()

    action.execute({"type": "not_contains", "actual": "hello", "not_contains": "world"})
    action.execute({"type": "not_contains", "actual": "abc", "not_contains": r"\d+", "regex": True})

    with pytest.raises(AssertionError):
        action.execute({"type": "not_contains", "actual": "hello", "not_contains": "hell"})

    with pytest.raises(AssertionError):
        action.execute({"type": "not_contains", "actual": "abc123", "not_contains": r"\d+", "regex": True})


def test_matches_fullmatch():
    action = _make_action()

    action.execute({"type": "matches", "actual": "order-123", "pattern": r"order-\d+"})

    with pytest.raises(AssertionError):
        action.execute({"type": "matches", "actual": "order-123-extra", "pattern": r"order-\d+"})


def test_not_exists_and_clickable(monkeypatch):
    action = _make_action()

    # Monkeypatch target resolver to avoid importing real pages
    action._resolve_target = lambda target: StubElement(exists=False)
    action.execute({"type": "not_exists", "target": "dummy.page.element"})

    action._resolve_target = lambda target: StubElement(exists=True, enabled=True, visible=True)
    action.execute({"type": "clickable", "target": "dummy.page.element"})

    action._resolve_target = lambda target: StubElement(exists=True, enabled=False, visible=True)
    with pytest.raises(AssertionError):
        action.execute({"type": "clickable", "target": "dummy.page.element"})

    action._resolve_target = lambda target: StubElement(exists=True, enabled=True, visible=True)
    with pytest.raises(AssertionError):
        action.execute({"type": "not_exists", "target": "dummy.page.element"})


def test_element_text_empty(monkeypatch):
    evaluator = ConditionEvaluator(Context())

    monkeypatch.setattr(evaluator, "_resolve_element", lambda target, required_field="": StubElement(text=""))
    assert evaluator._evaluate_text_empty({"target": "dummy", "expected": True}) is True

    monkeypatch.setattr(evaluator, "_resolve_element", lambda target, required_field="": StubElement(text="value"))
    assert evaluator._evaluate_text_empty({"target": "dummy", "expected": True}) is False


def test_checkbox_state(monkeypatch):
    evaluator = ConditionEvaluator(Context())

    class ToggleStub:
        def __init__(self, toggle_state=None, checked=None):
            self._toggle_state = toggle_state
            self._checked = checked

        def get_toggle_state(self):
            return self._toggle_state

        def is_checked(self):
            return self._checked

    # True via toggle state
    monkeypatch.setattr(evaluator, "_resolve_element", lambda target, required_field="": ToggleStub(toggle_state=1))
    assert evaluator._evaluate_checkbox_state({"target": "dummy", "expected": True}) is True

    # False via is_checked fallback
    monkeypatch.setattr(evaluator, "_resolve_element", lambda target, required_field="": ToggleStub(toggle_state=None, checked=False))
    assert evaluator._evaluate_checkbox_state({"target": "dummy", "expected": False}) is True

    # Mismatch raises False result
    monkeypatch.setattr(evaluator, "_resolve_element", lambda target, required_field="": ToggleStub(toggle_state=0))
    assert evaluator._evaluate_checkbox_state({"target": "dummy", "expected": True}) is False
