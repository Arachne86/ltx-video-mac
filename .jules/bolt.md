## 2026-05-08 - Main Thread Disk I/O Bottleneck Avoidance
**Learning:** In Swift apps, running synchronous file system operations (JSON encoding/writing, deleting files) on the main thread inside @MainActor classes blocks the UI, causing hitches. Task.detached causes sequential disk writes to execute concurrently, leading to data races.
**Action:** Offload file system I/O to a dedicated serial background DispatchQueue. Always capture main-actor state synchronously as local constants before dispatching to the background queue to ensure thread safety and avoid strict concurrency warnings.
