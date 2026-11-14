# iOS validation checklist — Lara compatibility milestone

## Static checks
- [ ] Both dylibs in both IPAs are uniquely located and hashed.
- [ ] ARM64 and ARM64e slices are present and individually inspected.
- [ ] Install names, linked dylibs, weak/re-export/upward dependencies, and rpaths are inventoried.
- [ ] Minimum iOS and SDK load-command metadata are recorded.
- [ ] Export trie presence and exported symbol names are cross-checked.
- [ ] Objective-C class/category/selector reference sections are inventoried.
- [ ] No candidate API is marked compatible solely from a matching symbol name.

## Build and signing checks
- [ ] Build succeeds for the intended device architectures.
- [ ] No missing or duplicate embedded framework is present.
- [ ] All required linked libraries resolve.
- [ ] Code signature verifies after packaging.
- [ ] Entitlements are limited to those legitimately available to the app.
- [ ] Bundle ID, provisioning profile, minimum OS, and device family are consistent.

## Runtime checks on an owned app/test target
- [ ] Clean install, first launch, background/foreground, and clean termination pass.
- [ ] Each candidate API is tested with valid, invalid, and boundary inputs.
- [ ] Error paths return safely and do not leave resources or threads active.
- [ ] Repeated start/stop and app lifecycle transitions are stable.
- [ ] No unexpected permission prompts or access outside the app's own test boundary.
- [ ] Crash logs, console logs, and performance measurements are retained.

## Release decision
- [ ] All blockers resolved or explicitly excluded from scope.
- [ ] Baseline and candidate hashes recorded.
- [ ] Rollback path tested.
- [ ] Final IPA and report set archived with source commit and toolchain metadata.

**Pass condition:** every applicable item is evidenced. A successful compile alone is not a compatibility pass.
