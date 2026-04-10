## 2024-05-30 - Prevent Main Thread Blocking in SwiftUI Lists
**Learning:** Performing synchronous disk I/O (like `NSImage(contentsOf:)`) directly inside the `body` of a SwiftUI view, especially those in `ScrollView` or `LazyVGrid`, blocks the main thread and causes severe scrolling hitches.
**Action:** Always load local images asynchronously using a `.task` modifier with `Task.detached(priority: .background)` to keep the UI thread unblocked, and assign the result to a `@State` variable.
