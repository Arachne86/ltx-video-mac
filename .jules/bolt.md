## 2026-06-30 - [Offload MainActor I/O]
**Learning:** Synchronous file system operations (JSON encoding, writing, deleting) block the main thread and cause UI hitches in @MainActor classes.
**Action:** Offload these to a dedicated serial background DispatchQueue to maintain UI responsiveness and ensure write order, capturing state synchronously as local variables on the main thread before dispatching.
