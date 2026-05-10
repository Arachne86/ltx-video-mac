## 2026-05-10 - Offload Synchronous Disk I/O to Background Queue
**Learning:** In @MainActor classes like HistoryManager and PresetManager, synchronous file system operations (JSON encoding, writing) block the main thread and cause UI hitches. Offload these to a dedicated serial background DispatchQueue to maintain UI responsiveness and ensure write order.
**Action:** Always capture state synchronously as local variables on the main thread before dispatching to a serial ioQueue to avoid strict concurrency warnings.
