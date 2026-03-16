## 2024-03-16 - SwiftUI Performance Optimization: Static Let vs Static Var

**Learning:** When using static collections (like grouped enums) in SwiftUI `ForEach` loops, using `static var` (a computed property) causes the collection to be re-evaluated and filtered on every single UI render pass. This is extremely inefficient for static data.
**Action:** Use a lazily-initialized static constant (`static let`) with a closure instead to compute and cache the result exactly once. When initializing a `static let` property using a closure, the closure does not have implicit access to the type's other static members, so you must explicitly qualify them with the type name (e.g., `MusicGenre.allCases` instead of just `allCases`).
