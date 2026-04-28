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

## SwiftData test target setup

When the test target has `TEST_HOST` set (test bundle loaded INTO the host app
process at runtime) and the project uses SwiftData `@Model` types, do NOT compile
shared model/service files into the test target. Use `@testable import <App>` only.
Two type copies in one process (`App.Foo` vs `AppTests.Foo`) crash SwiftData hard
on the first `context.insert(...)` with `EXC_BREAKPOINT` deep in
`SwiftData.framework`.

This is silent because both compilations are valid in isolation, the build
succeeds, and CI rarely runs tests. Xcode 16+'s `PBXFileSystemSynchronizedRootGroup`
membership exception sets make it especially easy to add shared files to multiple
targets by accident.

## Running tests

```bash
# Via Xcode
xcodebuild test -scheme [APP_NAME] -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -quiet

# Via slash command
/test {target}
```
