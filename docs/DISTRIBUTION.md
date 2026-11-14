# MathBlitz 2.1 Distribution

| Target | Build and availability |
| --- | --- |
| Web | [Live Vercel guest app](https://mathblitz-eight.vercel.app/), no sign-in required |
| Windows | `artifacts/windows/MathBlitz-2.1.0-Windows-x64-Setup.exe`, unsigned x64 installer |
| Android | [Download APK](https://mathblitz-eight.vercel.app/downloads/MathBlitz-2.1.0-Android.apk), debug-signed sideload build for Android 6.0+ |
| iOS | iPhone/iPad Xcode project and unsigned Apple Silicon simulator build workflow. No TestFlight build yet. |

Guest progress and sound preferences are stored on the device. Recent history is capped at 1,000 attempts. Different devices, browsers, and the FastAPI account edition do not share guest data. Focus music is opt-in per session and pauses when the app is hidden. The Windows, Android, and iOS packages bundle the web assets and puzzle bank; no backend, signup, or network connection is required for guest practice.

## Windows

Requires Node.js 24 and Windows x64. The logo and icons are committed; no image tools are required for a normal build.

```powershell
npm.cmd ci --prefix windows
npm.cmd --prefix windows run build
```

Open the generated setup executable and follow the per-user installer. This build has no Authenticode publisher signature, so Windows may show a SmartScreen warning. Only install a build from a trusted source. To run the unpacked executable without installing, run `artifacts/windows/win-unpacked/MathBlitz.exe`.

## Android

Requires the Android SDK (build tools, platform 35 or newer, and command-line tools), JDK 17, and Node.js 24. Set `ANDROID_HOME` and `JAVA_HOME` if they are not already configured.

```powershell
.\android\build.ps1 -Guest
adb install -r .\android\build-guest\MathBlitz-2.1.0-Android.apk
```

Alternatively open the APK on your Android phone and allow installation from the trusted app you used to open it. The demo APK uses a persistent local debug key. Keep the same key for upgrades; an APK signed with another key cannot replace an installed copy. This is a sideload build, not a Play Store release. The guest package `com.mathblitz.guest` can coexist with the prior client `com.mathblitz.mobile`.

## iOS And TestFlight

The Xcode project uses Capacitor with bundled guest content. On macOS, with [Apple's supported version of Xcode](https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds/) and Node.js 24:

```sh
npm ci --prefix ios
npm --prefix ios run sync
open ios/native/App/App.xcodeproj
```

Run the `App` scheme on a simulator first. The `Package MathBlitz` GitHub workflow also compiles an unsigned Apple Silicon simulator app. Its ZIP is not an IPA and cannot be installed on an iPhone or uploaded to TestFlight.

1. Enroll in the [Apple Developer Program](https://developer.apple.com/programs/whats-included/) and sign in to Xcode with the authorized Apple account.
2. Register an available bundle ID (the project starts with `com.mathblitz.ios`) and create the matching App Store Connect app record. In Xcode, select your team under Signing & Capabilities and enable automatic signing.
3. Select a generic iOS device, choose Product > Archive, then use Distribute App > App Store Connect to upload the signed build. Set a new build number for every upload.
4. Once processing finishes, use [TestFlight](https://developer.apple.com/testflight/) in App Store Connect to create an internal tester group and invite eligible teammates. External testers require beta review for the first build. App metadata, privacy answers, and review decisions are managed by the Apple account owner.

## Reproduce The Guest Web Build

```powershell
.\.venv\Scripts\python.exe -m scripts.build_guest_catalog
node --test tests/guest.test.mjs
node scripts/stage_guest.mjs .output/guest
```

For Vercel, import this repository as a static project using the checked-in `vercel.json`, or use `vercel --prod` from an authorized account. The current live edition was deployed from the staged static files with the signed APK added under `downloads/`. Attach the APK again when manually publishing a new build; it is not checked into Git. Automatic GitHub deployments require linking the GitHub Login Connection in Vercel first. The [free Hobby plan](https://vercel.com/docs/plans/hobby) is intended for personal, non-commercial use.

Do not deploy a SQLite file or include account data in a serverless static bundle. Hosted accounts, global leaderboards, PostgreSQL, and shared Redis are **not** part of this deployment. The self-hosted backend remains independent.
