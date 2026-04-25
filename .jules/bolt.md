
## 2024-05-18 - Offload Synchronous Disk I/O from MainActor
**Learning:** In `@MainActor` classes (like `HistoryManager` and `PresetManager`), performing synchronous file system operations (JSON encoding, `data.write`, and `FileManager.removeItem`) blocks the main thread, causing UI hitches and frame drops. Simply wrapping them in `Task.detached` is dangerous as it executes concurrently and can introduce data races or unordered writes.
**Action:** Always capture mutable state synchronously as local constants on the main thread, and then offload the disk operations to a dedicated serial background `DispatchQueue` (e.g., `ioQueue.async`). Also use `options: .atomic` for safe file writing.
