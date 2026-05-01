# Legal URLs Rule

Privacy, terms, marketing, and support URLs live in many places: Swift code (in-app
SafariView links), and across all locale-specific fastlane metadata files (`privacy_url.txt`,
`marketing_url.txt`, `support_url.txt`, **and embedded URLs inside `description.txt`**).
For an app with 12 locales, that's 36+ files plus Swift code — a 38+-file scavenger hunt
when the host changes.

**Plan for the URL host moving at least once during the app's life.** Common scenarios:
free GitHub Pages → custom domain at launch, hosting subscription expiration, consolidating
legal pages for multiple apps under one domain.

## The pattern

Two small files give a single source of truth and a one-shot migration command.

### 1. Swift constant

`<App>/Configuration/LegalURLs.swift`:

```swift
import Foundation

enum LegalURLs {
    static let base = URL(string: "https://your-host.com/your-path")!
    static let privacy = base.appendingPathComponent("privacy.html")
    static let terms = base.appendingPathComponent("terms.html")
}
```

Reference `LegalURLs.privacy` / `LegalURLs.terms` from every SwiftUI view that links to
legal pages. Never hardcode the URL string in views.

### 2. Update script

`scripts/update-legal-urls.sh` — idempotent, takes a base URL, rewrites the Swift file
plus every locale's metadata files in one shot:

```bash
#!/usr/bin/env bash
# Update privacy/terms/marketing/support URLs everywhere in one shot.
#
# Usage:
#   ./scripts/update-legal-urls.sh https://your-new-host.com/your-path
#
# Writes:
#   - <App>/Configuration/LegalURLs.swift          (base URL constant)
#   - fastlane/metadata/*/privacy_url.txt          (<base>/privacy.html)
#   - fastlane/metadata/*/marketing_url.txt        (<base>/)
#   - fastlane/metadata/*/support_url.txt          (<base>/)
#   - fastlane/metadata/*/description.txt          (rewrites embedded
#                                                   privacy.html / terms.html
#                                                   URLs in-place)
#
# Idempotent — running twice produces no diff.

set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <base-url>" >&2
  exit 1
fi

BASE_URL="${1%/}"  # strip trailing slash

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SWIFT_FILE="$REPO_ROOT/<App>/Configuration/LegalURLs.swift"   # adjust per project
METADATA_DIR="$REPO_ROOT/fastlane/metadata"

if [ ! -d "$METADATA_DIR" ]; then
  echo "❌ fastlane/metadata not found at $METADATA_DIR" >&2
  exit 1
fi

# 1. LegalURLs.swift — overwrite from heredoc.
mkdir -p "$(dirname "$SWIFT_FILE")"
cat > "$SWIFT_FILE" <<EOF
import Foundation

enum LegalURLs {
    static let base = URL(string: "$BASE_URL")!
    static let privacy = base.appendingPathComponent("privacy.html")
    static let terms = base.appendingPathComponent("terms.html")
}
EOF
echo "✅ wrote $SWIFT_FILE"

# 2. Per-locale URL files. Iterate actual locale dirs so we don't hardcode
#    a list that drifts from reality.
LOCALE_COUNT=0
for locale_dir in "$METADATA_DIR"/*/; do
  printf '%s' "$BASE_URL/privacy.html" > "$locale_dir/privacy_url.txt"
  printf '%s' "$BASE_URL/" > "$locale_dir/marketing_url.txt"
  printf '%s' "$BASE_URL/" > "$locale_dir/support_url.txt"
  LOCALE_COUNT=$((LOCALE_COUNT + 1))
done
echo "✅ updated privacy/marketing/support URLs in $LOCALE_COUNT locales"

# 3. description.txt — rewrite embedded privacy.html / terms.html URLs.
#    Apple's EULA and any unrelated link is untouched because the pattern
#    matches only URLs ending in /privacy.html or /terms.html.
DESC_COUNT=0
for locale_dir in "$METADATA_DIR"/*/; do
  desc="$locale_dir/description.txt"
  [ -f "$desc" ] || continue
  sed -E -i '' \
    -e "s|https://[^[:space:]]+/privacy\\.html|$BASE_URL/privacy.html|g" \
    -e "s|https://[^[:space:]]+/terms\\.html|$BASE_URL/terms.html|g" \
    "$desc"
  DESC_COUNT=$((DESC_COUNT + 1))
done
echo "✅ rewrote privacy/terms URLs inside $DESC_COUNT description.txt files"

echo ""
echo "Base URL: $BASE_URL"
echo "Run: bundle exec fastlane upload_metadata  # to push to ASC"
```

## Migration workflow

When the URL host changes:

```bash
./scripts/update-legal-urls.sh https://new-host.com/legal
git diff   # review — should be a clean sweep across Swift + all locales + description.txt
bundle exec fastlane upload_metadata
```

## Why the description.txt rewrite matters

App descriptions often embed privacy/terms links inline ("Read our [Privacy Policy](https://...)").
Without the in-place description rewrite, the `_url.txt` files point to the new host
but the visible description text still links to the old (potentially dead) URL — and
ASC's review can flag a broken privacy link in the description even when the dedicated
`privacy_url` field is correct.

The `sed` pattern matches only URLs ending in `/privacy.html` or `/terms.html`, so
Apple's EULA URL and any unrelated marketing links are left untouched.

## Rules

- **Never hardcode** privacy/terms URLs in Swift views or metadata files.
- **Always reference** `LegalURLs.privacy` / `LegalURLs.terms` from Swift.
- **When the host changes**, run `./scripts/update-legal-urls.sh <new-base>` — never
  edit individual files by hand.
- **The script is idempotent** — running it twice produces no diff. Safe to re-run
  to verify state.
