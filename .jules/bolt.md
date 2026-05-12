## 2026-05-12 - Swift Subprocess Output Buffering
**Learning:** Naively passing an accumulated string of stdout/stderr to a handler on every readability event (e.g. `accumulated += str; handler(accumulated)`) creates an O(N^2) complexity bottleneck, especially when the handler re-evaluates the entire string from scratch.
**Action:** Use a line buffer inside the readability handler to split chunks by `\n` and yield complete lines individually to the handler in O(N) time.
