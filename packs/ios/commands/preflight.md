Pre-deploy gate — validate everything before kicking off a build/upload cycle.

Run this before /deploy or /release. Catches missing simulators, ASC character-limit
violations, and forgotten metadata fields — all of which fail late and waste a full
build cycle.

Steps:

1. **Simulator availability** — Run `xcrun simctl list devices available` and confirm
   the project's required simulators exist. Standard set:
   - iPhone 6.9" screenshots: iPhone 17 Pro Max
   - iPad 13" screenshots: iPad Pro 13-inch (M5)
   - Build/run target: __PRIMARY_SIM__
   Skip iPad checks if the project does not ship iPad. If a required sim is missing,
   FAIL — suggest `xcrun simctl create` or downloading the runtime via
   Xcode > Settings > Platforms.

2. **ASC metadata character limits** — For each locale directory under
   `fastlane/metadata/`, validate text files against ASC limits using `wc -m`
   (subtract 1 for trailing newline):
   - `name.txt` ≤ 30
   - `subtitle.txt` ≤ 30
   - `keywords.txt` ≤ 100
   - `description.txt` ≤ 4000
   - `release_notes.txt` ≤ 4000
   - `promotional_text.txt` ≤ 170
   Report file path, current count, and overage for any file over limit.

3. **Metadata field completeness** — For each locale dir, confirm BOTH
   `release_notes.txt` AND `promotional_text.txt` exist and are non-empty (not just
   whitespace, not just stale placeholders like "Initial release."). Catches
   multi-locale ships where a field gets forgotten on some locales.

4. **Git state** —
   - `git status` must be clean (warn if untracked files)
   - Current branch must NOT be `main` — should be `dev`, `release/*`, or feature/*
   - Branch should be pushed and up-to-date with origin

5. **Version sanity** — Read `MARKETING_VERSION` from `project.yml`. Ask the user
   what version they think they're shipping. If mismatch, FAIL.

6. **Build number** — Read `CURRENT_PROJECT_VERSION` from `project.yml`. Check whether
   a git tag like `v<MARKETING>-beta.<BUILD>` already exists. If yes, warn — the build
   number likely needs a bump.

Present results as a PASS / FAIL / WARN table:

```
## Preflight — v1.2.0 build 71

| Check | Status | Detail |
|---|---|---|
| Simulators | ✅ PASS | iPhone 17 Pro Max, iPad Pro 13" M5 available |
| Metadata char limits | ❌ FAIL | en-US/subtitle.txt: 31 chars (max 30) |
| Metadata completeness | ✅ PASS | All 12 locales have release_notes + promotional_text |
| Git state | ⚠️ WARN | On dev, 2 unpushed commits |
| Version | ✅ PASS | MARKETING_VERSION 1.2.0 matches |
| Build number | ✅ PASS | 71 (no existing tag) |

Overall: ❌ FAIL — fix metadata char limits before deploy.
```

If any check FAILs, refuse to proceed and offer to fix the failing items. Only after
all checks PASS (or the user explicitly overrides) should /deploy or /release be invoked.
