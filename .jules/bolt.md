## 2024-05-15 - Offload Synchronous File Saves from @MainActor
**Learning:** Synchronous JSON encoding and file writes in `@MainActor` classes block the main thread, causing UI hitches. Data writing should use `.atomic` writes.
**Action:** Always offload disk I/O to a dedicated serial background `DispatchQueue` while capturing state synchronously on the main thread, instead of using `Task.detached` which can introduce concurrent data races.
