## 2024-05-30 - Offload synchronous MainActor disk I/O to background queues
**Learning:** In `@MainActor` classes (like `HistoryManager` and `PresetManager`), synchronous file system operations (JSON encoding, writing, deleting) block the main thread and cause UI hitches.
**Action:** Offload these to a dedicated serial background `DispatchQueue` to maintain UI responsiveness and ensure write order. Always capture state synchronously as local variables on the main thread before dispatching to avoid strict concurrency warnings/errors.
