## 2024-05-24 - Asynchronous Image Loading for UI Performance
**Learning:** Synchronous disk I/O like `NSImage(contentsOf:)` on the main thread causes UI hitching, especially in scrollable lists. Using `AsyncImage` for local file URLs lacks caching and causes flickering.
**Action:** Use a `.task(id:)` modifier with `Task.detached(priority: .background)` to load the `NSImage` asynchronously, then assign it to a `@State` variable on the main actor if not cancelled.
