## 2025-03-08 - [UI Performance] Synchronous disk I/O on the main thread
**Learning:** Using `NSImage(contentsOf:)` in a SwiftUI grid component blocks the main thread because it synchronously loads from disk during rendering. This severely bottlenecks rendering and causes dropped frames when scrolling.
**Action:** Replace `NSImage(contentsOf:)` with `AsyncImage(url:)` for local `file://` URLs to load images asynchronously without blocking the UI thread.
