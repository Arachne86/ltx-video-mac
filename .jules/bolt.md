
## 2025-01-20 - [Offloading Main Thread I/O]
**Learning:** `@MainActor` synchronous disk I/O (like JSON encoding and file writing) blocks the main thread and causes UI hitches. However, simply using `Task.detached` for sequential file writes leads to data races and strict concurrency warnings because it executes concurrently and captures `self`.
**Action:** Always capture state synchronously as local variables on the main thread and offload the actual encoding/writing to a dedicated background serial `DispatchQueue`. This maintains UI responsiveness, avoids strict concurrency warnings, and ensures write order safely.
