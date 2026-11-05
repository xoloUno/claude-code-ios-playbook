---
description: Testing conventions and strategy for solo indie iOS projects
globs: **/*Tests.swift, **/*Test.swift, **/Tests/**/*.swift
---

# Testing Conventions

## Framework

Use **Swift Testing** (`import Testing`, `@Test`, `#expect`, `#require`) for all new tests.
Do not use XCTest for new test files unless testing UI (XCUITest) or snapshot screenshots.

## What to test in a v1

Solo dev with limited hours — be strategic, not exhaustive.

**Always test:**
- Business logic and data transformations (models, calculations, formatting)
- Subscription state gating (free vs paid feature access)
- Data persistence round-trips (encode → store → decode)
- Edge cases in core loop logic (the 3-4 steps in CLAUDE.md's "Core Loop")

**Test if time allows:**
- ViewModel state transitions (given input → expected published state)
- Service layer methods (HealthKit queries, network parsing)

**Skip for v1:**
- SwiftUI view layout tests (use previews instead)
- Trivial getters/setters
- Apple framework wrappers that just delegate (trust the framework)
- Tests that require extensive mocking of system frameworks

## Conventions

- **File naming:** `{TypeName}Tests.swift` in `Tests/` directory
- **Test naming:** `test_{method}_{condition}_{expected}` or descriptive `@Test("description")`
- **Pattern:** Arrange-Act-Assert with clear separation
- **Parameterized tests:** Use `@Test(arguments:)` for multiple inputs with same logic
- **No mocking persistence** — use real UserDefaults (with a test suite name) or
  in-memory SwiftData containers. Mock boundaries (network), not internals.
- **Two Swift Testing compile traps** (Swift 6.4):
  - A `@MainActor` suite's `deinit` is nonisolated, so cleanup there can't touch the suite's
    statics. Make immutable `Sendable` constants `nonisolated static let`. Keep mutable state
    actor-isolated or behind synchronization (e.g. a `nonisolated static let` holding a
    `Mutex`); `nonisolated` can't go on a mutable `static var`.
  - `#expect(items.allSatisfy(\.flag))` fails with a misleading "call can throw" error; the
    closure form `#expect(items.allSatisfy { $0.flag })` compiles.
  - `#expect(try await store.load().field == value)` inside an `async throws` closure fails
    with "errors thrown from here are not handled". Hoist it:
    `let saved = try await store.load()`, then `#expect(saved.field == value)`.
- **Express version fixtures relative to the current constant.** A literal
  `{"schemaVersion":2}` meant as "newer" becomes current after a bump, and the failure looks
  like a data-loss bug. Write `currentSchemaVersion + 1`.
- **Bound every wait in async tests.** A test that waits for a condition only the fixed code
  produces (`await clock.waitForSleeper()`) hangs instead of failing on the regression it
  guards. Spin with `Task.yield()` up to a cap, or race a deadline, then `#expect` the
  condition. To prove a new test catches its bug, remove the fix and run it under
  `timeout`.

## Test the error paths, not just the happy path

For any service behind a protocol-based test double (sync, networking, persistence-that-can-fail),
a happy-path-only double hides silently-swallowed errors. Empty `catch` blocks in sync code have
shipped and only surfaced in on-device TestFlight testing, because the unit tests exercised only
the recording/success double.

Add a **throwing** test double (`Throwing<Service>` alongside `Recording<Service>`) and verify:

1. Errors propagate to observable state (e.g. a `lastSyncError` is set).
2. Idempotency flags stay **unset** after a failure, so retries actually retry.
3. The app keeps functioning in degraded mode.

Mock the boundary, then prove the failure behavior — not just the success behavior.

A double must also cancel the way the real API does. `URLSessionWebSocketTask.receive()` has
no task-cancellation handler, so a timeout that cancels a task group still waits until the
socket closes; close the socket first. A fake built on cancellable `Task.sleep` hides that
bug, so give timeout tests a fake that resumes only on close. Likewise, an unstructured
`Task` in a FIFO chain doesn't inherit its caller's cancellation: propagate it, and check
for cancellation after the predecessor finishes so a cancelled queued command isn't sent.

## SwiftData test target setup

When the test target has `TEST_HOST` set (test bundle loaded INTO the host app
process at runtime) and the project uses SwiftData `@Model` types, do NOT compile
shared model/service files into the test target. Use `@testable import <App>` only.
Two type copies in one process (`App.Foo` vs `AppTests.Foo`) crash SwiftData on
the first `context.insert(...)` with `EXC_BREAKPOINT` deep in `SwiftData.framework`.

This is silent because both compilations are valid in isolation, the build
succeeds, and CI rarely runs tests. Xcode 16+'s `PBXFileSystemSynchronizedRootGroup`
membership exception sets make it easy to add shared files to multiple
targets by accident.

## Running tests

```bash
# Via Xcode (boot the sim first; see simulator.md, which also covers pinning by UDID)
xcodebuild test -scheme [APP_NAME] -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -quiet

# Via slash command
/test {target}
```
