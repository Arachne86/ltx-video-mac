
## 2025-02-14 - SwiftUI ForEach Filter Performance Optimization
**Learning:** In SwiftUI, `ForEach` loops evaluating computed `static var` properties containing `filter` or similar sequence operations re-evaluate the computation on *every* UI render pass, causing unnecessary CPU overhead and potential UI micro-stutters, particularly in long scrollable lists or during rapid view updates.
**Action:** When binding statically filtered data to `ForEach` loops, use lazily initialized `static let` constants via closures (e.g., `static let items: [Item] = { ... }()`) to ensure the filtering logic executes exactly once per app session.
