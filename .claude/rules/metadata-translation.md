# Metadata Translation Rule

App Store metadata is multi-locale: `fastlane/metadata/<locale>/*.txt`. The
**en-US locale is the source of truth** — edits happen there during dev
cycles. Other locales (es-ES, fr-FR, de-DE, etc.) are derived translations.

## Token-efficient workflow

| Phase | What happens |
|---|---|
| Dev cycle | Edit en-US freely. `/wrapup` humanizes en-US when modified. |
| Drift period | Other locales lag behind en-US — expected, not a bug. |
| Release | `/release` retranslates all non-en-US locales fresh from current en-US, then uploads. |

Translation runs at the release-time gate, not every commit. Translation is
expensive to run continuously, and the locale files only matter when
uploading to ASC.

## Files that get translated

Translated (prose content):
- `description.txt`
- `name.txt`
- `subtitle.txt`
- `keywords.txt`
- `promotional_text.txt`
- `release_notes.txt`

Not translated (URLs/identifiers — handled by `legal-urls.md`):
- `marketing_url.txt`
- `privacy_url.txt`
- `support_url.txt`

## Release-time translation procedure

When `/release` runs (or a manual `/translate` pass), for each non-en-US
locale directory under `fastlane/metadata/`:

1. Read the current en-US file (source of truth — already humanized via
   `/wrapup` during dev cycles)
2. Read the locale's current file (for tone, formality, established
   phrasing — preserves voice across translations)
3. Generate a translation that:
   - Reflects the latest en-US content
   - Preserves the locale's existing tone and voice
   - Respects ASC character limits (table below)
   - Honors ASO conventions for the locale (keyword density, formality
     register, locale-specific marketing phrasing)
4. Show a diff (old locale file vs. proposed new translation)
5. Ask for approval before writing — translations are high-stakes
   (App Store rejection risk for bad translations; cultural missteps are
   not reversible without a new submission)
6. Write the new translation only after approval

## ASC character limits

Translations must stay under these per locale:

| File | Limit |
|---|---|
| `name.txt` | 30 |
| `subtitle.txt` | 30 |
| `keywords.txt` | 100 (comma-separated, no spaces after commas to save chars) |
| `promotional_text.txt` | 170 |
| `description.txt` | 4000 |
| `release_notes.txt` | 4000 |

Some locales (German especially) tend to run longer than English. If a
translation exceeds the limit, shorten by cutting non-essential clauses
rather than truncating mid-sentence.

## Skip conditions

- Skip if `fastlane/metadata/` only contains en-US (single-locale app —
  common for v1)
- Skip locales where the file is byte-identical to en-US (already up to
  date, or the locale falls back to en-US in ASC)
- Skip files that don't exist in the locale (don't create new files
  speculatively — a missing file means the locale falls back to en-US,
  which is fine)

## Why this rule exists

Two failure modes this prevents:

1. **Stale translations shipped to ASC.** Without an explicit release-time
   translation step, translations drift indefinitely and eventually ship
   with content that doesn't match en-US. Reviewers and users see the
   mismatch.
2. **Token waste on every dev session.** Running translation logic per
   `/wrapup` would burn tokens N×M times (locales × files) for content the
   user is still iterating on. Release-time is the natural boundary —
   translation only matters when uploading.
