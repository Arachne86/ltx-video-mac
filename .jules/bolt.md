
## 2024-05-24 - MainActor I/O Bottleneck Avoidance
**Learning:** In `@MainActor` Swift classes like `HistoryManager` and `PresetManager`, performing synchronous file operations (like `JSONEncoder().encode()` or `Data.write()`) directly on the main thread causes UI hitches and dropped frames. Using `Task.detached` to avoid this is incorrect for sequential operations, as it can introduce data races if multiple writes are fired in rapid succession.
**Action:** When implementing persistence in main-thread-bound services, capture the current state synchronously on the main thread, and then offload the actual encoding and file writing to a dedicated, serial background `DispatchQueue`. Always use the `.atomic` flag for `Data.write(to:options:)` to ensure file integrity.
