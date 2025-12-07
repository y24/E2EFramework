# Condition & Validation Enhancement Plan

Current status and implementation plan for strengthening the E2E framework's condition branching and verification capabilities.

## 1. Conditions (src/core/execution/condition.py)

### Missing / To Be Implemented
| Type | Description | Status | Note |
| :--- | :--- | :--- | :--- |
| `variable` | Variable comparison | Existing | Supports equals, not_equals, contains |
| `element_exists` | Check if element exists | Existing | Supports timeout |
| `element_text_empty` | Check if element text is empty | New | Use for "Input if empty" logic |
| `checkbox_state` | Check checkbox ON/OFF | New | Use for "Turn ON if OFF" logic |

### Implementation Details
- **element_text_empty**:
  - Target: Element path
  - Logic: Fetch text (get_value/window_text), return True if empty string or None.
- **checkbox_state**:
  - Target: Element path (Checkbox)
  - Parameter: `expected` (bool - True for ON, False for OFF)
  - Logic: Check toggle state (`get_toggle_state()` or `is_checked()`).

## 2. Validations (src/core/execution/actions/verify_actions.py)

### Missing / To Be Implemented
| Type | Description | Status | Note |
| :--- | :--- | :--- | :--- |
| `exists` | Element exists | Existing | |
| `not_exists` | Element does not exist | New | Inverse of existing check |
| `contains` | Text contains (simple) | Existing | Enhance for Regex |
| `not_contains` | Text does not contain | New | Inverse of contains |
| `clickable` | Element is clickable | New | Check `is_enabled()` and `is_visible()`? |
| `matches` | Regex full match | New | Explicit regex match |

### Implementation Details
- **not_exists**:
  - Check `not element.exists()`.
- **contains (Enhancement)**:
  - Add `regex` parameter (bool, default False).
  - If `regex=True`, use `re.search`.
- **not_contains**:
  - Inverse logic of `contains` (including regex support).
- **clickable**:
  - Check `element.is_enabled()`. (Maybe also check visibility if needed).

### Additional Proposals
- **file_size**: (Already implemented partially in verify? Need to confirm strictly).
- **list_count**: Check number of items in list/combo.

## 3. Implementation Plan

1.  **Update `src/core/execution/condition.py`**:
    - Add `_evaluate_text_empty` method.
    - Add `_evaluate_checkbox_state` method.
2.  **Update `src/core/execution/actions/verify_actions.py`**:
    - Add `not_exists` handling.
    - Update `contains` to support `regex`.
    - Add `not_contains` handling.
    - Add `clickable` handling.
3.  **Documentation**:
    - Update `implementation_status.md` to `Done` once completed.
 Update `implementation_status.md` to `Done` once completed.
