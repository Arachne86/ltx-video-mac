## 2024-05-24 - [Avoid synchronous disk I/O in SwiftUI view bodies]
**Learning:** `NSImage(contentsOf:)` causes synchronous disk I/O on the main thread inside SwiftUI view bodies, blocking fluid scrolling and severely bottlenecking rendering performance in lists/grids.
**Action:** Use `AsyncImage(url:)` which natively supports local `file://` URLs and loads images asynchronously without blocking the main thread.
