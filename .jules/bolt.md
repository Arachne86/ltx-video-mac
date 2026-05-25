## 2024-03-24 - [Strict Concurrency Background Queue IO]
**Learning:** When offloading synchronous disk I/O (JSON encoding and file writing/deleting) from @MainActor classes to background queues to prevent UI hitches, capturing actor state directly in the async closure triggers strict concurrency errors/data races.
**Action:** Always capture the required state (e.g. results arrays or file URLs) synchronously as local let variables on the main thread before dispatching the background task.
