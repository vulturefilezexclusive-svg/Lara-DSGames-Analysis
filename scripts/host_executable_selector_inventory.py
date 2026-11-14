#!/usr/bin/env python3
"""Static inventory of app main executables and Objective-C selector-name sections."""
import hashlib, json, plistlib, struct, subprocess, zipfile
from pathlib import Path

APPS = [
    ("Lara-v0.2", Path("work/lara")),
    ("DSGames-2.5", Path("work/dsgames")),
]
OUT = Path("reports/metadata")
OUT.mkdir(parents=True, exist_ok=True)

LC_LOADS = {0xc:"load",0x80000018:"weak",0x8000001f:"reexport",0x80000023:"upward"}
LC_RPATH=0x8000001c
LC_ID_DYLIB=0xd
LC_BUILD_VERSION=0x32
LC_VERSION_MIN_IPHONEOS=0x24
LC_SEGMENT_64=0x19

def ver(v): return f"{(v>>16)&65535}.{(v>>8)&255}.{v&255}"

def slices(data):
    magic=data[:4]
    if magic in (b'\xca\xfe\xba\xbe',b'\xbe\xba\xfe\xca',b'\xca\xfe\xba\xbf',b'\xbf\xba\xfe\xca'):
        be=magic in (b'\xca\xfe\xba\xbe',b'\xca\xfe\xba\xbf')
        endian='>' if be else '<'; is64=magic in (b'\xca\xfe\xba\xbf',b'\xbf\xba\xfe\xca')
        n=struct.unpack_from(endian+'I',data,4)[0]; pos=8; out=[]
        for _ in range(n):
            if is64:
                cpu,sub,off,size,align,res=struct.unpack_from(endian+'iiQQII',data,pos); pos+=32
            else:
                cpu,sub,off,size,align=struct.unpack_from(endian+'iiIII',data,pos); pos+=20
            name={0x0100000c:'arm64',0x0200000c:'arm64_32',0x01000007:'x86_64'}.get(cpu&0xffffffff,hex(cpu&0xffffffff))
            if name=='arm64' and (sub&0xffffff)==2: name='arm64e'
            out.append((name,data[off:off+size]))
        return out
    return [('thin',data)]

def parse_slice(name,b):
    if len(b)<32 or b[:4] not in (b'\xcf\xfa\xed\xfe',b'\xfe\xed\xfa\xcf'):
        return {"architecture":name,"error":"unsupported or invalid 64-bit Mach-O slice"}
    e='<' if b[:4]==b'\xcf\xfa\xed\xfe' else '>'
    h=struct.unpack_from(e+'IiiIIIII',b,0); ncmds=h[4]; pos=32
    loads=[]; rpaths=[]; minos=None; sdk=None; objc_strings=[]
    for _ in range(ncmds):
        if pos+8>len(b): break
        cmd,sz=struct.unpack_from(e+'II',b,pos)
        if sz<8 or pos+sz>len(b): break
        if cmd in LC_LOADS or cmd==LC_ID_DYLIB:
            no=struct.unpack_from(e+'I',b,pos+8)[0]
            value=b[pos+no:pos+sz].split(b'\0',1)[0].decode('utf-8','replace')
            loads.append({"kind":"id" if cmd==LC_ID_DYLIB else LC_LOADS[cmd],"name":value})
        elif cmd==LC_RPATH:
            no=struct.unpack_from(e+'I',b,pos+8)[0]
            rpaths.append(b[pos+no:pos+sz].split(b'\0',1)[0].decode('utf-8','replace'))
        elif cmd==LC_BUILD_VERSION:
            _,mv,sv,_=struct.unpack_from(e+'IIII',b,pos+8); minos=ver(mv); sdk=ver(sv)
        elif cmd==LC_VERSION_MIN_IPHONEOS:
            mv,sv=struct.unpack_from(e+'II',b,pos+8); minos=ver(mv); sdk=ver(sv)
        elif cmd==LC_SEGMENT_64:
            nsects=struct.unpack_from(e+'I',b,pos+64)[0]
            sp=pos+72
            for _s in range(nsects):
                sect=b[sp:sp+16].split(b'\0',1)[0].decode('ascii','replace')
                seg=b[sp+16:sp+32].split(b'\0',1)[0].decode('ascii','replace')
                size,offset=struct.unpack_from(e+'QQI',b,sp+32)[0],struct.unpack_from(e+'I',b,sp+48)[0]
                if sect=="__objc_methname" and offset+size<=len(b):
                    raw=b[offset:offset+size]
                    for item in raw.split(b'\0'):
                        if 1<=len(item)<=256 and all(c>=32 and c<127 for c in item):
                            objc_strings.append(item.decode('ascii'))
                sp+=80
        pos+=sz
    return {"architecture":name,"load_commands":loads,"rpaths":rpaths,
            "minimum_os":minos,"sdk":sdk,
            "objc_methname_count":len(set(objc_strings)),
            "objc_methname_candidates":sorted(set(objc_strings))}

result=[]
for app,root in APPS:
    plist_paths=list(root.glob("Payload/*.app/Info.plist"))
    if len(plist_paths)!=1:
        result.append({"app":app,"error":f"expected one app Info.plist, found {len(plist_paths)}"}); continue
    plist_path=plist_paths[0]
    with plist_path.open("rb") as f: info=plistlib.load(f)
    executable=info.get("CFBundleExecutable")
    binary=plist_path.parent/executable if executable else None
    if not binary or not binary.is_file():
        result.append({"app":app,"bundle_id":info.get("CFBundleIdentifier"),
                       "error":"CFBundleExecutable missing or executable file absent"}); continue
    data=binary.read_bytes()
    result.append({"app":app,"bundle_id":info.get("CFBundleIdentifier"),
        "version":info.get("CFBundleShortVersionString"),
        "build":info.get("CFBundleVersion"),"executable":executable,
        "path":str(binary),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),
        "slices":[parse_slice(a,b) for a,b in slices(data)]})

(OUT/"host-executable-selector-inventory.json").write_text(json.dumps(result,indent=2)+"\n")
lines=["# Main executable and Objective-C selector-name inventory","",
"Static analysis only. Selector-name strings do not prove that a method is implemented, callable, or safe to reuse.",""]
for x in result:
    lines += [f"## {x['app']}",""]
    if "error" in x: lines += [f"ERROR: {x['error']}",""]; continue
    lines += [f"- Bundle ID: {x['bundle_id']}",f"- Version/build: {x.get('version')} / {x.get('build')}",
              f"- Executable: {x['executable']}",f"- Size: {x['bytes']} bytes",f"- SHA-256: {x['sha256']}",""]
    for s in x["slices"]:
        lines += [f"### {s['architecture']}",""]
        if "error" in s: lines += [s["error"],""]; continue
        lines += [f"- Minimum OS: {s['minimum_os'] or 'unknown'}; SDK: {s['sdk'] or 'unknown'}",
                  "- Rpaths: "+(", ".join(s["rpaths"]) or "(none declared)",
                  "- Linked dylibs:"] 
        lines += [f"  - {d['kind']}: {d['name']}" for d in s["load_commands"]] or ["  - (none found)"]
        lines += [f"- Objective-C method-name strings found: {s['objc_methname_count']}","",
                  "<details><summary>Selector-name candidates</summary>",""]
        lines += [f"- `{v}`" for v in s["objc_methname_candidates"]]
        lines += ["","</details>",""]
(OUT/"host-executable-selector-inventory.md").write_text("\n".join(lines)+"\n")
