
## 2024-05-24 - Lazily Initialize Static Arrays in SwiftUI
**Learning:** In SwiftUI, computed `static var` properties (like `Enum.allCases.filter`) used in `ForEach` or Pickers are re-evaluated on every UI render pass, causing unnecessary allocations and filtering overhead.
**Action:** Use lazily-initialized static constants (`static let myProperty: [Type] = { ... }()`) instead to compute and cache the result exactly once. Remember to explicitly qualify members inside the closure (e.g., `MyEnum.allCases` instead of `allCases`).
