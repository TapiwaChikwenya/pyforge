# PyForge iOS project plan

## Product goal

Ship a native iPhone companion for PyForge that lets a learner complete the
core learning loop against the existing FastAPI service: discover the path,
open a project, solve an exercise, run its checks, and see progress persist.

The first release deliberately targets **local mode**. The iPhone connects to
the PyForge server running on the learner's Mac, and the server uses the same
sandboxed exercise runner and progress store as the web app. Hosted mode can be
browsed, but hosted exercise execution and GitHub authentication are follow-up
work because the hosted server intentionally exposes no `/api/run` endpoint.

## Assumptions and decisions

- SwiftUI, structured concurrency, and `URLSession`; no third-party packages.
- iOS 17 is the minimum deployment target. This supports modern navigation and
  observation APIs while covering currently supported iPhones.
- The API remains the source of truth. Curriculum content is not duplicated in
  the app, so web and iOS cannot silently drift.
- Exercise code executes on the Mac's local PyForge server, never inside the
  iOS process. This preserves the existing sandbox and avoids shipping an
  incomplete Python runtime.
- The server address is user-configurable and persisted on-device. Simulator
  development defaults to `http://127.0.0.1:8000`; a physical phone should use
  the Mac's Bonjour address, such as `http://my-mac.local:8000`.
- Local-network HTTP is allowed only to support development against a Mac on
  the same network. Production hosted deployments should use HTTPS.
- Authentication, certificate/portfolio export, review queues, mentor mode,
  and community solutions are post-MVP stories.

## Architecture

```text
SwiftUI views -> AppModel (@MainActor) -> PyForgeAPI -> FastAPI
     |                  |
     |                  +-> connection, curriculum, selected project, errors
     +-> NavigationStack, native editor, progress and settings
```

- `Models/`: Codable API representations with forward-compatible optional
  fields.
- `Networking/`: one typed API client and actionable HTTP/decoding errors.
- `App/`: app entry point and shared state model.
- `Features/`: dashboard, project workspace, exercise runner, and settings.
- `DesignSystem/`: reusable brand colors and compact UI components.

## Visual direction

PyForge should feel like a premium technical workshop rather than a generic
course catalog. The icon and interface share one visual language:

- midnight and indigo represent the technical workspace;
- molten ember marks primary actions, progress, and moments of success;
- layered steel surfaces echo data stacks and the forge/anvil silhouette;
- warm off-white canvas keeps dense learning content readable;
- rounded, heavy headings create confidence while monospaced details retain a
  developer-tool character;
- depth and glow are deliberate and restrained so accessibility and content
  hierarchy stay ahead of decoration.

The app must remain usable with Dynamic Type, VoiceOver labels, light or dark
appearance, and Reduced Motion. Brand recognition cannot depend on color alone.

## User stories

### P0 · phone-testable MVP

#### US-00 — Experience a coherent PyForge brand

As a learner, I want the app to feel focused, beautiful, and purpose-built so
that returning to practice feels motivating.

Acceptance criteria:

- A production-ready opaque 1024px app icon is present and legible at small
  home-screen sizes.
- The icon's ember, midnight, steel, layering, and code cues recur throughout
  the interface without overpowering curriculum content.
- Loading, connected, empty, failure, and execution-result states use the same
  visual system.
- Primary actions, progress, navigation, and cards have consistent hierarchy.
- The dashboard is visually inspected in an iPhone simulator after rendering.

#### US-01 — Connect to a PyForge server

As a learner, I want to configure the server running on my Mac so that my phone
can use the same curriculum and execution environment.

Acceptance criteria:

- The app shows the current endpoint and connection state.
- A learner can edit, validate, and persist an HTTP or HTTPS base URL.
- Save performs a real `/healthz` check and reports a useful failure.
- The app explains the simulator versus physical-device address difference.
- Local-network permission has a clear purpose string.

#### US-02 — See the learning path and progress

As a learner, I want a staged curriculum dashboard so that I know what to learn
next and how far I have progressed.

Acceptance criteria:

- The app loads `/api/curriculum` and renders all stages in server order.
- Each project shows title, level, estimated time, technology tags, and exercise
  completion.
- Overall exercise progress is visible and refreshable.
- Empty, loading, offline, and retry states are distinct and accessible.

#### US-03 — Understand a project

As a learner, I want a project workspace so that I can understand the brief,
environment, exercises, milestones, and interview topics.

Acceptance criteria:

- Opening a project loads `/api/project/{id}`.
- Overview presents the project brief, stack command, and technology list.
- Exercises show completion and runtime requirements.
- Milestones and interview prompts are available in dedicated sections.

#### US-04 — Solve and run an exercise

As a learner, I want to edit starter code and run checks so that I get immediate
feedback on my solution.

Acceptance criteria:

- The editor starts with the server-provided starter code and uses a monospaced
  font with keyboard-friendly editing.
- Instructions, objectives, progressive hints, and useful resources are visible.
- Run posts project id, exercise id, and code to `/api/run`.
- While running, duplicate submissions are prevented.
- Pass, failure, stdout, stderr, and timeout/error states are visually distinct.
- A passing result updates project and dashboard progress without restarting.
- Hosted mode clearly explains why native Run is unavailable.

#### US-05 — Track project milestones

As a learner, I want to toggle milestones so that implementation work outside
the exercises is reflected in my progress.

Acceptance criteria:

- Completed milestones match server state.
- Tapping a milestone writes through `/api/milestone`.
- Optimistic UI rolls back and reports an error when the request fails.

#### US-06 — Practice interview questions

As a learner, I want to reveal interview answers deliberately so that I can
self-test instead of passively reading.

Acceptance criteria:

- Questions show difficulty and topics.
- Answers are hidden initially and revealed individually.
- The explanation is displayed with the revealed answer.

### P1 · next release

- US-07: Resume unsent exercise drafts locally per exercise.
- US-08: Add native linting feedback from local `/api/lint`.
- US-09: Surface spaced review and mentor debrief flows.
- US-10: Unlock and read community solutions after a pass.
- US-11: View and share portfolio markdown and the certificate.
- US-12: Add accessibility UI tests, dynamic-type screenshots, and offline cache.

### P2 · hosted distribution

- US-13: GitHub sign-in using an ASWebAuthenticationSession-compatible backend
  callback and secure cookie/token handoff.
- US-14: Execute browser-compatible exercises in an isolated on-device runtime,
  or provide a secured execution service with explicit resource limits.
- US-15: Anonymous hosted progress and account merge parity with the web app.
- US-16: App Store assets, privacy manifest, analytics consent, and release CI.

## Delivery sequence

1. Contract and foundation: models, networking, shared state, Xcode project.
2. US-01 and US-02: settings/connection flow and curriculum dashboard.
3. US-03 and US-06: project workspace and interview study flow.
4. US-04: native exercise editor, runner feedback, progress refresh.
5. US-05: milestones with rollback-safe persistence.
6. Unit tests, simulator build, physical-device runbook, and handoff.

## Definition of done for this iteration

- The checked-in `.xcodeproj` opens without a generator or package install.
- Debug simulator compilation and unit tests pass using the installed Xcode.
- The app contains no secrets or developer-specific signing identifiers.
- A developer can start PyForge, configure their signing team, connect an
  iPhone, and run the app by following `ios/README.md`.
- Known hosted-mode limitations are visible in-product and documented.
