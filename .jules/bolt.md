## 2024-05-24 - Avoid Synchronous Disk I/O on Main Thread in SwiftUI
**Learning:** Using `NSImage(contentsOf:)` on local file URLs inside a SwiftUI `LazyVGrid` or `List` performs synchronous disk I/O on the main thread. This severely bottlenecks rendering and blocks fluid scrolling.
**Action:** Use `AsyncImage(url:)` instead, which natively supports local `file://` URLs and loads images asynchronously, keeping the UI responsive.
