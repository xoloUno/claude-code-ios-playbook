# Metadata Translation Rule

App Store metadata is multi-locale: `fastlane/metadata/<locale>/*.txt`. The
**en-US locale is the source of truth** — edits happen there during dev
cycles. Other locales (es-ES, fr-FR, de-DE, etc.) are derived translations.

## Two translation surfaces — only one is this rule's job

An app has two localization surfaces with different owners:

1. **In-app strings (`.xcstrings` String Catalogs)** — first-party owner is
   **Xcode 27's localization agents** (coordinator + sub-agents over the
   String Catalog MCP tools; output is marked "Machine Translated"; the
   Generate Translations button covers per-string passes). Don't rebuild that
   flow here — see `wwdc26-ios27.md`.
2. **App Store metadata (`fastlane/metadata/<locale>/`)** — stays
   playbook-owned. The release-time procedure below is unchanged.

**Shared glossary: `TRANSLATION.md`.** Keep one project-level glossary file,
referenced from the project's `CLAUDE.md`, that both surfaces consume —
Xcode's localization agents auto-read `CLAUDE.md`/`AGENTS.md` and the files
they reference; the release-time procedure below reads it too. It holds:

- App-specific terms and their chosen translation per locale (decide once,
  reuse everywhere — app name handling especially)
- Strings that must NOT be translated (brand names, feature names kept in
  English)
- Regional variants where one language splits (es-ES vs es-419, pt-PT vs
  pt-BR) — Apple ships per-locale style guides for 16 locales but **none for
  Spanish or Portuguese**, so for es/pt the glossary is the only style
  authority. (Real catch: one app's `es` locale turned out to be
  Latin-American Spanish — "Destacadas"/"Agrega" — so Spain users were
  getting LatAm terms; a glossary makes that decision visible.)
- Apple's own per-locale product terminology — app-agnostic and identical
  across every iOS app, so never re-translate it. Seed examples: "Pinned" →
  Fijadas (es-ES) vs Destacadas (es-419); Health app → Salud / Santé /
  Salute / Saúde / ヘルスケア / 건강 / 健康; Live Activity → activité en
  direct (fr) / Live-Aktivität (de); Dynamic Island → 灵动岛 /
  ダイナミックアイランド. Sourcing method when a term isn't in the glossary
  yet: set the per-app language on a device and read the term off Apple's
  own stock apps, or use Apple's published localization glossaries.

**In-app strings quoted in metadata are extracted, never translated.** When
release notes or a description quote UI verbatim ("Pinned", a button label),
the source of truth is the app's own `Localizable.xcstrings` — hand-translating
the quote diverges from what users actually see on screen. Extract per locale:

```sh
python3 -c 'import json; d=json.load(open("<App>/Localizable.xcstrings"))["strings"]; \
  [print(loc, locs[loc]["stringUnit"]["value"]) for k in ["Pinned"] \
   for locs in [d[k]["localizations"]] for loc in sorted(locs)]'
```

This keeps in-app strings and ASC metadata using the same vocabulary even
though different agents translate them at different times.

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
   - Honors the project's `TRANSLATION.md` glossary if present (chosen
     terms, do-not-translate list, regional variants)
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
