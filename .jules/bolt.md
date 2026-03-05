## 2024-05-24 - [Avoid synchronous file loading in SwiftUI]
**Learning:** Using `NSImage(contentsOf:)` in the `body` of a SwiftUI view causes synchronous disk I/O on the main thread, resulting in severe frame drops when rendering lists or grids (like in `HistoryThumbnailView`).
**Action:** Use `AsyncImage(url:)` natively supported by SwiftUI to load images asynchronously, keeping the main thread free and allowing fluid scrolling.
