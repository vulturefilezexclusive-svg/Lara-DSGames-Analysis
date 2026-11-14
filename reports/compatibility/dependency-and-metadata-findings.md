# Lara v0.2 / DSGames 2.5 — dependency and metadata findings

**Workflow evidence:** GitHub Actions run 43549800723 completed successfully on the main branch. The generated source inventory is `reports/metadata/macho-dependency-objc-inventory.md`.

## Confirmed static findings

| Component | Lara v0.2 | DSGames 2.5 | Assessment |
|---|---|---|---|
| `libgrabkernel2.dylib` slices | arm64, arm64e | arm64, arm64e | Architecture match |
| `libxpf.dylib` slices | arm64, arm64e | arm64, arm64e | Architecture match |
| `libgrabkernel2` install name | `@rpath/libgrabkernel2.dylib` | Same | Name match |
| `libxpf` install name | `@executable_path/Frameworks/libxpf.dylib` | Same | Name match |
| `libgrabkernel2` minimum OS | 14.0 | 14.0 | Dylib load-command match |
| `libxpf` minimum OS | 15.0 | 15.0 | Dylib load-command match |
| `libgrabkernel2` Objective-C sections | class/category/selector reference sections present | Same section families present | Metadata exists in both |
| Exported Objective-C class symbols in `libgrabkernel2` | `Partial` class/metaclass | None detected | Export visibility differs |
| `libxpf` Objective-C sections/classes | None detected | None detected | No Obj-C metadata detected by this inventory |

The two libraries have matching listed system dependencies: Foundation, Security, zlib, UIKit, Objective-C runtime, libSystem and CoreFoundation for `libgrabkernel2`; Foundation, libcompression, libSystem and CoreFoundation for `libxpf`.

## Important interpretation and limitations

1. These are **dylib-level** load-command findings. They do not replace a full inventory of each app's main executable, embedded frameworks, plug-ins, or runtime-loaded libraries.
2. Neither dylib declares an LC_RPATH in this inventory. That alone is not a load failure: dyld resolution of an `@rpath` install name also depends on the loading image's run-path search paths. The host executable's LC_RPATH entries still need to be inspected.
3. The report detects Objective-C metadata section families; it does **not** enumerate or compare the actual selector strings, method implementations, class layouts, or category contents. The selector compatibility result therefore remains unknown.
4. Minimum OS values above are from the dylibs' Mach-O load commands. They are not the host apps' deployment targets. Previously recorded app-level targets remain Lara 16.0 and DSGames 16.1.
5. Matching install names, dependencies, architectures, or exported symbol spellings do not establish matching function prototypes, data layouts, ownership, error behavior, or runtime semantics.

## Compatibility disposition

- **Architecture:** compatible at the slice-presence level only.
- **Install names/dependency declarations:** structurally aligned for these two libraries.
- **Objective-C selector/API compatibility:** unknown; actual selector and method-level extraction is still required.
- **Binary substitution or direct API calls:** not approved by this evidence.
- **Next safe analysis step:** inventory each main executable's load commands and run-paths, then compare actual selector references and call-site ABI evidence. Runtime validation should stay within Lara or a controlled app/test target owned by the project; this report does not establish or authorize access to unrelated processes.
