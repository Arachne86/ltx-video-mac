
## 2024-05-23 - Avoid Synchronous Disk I/O in SwiftUI Grid Views
**Learning:** In SwiftUI lists and grids, synchronously loading images from disk using `NSImage(contentsOf:)` blocks the main thread during evaluation, leading to stuttering during scrolling and unresponsiveness. `AsyncImage` works perfectly with local `file://` URLs and handles off-thread loading and placeholder rendering automatically.
**Action:** Always prefer `AsyncImage(url:)` over `NSImage(contentsOf:)` or `UIImage(contentsOfFile:)` when rendering images dynamically in repetitive views like lists, grids, or carousels.
