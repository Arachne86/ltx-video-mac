## 2026-03-23 - Async Image Loading in SwiftUI
**Learning:** Performing synchronous file I/O operations (like `NSImage(contentsOf:)`) directly within a SwiftUI view's `body` property forces execution on the MainActor, blocking the main thread and causing severe UI stuttering, especially in scrollable lists or grids like `HistoryView`.
**Action:** Always offload synchronous disk reads to a background thread using `Task.detached(priority: .background)` within a `.task` modifier, and await the result to safely update a `@State` property on the MainActor.
