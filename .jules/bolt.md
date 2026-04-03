## 2024-05-24 - Lazily Initialize Static Computations Used in SwiftUI Loops
**Learning:** Using `static var` with a computed closure for statically filtered lists accessed by `ForEach` loops causes the list to be re-evaluated on every UI render pass, impacting performance.
**Action:** Convert these properties to lazily-initialized `static let` with a closure to compute and cache the result exactly once. Remember to fully qualify member access (e.g., `MusicGenre.allCases`) inside the static closure.
