## 2024-05-24 - Async UI Image Loading
**Learning:** Loading local images synchronously with `NSImage(contentsOf:)` on the main thread in SwiftUI blocks the UI, notably impacting fluid scrolling in views with many images (e.g., `HistoryView`) and freezing the UI when picking large images (e.g., in `PromptInputView`).
**Action:** Use `AsyncImage(url:)` for loading local URLs in lists/grids, and wrap manual image processing (like thumbnail generation) in `Task.detached` to offload work from the main thread.
