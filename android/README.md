# MathBlitz Android

Native Android client for the MathBlitz FastAPI service.

## What It Includes

- Sign in and account creation.
- Scenario catalog from `/api/v1/activities`.
- Five difficulty levels.
- Timed task issue, hints, answer submission, and feedback.
- Dashboard and leaderboard summaries.
- Responsive phone/tablet layout with color-blind-friendly accents.
- Local API base URL setting.

## Local API URL

Android emulators cannot reach the host computer at `127.0.0.1`. The app
defaults to:

```text
http://10.0.2.2:8000
```

For a physical Android device, set the URL on the sign-in screen before
authenticating, or use Settings in the app. Use your computer's LAN address,
for example:

```text
http://192.168.1.25:8000
```

Changing the API URL clears the previous sign-in instead of sending its token
to a different server. The backend must listen on a reachable interface for
LAN access; keep this restricted to a trusted development network.

## Build Without Gradle

This repository includes a PowerShell build script that uses the installed
Android SDK command-line tools directly.

```powershell
cd android
.\build.ps1
```

The signed debug APK is written to:

```text
android/build/mathblitz-debug.apk
```

Install on a connected device or emulator:

```powershell
adb install -r .\build\mathblitz-debug.apk
```

The script retains `android/debug.keystore` across builds, outside the cleaned
`build/` directory. It adopts the old `build/debug.keystore` if present on the
first run of the updated script. Both key locations remain ignored by Git.
This is debug signing, not a release-key management pipeline.

The manifest currently declares minimum SDK 23 and target SDK 35. Version
`2.0.1` was built, installed, and exercised on an Android 16 emulator on
October 29, 2026. The live walkthrough covered sign-in, tasks, answer feedback,
progress, the library, settings, and portrait/landscape layouts. It does not
establish physical-device, tablet, older-version, or accessibility coverage.

See [the live verification report](../docs/DEMO_VERIFICATION.md) and
[README showcases](../README.md#android-showcase).
