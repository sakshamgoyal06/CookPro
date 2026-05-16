# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

CookPro is a native Android app (Java) built with Gradle 5.6.4 and Android Gradle Plugin 3.6.3. It targets Android SDK 29 (min SDK 16).

### Environment requirements

- **JDK 8** is required for Gradle builds (`JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64`).
- **Android SDK** is at `/opt/android-sdk` with platform `android-29` and build-tools `29.0.3`.
- Both `ANDROID_SDK_ROOT` and `ANDROID_HOME` must be set to `/opt/android-sdk`.
- The Android SDK `sdkmanager` requires JDK 17+ to run; use the system JDK 21 (`/usr/lib/jvm/java-21-openjdk-amd64`) only for `sdkmanager` commands.

### Build, test, and lint commands

All commands must be run from the repo root with the correct env vars:

```bash
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export ANDROID_SDK_ROOT=/opt/android-sdk
export ANDROID_HOME=/opt/android-sdk
```

| Task | Command |
|------|---------|
| Build debug APK | `./gradlew assembleDebug` |
| Run unit tests | `./gradlew test` |
| Run lint | `./gradlew lint` |
| Clean build | `./gradlew clean` |

### Gotchas

- Firebase dependencies (`firebase-auth`, `firebase-database`, `firebase-storage`) are declared in `app/build.gradle` but `google-services.json` is missing and the `com.google.gms.google-services` plugin is **not applied**. Firebase features are non-functional but do not block compilation.
- The `CalendarAdapter.java` file uses deprecated Android API calls — this produces compiler notes but not errors.
- Instrumented tests (`androidTest`) require a physical device or emulator and cannot run in headless CI.
- Lint reports are written to `app/build/reports/lint-results.html`.
