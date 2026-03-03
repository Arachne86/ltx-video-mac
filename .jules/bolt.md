## 2024-05-24 - AsyncImage over NSImage for SwiftUI Performance
**Learning:** Loading images synchronously from the local disk using `NSImage(contentsOf:)` directly in a SwiftUI view (especially inside a LazyVGrid/List) blocks the main thread. This leads to dropped frames and severe stuttering during rapid scrolling because the UI thread waits for disk I/O for every thumbnail appearing on screen.
**Action:** Always prefer `AsyncImage(url:)` for loading `file://` URLs in SwiftUI lists/grids. It natively handles asynchronous loading and offloads the file reading from the main rendering thread.
