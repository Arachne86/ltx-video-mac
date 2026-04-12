## 2024-04-12 - Background Dispatch Queue with Actor Capture Safety
**Learning:** When offloading synchronous disk I/O (like JSON encoding and `FileManager` removals) to a background `DispatchQueue` within a `@MainActor` class, directly capturing the actor (`self`) in the async closure triggers strict concurrency warnings/errors.
**Action:** Always capture local variables (e.g., `let currentResults = results`, `let targetFile = historyFile`) synchronously on the main thread before the `async` closure to safely pass data to the background queue without violating actor isolation.
