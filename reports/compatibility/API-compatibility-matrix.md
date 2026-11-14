# Lara v0.2 / DSGames 2.5 — API compatibility matrix

**Evidence basis:** generated symbol reports and previously recorded bundle/build metadata. This is a static review, not a runtime capability assessment.

## Matrix

| Surface | Lara evidence | DSGames evidence | Classification | Decision |
|---|---|---|---|---|
| `libgrabkernel2` architecture | arm64 + arm64e | arm64 + arm64e | Architecture match | Continue static ABI review |
| `_grab_kernelcache` | Exported | Exported | Direct name match | Not approved for drop-in reuse until prototype/ABI and behavior are verified |
| Other `libgrabkernel2` exports | 23 additional exports | Not in DSGames global-export list | Not exported by target build | Do not link against these names in a DSGames-targeted adapter |
| `libxpf` architecture | arm64 + arm64e | arm64 + arm64e | Architecture match | Continue static ABI review |
| `_gXPF` | Exported | Exported | Direct name match | Global data layout and ownership unknown |
| `_xpf_construct_offset_dictionary` | Exported | Exported | Direct name match | Prototype and output contract unknown |
| `_xpf_item_resolve` | Exported | Exported | Direct name match | Prototype and resolution semantics unknown |
| `_xpf_start_with_kernel_path` | Exported | Exported | Direct name match | Initialization contract and side effects unknown |
| `_xpf_stop` | Exported | Exported | Direct name match | Lifecycle/thread-safety contract unknown |
| Other `libxpf` exports | 303 additional exports | Not in DSGames global-export list | Not exported by target build | No direct dynamic-link dependency on these names |
| Main-executable dependencies and run paths | 44 linked dylib entries; 2 declared run paths | 46 linked dylib entries; same 2 declared run paths | 37 exact dependency-name matches; host loader declarations broadly align | Review the 7 Lara-only and 9 DSGames-only dependency names before any change; see main-executable-comparison.md |
| Entitlement/profile metadata | Lara had no embedded profile in supplied IPA | DSGames profile had additional declared entitlements; grant/runtime availability unverified | Authorization context differs | No entitlement-based compatibility assumption |
| Minimum iOS metadata | Lara 16.0 | DSGames 16.1 | Platform baseline mismatch | Lara's deployment target must be tested on each supported OS; do not assume target parity |
| Objective-C metadata | Class/category/selector-reference sections present in libgrabkernel2; Partial class symbol exported | Same section families present; no exported class symbol detected | Metadata presence matches; selector/method compatibility unknown | Extract actual selector strings, method implementations, and class-layout evidence before reuse |
| Function prototypes/struct layouts | Not established from export names alone | Not established from export names alone | Unknown | Requires reliable headers, debug info, or unambiguous call-site evidence |

## Important interpretation

An exported symbol name only establishes that a linker-visible name exists in the inspected slice. It does not prove that the two builds use the same function signature, register/stack ABI, structure layout, ownership model, error conventions, synchronization requirements, or semantic behavior.

A symbol absent from the global export list may still exist as a local/hidden implementation detail. Do not treat absence from this list as proof that the implementation is absent.

## Classification rules

- **Direct name match:** same exported symbol spelling exists in both reports. This is a candidate for ABI review, not a green light to call.
- **Wrapper candidate:** only assign after a documented interface mismatch is understood and a safe, supported wrapper can be designed. No wrapper is approved yet.
- **Not exported:** symbol is not in the target build's global export list. Do not bind to it dynamically.
- **Unknown:** insufficient evidence for a compatibility decision.

## Dependency metadata update\n\nThe completed inventory reports matching install names and listed system dependencies for the two paired dylibs. Both libgrabkernel2 builds declare iOS 14.0 and both libxpf builds declare iOS 15.0 at the dylib load-command level. No LC_RPATH was found in these dylibs; host-executable run-path entries have not yet been inventoried. These findings are summarized in [dependency-and-metadata-findings.md](dependency-and-metadata-findings.md).\n\n## Main-executable inventory update\n\nThe host executable inventory is complete. Lara declares iOS 16.0 and DSGames 16.1; both declare the same two run-path entries. The exact dependency-name and method-name-string counts are documented in [main-executable-comparison.md](main-executable-comparison.md). The selector candidates are not proof of implemented or ABI-compatible methods.\n\n## Current disposition

No binary transplant or direct function-call integration is approved by this matrix. Preserve Lara's current implementation as the baseline and use the metadata inventory plus controlled tests on an owned app/test harness to close the remaining unknowns.
