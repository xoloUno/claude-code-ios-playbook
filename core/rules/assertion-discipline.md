# Assertion Discipline Rule

Some claims are too costly to get wrong. When planning or recommending an action, verify
before asserting in these high-stakes categories — do not recall from training memory.

This extends the auto-memory "Before recommending from memory" rule (which covers
file paths, function names, and feature flags). Same principle, wider scope.

## Categories that require verification

### App Store rendering & submission rules

Before claiming what the App Store does or doesn't render automatically (frames, chrome,
captions, scaling), verify against:
- Apple's marketing/screenshot guidelines on developer.apple.com
- A live App Store check on the target platform when possible
- The current `fastlane/deliver/lib/deliver/app_screenshot.rb` `DEVICE_TYPE_TO_DIMENSIONS`
  map for accepted dimensions per device class

Common false claims to watch for: "watch screenshots get a stylized watch frame
automatically" (false — they render as flat rectangles), "iPhone screenshots accept
alpha" (true) vs. "watch screenshots accept alpha" (false — `IMAGE_ALPHA_NOT_ALLOWED`).

### Repo visibility & GitHub Pages

Before recommending a repo visibility toggle (public ↔ private) or a GH Pages tier
change, run:

```bash
git remote -v
gh repo view --json visibility,owner,name
gh api repos/{owner}/{repo}/pages 2>/dev/null  # Pages config if any
```

Recommending "make the repo public to fix Pages" without checking can expose all source
code. Free-tier GH Pages now works for private repos in many configurations — check the
current state before suggesting visibility changes.

### Fastlane / ASC operational behavior

Before claiming what fastlane will do (timeout values, retry behavior, metadata sync
semantics) or what ASC accepts (image dimensions, alpha channels, version-state
transitions), verify by:
- Reading the relevant `fastlane/<tool>/lib/...` source for the version installed
- Querying the ASC API directly with a JWT'd helper (see `asc-troubleshooting.md`)
- Checking Apple's "App Store Connect API" reference

### Simulator / device capabilities

Before claiming a simulator can or can't do something (camera, biometrics, ApplePay,
push, certain HealthKit APIs), confirm with `xcrun simctl` introspection or by trying
the operation. Many capabilities are simulator-version-specific.

## How to apply

When you catch yourself about to assert in one of these categories, pause and ask:
"Have I checked this in this session, or am I recalling from training?" If it's recall,
check first, even if it costs an extra tool call. One extra check is cheap; a
confidently wrong recommendation in these categories is expensive — lost work,
exposed source, days of iteration on a screenshot pipeline that won't pass review.

## Why this rule exists

This rule was added after a planning session where two factual mistakes landed in
quick succession: claiming the App Store renders watch screenshots inside a stylized
frame (false — flat rectangles), and recommending a private→public repo toggle to "fix"
GH Pages (would have exposed all source). Both came from training memory, both were
caught by the user. High-stakes claim categories need the same verify-first
discipline already applied to code paths and feature flags.
