# Lara v0.2 vs DSGames 2.5 — static symbol comparison

**Scope:** static Mach-O export comparison for the four bundled dylibs. This report does not establish runtime behavior, entitlement availability, or cross-process access.

## Inputs and architecture

| Component | Lara v0.2 | DSGames 2.5 |
|---|---:|---:|
| `libgrabkernel2.dylib` size | 210,112 bytes | 278,528 bytes |
| `libgrabkernel2.dylib` SHA-256 | `fb27032f7a9401b52ba94821de301aa2a57e3f61fc67bf464db3ce4075b52a4e` | `a272e919c9ff3ae909aca7d10f83afbf74ff34a44663520d21bd27558b5c91de` |
| `libxpf.dylib` size | 472,112 bytes | 507,904 bytes |
| `libxpf.dylib` SHA-256 | `e87d0469bc542e1403531cf7d4f027335d514882c78b5a80cb750c5e6f310a30` | `f2dc42d209e2b52bc837469ce34c637076a23ae4f2823057c78e58e91025db78` |
| Architecture slices | arm64, arm64e | arm64, arm64e |

The architecture slices match for both library pairs. The binary hashes and file sizes differ, so these are not identical builds.

## Export comparison

Counts below are defined global external symbols from the generated arm64 reports.

| Library | Lara exports | DSGames exports | Exact-name overlap |
|---|---:|---:|---:|
| `libgrabkernel2.dylib` | 24 | 1 | 1 |
| `libxpf.dylib` | 308 | 5 | 5 |

### Shared exported names

**libgrabkernel2**
- `_grab_kernelcache`

**libxpf**
- `_gXPF`
- `_xpf_construct_offset_dictionary`
- `_xpf_item_resolve`
- `_xpf_start_with_kernel_path`
- `_xpf_stop`

### Lara-only exported names

Lara exposes substantially more global symbols in these reports:
- `libgrabkernel2.dylib`: 23 Lara-only exports
- `libxpf.dylib`: 303 Lara-only exports

This is an export-surface difference, not proof that DSGames lacks the corresponding internal routines. They may be local, hidden, stripped, or reached through other interfaces.

## Compatibility assessment

| Interface | Static finding | Status |
|---|---|---|
| `_grab_kernelcache` | Same exported name in both builds | **Name match only** |
| Five shared `libxpf` exports | Same exported names in both builds | **Name match only** |
| Remaining Lara exports | Not present in DSGames global-export list | **No direct exported match** |
| ARM64 / ARM64e slices | Both architectures present in both builds | **Architecture-level match** |
| Binary identity | Hashes and sizes differ | **Not identical** |
| ABI / calling convention / structure layout | Not established by symbol names | **Unknown** |
| Runtime behavior | Not measured by this workflow | **Unknown** |

**No direct-reuse decision is approved yet.** A matching symbol name does not establish matching function prototypes, ownership rules, structure layouts, error behavior, or OS-version assumptions. Treat all five shared `libxpf` names and the one shared `libgrabkernel2` name as candidates for deeper, non-invasive ABI review—not as drop-in compatible APIs.

## Next milestone: dependency and ABI evidence

1. Extract each dylib's install name, load commands, linked dependencies, rpaths, minimum OS metadata, and exported-symbol trie.
2. Compare Objective-C class/selector metadata and public API declarations where present.
3. Record function prototypes and data-layout evidence only where symbols can be mapped reliably to headers, debug metadata, or unambiguous call sites.
4. Produce a compatibility matrix with **direct match**, **wrapper candidate**, **not exported**, or **unknown** classifications.
5. Keep the baseline IPAs immutable; all reports remain additive under `reports/`.

The next milestone is limited to static compatibility and controlled testing of the user's own app or a purpose-built test target. It does not include instructions for injecting into, reading from, or modifying unrelated third-party processes.
