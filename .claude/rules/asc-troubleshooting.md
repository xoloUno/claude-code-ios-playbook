# App Store Connect Troubleshooting Rule

ASC's API and fastlane's wrappers around it have reliability quirks. When a
fastlane lane appears to hang or fail, check these first before assuming your work is
broken.

## Fastlane screenshot verify hang

**Symptom:** `bundle exec fastlane upload_screenshots` (or `release` with screenshots)
shows all file uploads completing in the first ~30 seconds, then enters a verify loop
emitting `Waiting for screenshots to appear before uploading. ... Server error got 500`
for tens of minutes.

**Cause:** Fastlane polls ASC after upload to confirm files are visible. ASC's verify
endpoint returns 500 transiently under high load. Fastlane retries up to its
`screenshot_processing_timeout` (default 3600s = one hour) before giving up. The files
uploaded successfully — fastlane just can't confirm.

**Fix — don't wait, verify directly:**

1. `Ctrl-C` (or `TaskStop` if running via the Task agent) the lane.
2. Run a direct ASC API query (`scripts/asc-query.rb` below) to list screenshot sets
   per locale. If state shows `COMPLETE` for all sets, **you're done** — fastlane's
   verify was just stuck.
3. If state shows missing files, re-run `upload_screenshots`. Let it complete the file
   upload phase only, then kill it before the retry loop begins (watch for the
   `Waiting for screenshots to appear` log line).

This is an ASC reliability issue, not a fastlane bug — Apple's verify endpoint flakes
under high load.

## ASC direct-query helper

Keep a small script around for ASC API sanity checks. Useful for: build state
(`PROCESSING` / `VALID` / `INVALID`), version state (`PREPARE_FOR_SUBMISSION` /
`WAITING_FOR_REVIEW` / `IN_REVIEW`), screenshot set state, build attachment, and
anything else fastlane can't quickly tell you.

`scripts/asc-query.rb`:

```ruby
#!/usr/bin/env ruby
# Direct ASC API query helper. Sources .env.fastlane for credentials.
#
# Usage:
#   ./scripts/asc-query.rb apps/{app_id}/builds?limit=5
#   ./scripts/asc-query.rb apps/{app_id}/appStoreVersions

require "jwt"
require "json"
require "net/http"
require "openssl"
require "uri"

key_id    = ENV["ASC_KEY_ID"]    or abort("ASC_KEY_ID missing — source .env.fastlane")
issuer_id = ENV["ASC_ISSUER_ID"] or abort("ASC_ISSUER_ID missing")
key_path  = File.expand_path(ENV["ASC_KEY_FILEPATH"] || abort("ASC_KEY_FILEPATH missing"))

private_key = OpenSSL::PKey.read(File.read(key_path))
payload = {
  iss: issuer_id,
  iat: Time.now.to_i,
  exp: Time.now.to_i + (20 * 60),
  aud: "appstoreconnect-v1"
}
token = JWT.encode(payload, private_key, "ES256", { kid: key_id, typ: "JWT" })

path = ARGV[0] or abort("Usage: asc-query.rb <api-path>\nExample: apps/{app_id}/builds")
uri = URI("https://api.appstoreconnect.apple.com/v1/#{path}")

req = Net::HTTP::Get.new(uri)
req["Authorization"] = "Bearer #{token}"

res = Net::HTTP.start(uri.host, uri.port, use_ssl: true) { |http| http.request(req) }

if res.is_a?(Net::HTTPSuccess)
  puts JSON.pretty_generate(JSON.parse(res.body))
else
  warn "HTTP #{res.code}: #{res.body}"
  exit 1
end
```

Make executable: `chmod +x scripts/asc-query.rb`.

Bash wrapper if preferred (sources `.env.fastlane` automatically):

```bash
#!/usr/bin/env bash
# scripts/asc-query.sh — convenience wrapper
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ -f "$ROOT/.env.fastlane" ] && set -a && . "$ROOT/.env.fastlane" && set +a
exec "$ROOT/scripts/asc-query.rb" "$@"
```

## Common queries

| Goal | Path |
|---|---|
| List recent builds | `apps/{app_id}/builds?limit=5` |
| Check build processing state | `builds/{build_id}` (look at `attributes.processingState`) |
| List versions and their state | `apps/{app_id}/appStoreVersions` |
| Inspect screenshot sets for a locale | `appStoreVersionLocalizations/{loc_id}/appScreenshotSets` |
| List screenshots in a set | `appScreenshotSets/{set_id}/appScreenshots` |

Find `app_id` once via `apps?filter[bundleId]={bundle.id}` and stash it in `.env.fastlane`
or `.env.project` for reuse.

## When NOT to use this

Don't reach for the direct API for routine work — fastlane is the right tool for normal
metadata sync and uploads. Use the helper when:

- A fastlane lane appears stuck in a verify/poll loop and you suspect ASC flakiness
- You need to confirm state without running a fastlane lane (faster)
- You're scripting a check that fastlane doesn't expose cleanly
