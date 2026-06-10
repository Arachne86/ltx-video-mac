
## 2024-05-18 - Offload Synchronous Image IO
**Learning:** Synchronous disk I/O (like `NSImage(contentsOf:)`) and image manipulation directly on the main thread is a common source of UI blocking in SwiftUI macOS apps, especially within repeated views or views that load large source files. Wait until it causes a problem though!
**Action:** When working on views with file-based images (like `HistoryView` thumbnails or `PromptInputView` source previews), explicitly use `Task.detached(priority: .background)` combined with `.task(id:)` or explicit `Task` blocks to push I/O and drawing work to background threads. This allows smooth scrolling and selection without main thread lockup.
