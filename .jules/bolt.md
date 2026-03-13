## 2024-03-13 - Cache MusicGenre.groupedByCategory statically
**Learning:** In SwiftUI macOS apps, computed static properties (`static var`) for statically filtered lists accessed by `ForEach` loops re-evaluate on every UI render pass, causing performance issues.
**Action:** Use lazily-initialized static constants (`static let`) with a closure to compute and cache the result exactly once. Remember to explicitly qualify static members inside the closure (e.g., `MusicGenre.allCases`).
