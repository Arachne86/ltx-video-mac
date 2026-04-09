## 2024-05-24 - Lazily evaluated static properties for static UI elements
**Learning:** In SwiftUI macOS apps, using computed static properties (`static var`) for statically filtered lists accessed by `ForEach` loops causes them to re-evaluate on every UI render pass, reducing performance.
**Action:** Use lazily-initialized static constants (`static let`) with a closure to compute and cache the result exactly once.
