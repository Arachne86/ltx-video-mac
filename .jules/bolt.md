## 2024-03-24 - SwiftUI Performance: Static var vs Static let in static list generation
**Learning:** In Swift, defining a computed static property (`static var`) that performs filtering (e.g., `Enum.allCases.filter`) for a list accessed by SwiftUI's `ForEach` causes the filtering to re-evaluate on every single UI render pass.
**Action:** Always use lazily-initialized static constants (`static let`) with a closure to compute and cache statically filtered lists exactly once, avoiding redundant O(N) operations during UI updates.
