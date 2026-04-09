---
description: Privacy manifest (PrivacyInfo.xcprivacy) maintenance rules
globs: **/*.xcprivacy, **/*.swift
---

# Privacy Manifest Rule

Apple requires a privacy manifest (`PrivacyInfo.xcprivacy`) declaring all "required reason
APIs" your app uses. App Store review will reject apps with undeclared API usage.

## When to update the manifest

Update `PrivacyInfo.xcprivacy` whenever you add code that uses any of these API categories:

| API Category | Common triggers | Reason code |
|---|---|---|
| **UserDefaults** | `UserDefaults.standard`, `@AppStorage` | `CA92.1` (app-specific data) |
| **File timestamp** | `FileManager` `.creationDate`, `.modificationDate` | `C617.1` (inside app container) |
| **System boot time** | `ProcessInfo.processInfo.systemUptime` | `35F9.1` (measure elapsed time) |
| **Disk space** | `FileManager` `.volumeAvailableCapacityKey` | `E174.1` (check before writing) |
| **Active keyboards** | `UITextInputMode.activeInputModes` | `54BD.1` (local keyboard info) |

The bootstrap template includes `CA92.1` (UserDefaults) by default since virtually every
app uses it.

## How to update

Add a new entry to the `NSPrivacyAccessedAPITypes` array in `PrivacyInfo.xcprivacy`:

```xml
<dict>
    <key>NSPrivacyAccessedAPIType</key>
    <string>NSPrivacyAccessedAPICategoryFileTimestamp</string>
    <key>NSPrivacyAccessedAPITypeReasons</key>
    <array>
        <string>C617.1</string>
    </array>
</dict>
```

## Third-party SDKs

If adding a third-party SDK that accesses required-reason APIs, the SDK must include its
own privacy manifest in its bundle. Check the SDK's documentation. If it doesn't include
one, you may need to add its API declarations to your app's manifest.

## Tracking and data collection

If the app collects user data or uses any tracking frameworks:
- Set `NSPrivacyTracking` to `true` and list domains in `NSPrivacyTrackingDomains`
- Add collected data types to `NSPrivacyCollectedDataTypes` with purpose and linkability

For most solo indie v1 apps with no analytics SDK, these arrays stay empty.

## Verification

Before submission, use the **apple-docs MCP tool** or check Apple's documentation for the
current list of required-reason APIs — Apple updates this list periodically.
