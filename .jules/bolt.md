## 2024-05-09 - Avoid Computed Static Properties in SwiftUI ForEach
**Learning:** Computed static properties (`static var`) accessed inside SwiftUI `ForEach` loops (like statically filtered lists) cause unnecessary re-evaluations during every UI render pass, leading to rendering performance hits.
**Action:** Use lazily-initialized static constants (`static let = { ... }()`) to compute and cache these values exactly once, and ensure other static members accessed within the closure are explicitly qualified (e.g., `Enum.allCases`).
