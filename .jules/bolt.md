## 2024-07-02 - O(N^2) String Parsing in Process Output
**Learning:** Accumulating stderr into a single string and repeatedly parsing it or calling `hasPrefix` not only causes O(N^2) complexity and massive intermediate allocations but also breaks progress tracking because `hasPrefix` checks the beginning of the entire accumulated string (ignoring new updates at the end).
**Action:** Use a `lineBuffer` to extract complete lines from chunked stream output, yielding individual lines to handlers to ensure O(1) processing per line and correct matching.
