## 2024-05-14 - Offload File Operations from Main Thread
**Learning:** In `@MainActor` classes (like `HistoryManager` and `PresetManager`), synchronous file system operations (JSON encoding, writing, deleting) block the main thread and cause UI hitches.
**Action:** Use a dedicated serial background `DispatchQueue` to offload these tasks, maintaining UI responsiveness and write order. Avoid `Task.detached` for sequential file writes. Ensure variables are captured synchronously as local variables on the main thread before dispatching.
