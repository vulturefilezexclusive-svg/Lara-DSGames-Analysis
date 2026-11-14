# Lara integration and rollback plan

## Baseline protection

1. Treat the existing Lara v0.2 IPA and its recorded SHA-256 values as immutable reference inputs.
2. Do not overwrite the baseline IPA, its embedded frameworks, or its signing assets.
3. Make all future changes on a separate integration branch or a clearly named candidate build.
4. Record source commit, toolchain version, deployment target, entitlements, and artifact hashes for every candidate.
5. Keep analysis reports additive under reports/; keep generated candidate binaries in a separate build/artifacts location.

## Integration gates

### Gate A — static compatibility
- Dependency/install-name/rpath inventory has completed for both libraries in both apps.
- Objective-C metadata inventory has completed and is compared.
- Candidate APIs have reliable prototypes and data-layout evidence.
- No unresolved dependency, architecture, or minimum-OS conflict remains.

### Gate B — isolated implementation
- Implement only documented, supported interfaces in Lara's own process.
- Prefer Lara's existing implementation where it already satisfies the product requirement.
- Add a narrow adapter layer with explicit input validation, error mapping, lifecycle ownership, and logging.
- Keep feature flags so the candidate path can be disabled without reinstalling or migrating user data.
- Do not introduce code for attaching to, reading from, or modifying unrelated third-party processes.

### Gate C — validation
- Build arm64 and arm64e slices as required by the target environment.
- Verify load commands, linked frameworks, signing, entitlements, and deployment target.
- Run unit tests and owned-process integration tests.
- Compare baseline and candidate launch, stability, memory, and functional behavior.
- Reject the candidate on crashes, unresolved symbols, signature failures, unexpected permissions, or regressions.

## Rollback

1. Disable the candidate feature flag.
2. Reinstall the last accepted Lara baseline build if the candidate cannot be disabled cleanly.
3. Preserve candidate logs and crash reports for diagnosis.
4. Revert only the integration commits; never rewrite or delete the baseline reference.
5. Re-run baseline smoke tests and verify the baseline artifact hash.

## Acceptance criteria

A candidate is eligible for a trial build only when all Gate A findings are documented, Gate B changes are isolated, Gate C tests pass, and the final IPA's hash/signature/install metadata are recorded. Unknown ABI contracts are blockers, not assumptions.
