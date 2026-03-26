## Bolt's Journal
## 2024-03-24 - Offloading @MainActor File Writes
**Learning:** In SwiftUI applications using `@MainActor` services, synchronous file system operations (like JSON encoding, writing, or deleting) directly on the main thread cause UI hitches and jank. Standard `Data.write(to:)` also isn't safe against partial writes without options.
**Action:** When saving application state (e.g., `HistoryManager`, `PresetManager`), always synchronously capture the state and the file URL on the main thread, then offload the `JSONEncoder` serialization and file writing to a private serial background `DispatchQueue`. Combine this with `.atomic` writing options to ensure data integrity without blocking the UI.
