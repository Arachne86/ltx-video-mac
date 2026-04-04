## 2025-02-12 - Single-pass regex with dictionary lookup
**Learning:** Python's `list.index(item)` in a hot substitution loop (like `re.sub` callbacks) introduces O(N) complexity per match. When optimizing multi-pattern regex substitutions with `re.sub`, calculating array indices inside the callback function diminishes the performance gains.
**Action:** Use a pre-computed dictionary mapping (e.g. `{word: index}`) at the module level for O(1) index lookups during single-pass regex substitutions.
