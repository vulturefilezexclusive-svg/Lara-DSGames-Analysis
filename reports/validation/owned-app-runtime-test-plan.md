# Owned-app runtime validation harness plan

## Purpose
Validate Lara's own runtime and supported interfaces without enumerating, attaching to, reading, or modifying unrelated processes.

## Current status
The repository contains IPA inputs and static-analysis scripts, but no Lara source tree, Xcode project, or reproducible build settings. This document is therefore a test specification, not an executable XCTest target.

## Harness boundary
All runtime checks must execute inside Lara and inspect only Lara-owned state. The harness must not request task ports for other apps, inspect other processes' memory, inject code, synthesize input into other apps, or bypass platform authorization.

## Proposed XCTest groups

1. **Bundle and runtime identity**
   - Assert bundle identifier, version, build, and supported minimum OS.
   - Record device model family, OS version, and process architecture using public APIs.
   - Confirm app launch, foreground/background transitions, and clean termination.

2. **App-owned resource integrity**
   - Enumerate only resources inside the app bundle.
   - Verify expected bundled resource hashes against a checked-in manifest.
   - Parse known, app-owned Mach-O fixture files as data; do not load or execute them.

3. **Public API and permission behavior**
   - Exercise only documented APIs available to the app.
   - Verify denied permissions fail closed and produce actionable diagnostics.
   - Confirm unsupported capabilities are reported as unavailable rather than silently bypassed.

4. **Regression and stability**
   - Run launch, navigation, lifecycle, and resource-loading tests on the oldest supported iOS version and a current iOS version.
   - Capture crash logs and structured app-owned diagnostic output.
   - Confirm no regression in baseline Lara screens and normal app behavior.

## Acceptance criteria
- Tests run on a signed development build of Lara from its own source project.
- No test inspects or alters another process.
- All permission-denied paths fail closed.
- No crash during repeated launch/background/foreground cycles.
- Test results, device/OS metadata, and build commit are archived with the CI run.

## Required input to implement
A matching Lara source workspace containing the Xcode project/workspace, source files, package/dependency declarations, and build configuration. Signing assets are needed only for device installation and must be supplied through the user's secure signing workflow, not committed to this repository.
