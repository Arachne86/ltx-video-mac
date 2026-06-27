
## 2024-05-18 - [Offload MainActor File Operations]
**Learning:** In `@MainActor` classes (like `HistoryManager` and `PresetManager`), synchronous file system operations (JSON encoding, writing, deleting) block the main thread and cause UI hitches.
**Action:** Offload these to a dedicated serial background `DispatchQueue` to maintain UI responsiveness and ensure write order. Do not use `Task.detached` for sequential file writes, as it executes concurrently and introduces data races. Always capture state synchronously as local variables on the main thread before dispatching.
