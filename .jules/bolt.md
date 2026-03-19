## 2024-05-15 - Optimize static property evaluation for UI pickers
**Learning:** In SwiftUI, computed static properties (`static var`) used for statically filtered lists (e.g., `Enum.allCases.filter`) accessed by `ForEach` loops will re-evaluate on every UI render pass.
**Action:** Use lazily-initialized static constants (`static let`) with a closure to compute and cache the result exactly once. Remember to explicitly qualify static members like `MusicGenre.allCases` inside the closure.
