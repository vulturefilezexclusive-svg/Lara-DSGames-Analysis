# IPA archive and release-metadata gate

Static checks only. This does not execute either app or cryptographically verify Apple's signature on a device.

## Lara-v0.2 — FAIL

- [x] **ZIP CRC integrity** — All entries pass CRC
- [x] **Archive paths are confined** — 0 unsafe path(s)
- [x] **Exactly one app Info.plist** — Found 1
- [x] **CFBundleExecutable exists in app bundle** — Payload/lara.app/lara
- [x] **Bundle identifier present** — com.roooot.lara
- [x] **Version/build metadata present** — 0.2 / Release
- [ ] **CodeResources manifest present** — No CodeResources manifest
- [x] **Provisioning profile status recorded** — Absent; may be expected for unsigned/ad-hoc input
- [x] **Device ARM64 architecture present** — arm64e
- IPA size: 5474210
- IPA SHA-256: c8ba0fec11137d36732108afa8cb3da1947779745bc368ba7e78f1af993298a2
- Bundle ID: com.roooot.lara
- Version: 0.2
- Build: Release
- Minimum iOS: 16.0
- Architectures: arm64e

## DSGames-2.5 — PASS

- [x] **ZIP CRC integrity** — All entries pass CRC
- [x] **Archive paths are confined** — 0 unsafe path(s)
- [x] **Exactly one app Info.plist** — Found 1
- [x] **CFBundleExecutable exists in app bundle** — Payload/DSGames.app/DSGames
- [x] **Bundle identifier present** — com.dsgames.app
- [x] **Version/build metadata present** — 2.5 / 2026110402
- [x] **CodeResources manifest present** — Manifest found
- [x] **Provisioning profile status recorded** — Present (contents not decoded)
- [x] **Device ARM64 architecture present** — arm64e
- IPA size: 19684890
- IPA SHA-256: 84472e8069a14daaa4670590de10e0013a1dd0ee0fc7f9b772c70f2cd120f9f1
- Bundle ID: com.dsgames.app
- Version: 2.5
- Build: 2026110402
- Minimum iOS: 16.1
- Architectures: arm64e

## Interpretation

A CodeResources file or embedded profile is metadata evidence, not proof iOS will accept the signature.
Device installation still requires a valid signing chain, provisioning, entitlement authorization, and runtime validation.
The gate checks archive structure and declared metadata; it does not certify app behavior.
