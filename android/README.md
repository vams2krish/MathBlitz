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

For a physical Android device, open Settings in the app and use your computer's
LAN address, for example:

```text
http://192.168.1.25:8000
```

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
