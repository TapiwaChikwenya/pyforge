# PyForge for iOS

The `PyForge.xcodeproj` project is a native SwiftUI client for the existing
PyForge API. The current MVP supports the complete learning loop against a
**local-mode** server: curriculum, projects, exercises, checks, progress,
milestones, and interview practice.

## Run on an iPhone

### 1. Start PyForge on the Mac

From the repository root:

```bash
docker compose up -d --build
curl http://localhost:8000/healthz
```

The response should include `"ok": true` and `"mode": "local"`.

Find the Mac's Bonjour hostname:

```bash
scutil --get LocalHostName
```

If that prints `My-Mac`, the address to enter on the phone is normally:

```text
http://My-Mac.local:8000
```

The Mac and phone must be on the same trusted Wi-Fi network. If macOS asks,
allow incoming connections for Docker. A corporate or guest Wi-Fi network may
block device-to-device traffic; a personal hotspot or home network is usually
the simplest alternative.

### 2. Configure signing in Xcode

1. Open [`PyForge.xcodeproj`](PyForge.xcodeproj).
2. Select the **PyForge** project, then the **PyForge** target.
3. In **Signing & Capabilities**, confirm your Apple developer team.
4. If Xcode reports a signing conflict, change the bundle identifier to a
   unique value such as `com.yourname.PyForge`.
5. Connect the unlocked iPhone by cable, or pair it for wireless development.
6. Select the phone in Xcode's run-destination menu and press **Run**.

A free Apple ID can use a Personal Team for development installs, though those
builds need periodic re-signing. On a first install, iOS may ask you to enable
Developer Mode and trust the developer identity.

### 3. Connect the app

1. Tap the server icon in the app's top-right corner.
2. Replace `http://127.0.0.1:8000` with the Mac's `.local` address from step 1.
3. Tap **Test & Save**.
4. Accept the iOS local-network permission prompt.

`127.0.0.1` refers to the phone itself and is only the correct default for the
iOS Simulator. Prefer a `.local` hostname for a physical device; the app's
transport policy permits local-network HTTP for development and expects HTTPS
for a public server.

## Validate from the command line

The active command-line developer directory on this Mac may point at Command
Line Tools, so these commands explicitly select the installed Xcode:

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer \
  xcodebuild -project ios/PyForge.xcodeproj \
  -scheme PyForge \
  -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 16 Pro,OS=18.4' \
  CODE_SIGNING_ALLOWED=NO build

DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer \
  xcodebuild -project ios/PyForge.xcodeproj \
  -scheme PyForge \
  -destination 'platform=iOS Simulator,name=iPhone 16 Pro,OS=18.4' \
  CODE_SIGNING_ALLOWED=NO test
```

## Current boundaries

- Native exercise runs require local mode. Hosted mode deliberately has no
  `/api/run` endpoint, and the app communicates that constraint in the editor.
- GitHub sign-in and cross-device hosted progress are planned, not stubbed.
- Exercise drafts are not yet persisted if the view is closed.
Do not expose the local-mode server to an untrusted network. Its runner is
sandboxed for a learner's own machine, not designed as a public multi-tenant
execution service. Stop the stack when finished with `docker compose down`.

The implementation plan, acceptance criteria, and next-release backlog live in
[`docs/IOS_PROJECT_PLAN.md`](../docs/IOS_PROJECT_PLAN.md).

## Brand and interface

The production app icon is included as a 1024px opaque master in the asset
catalog. Its midnight-steel data forge, ember seam, and code-chevron geometry
also define the in-app design system: warm canvas backgrounds, dark technical
surfaces, ember actions, layered cards, rounded display type, and restrained
glow. The same brand mark is reused in loading, navigation, dashboard, and
server-connection states so the identity remains recognizable without relying
on the icon alone.
