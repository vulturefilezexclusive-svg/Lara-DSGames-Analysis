#!/usr/bin/env python3
"""Static Mach-O metadata inventory for the two checked-in IPA files."""
import hashlib, json, struct, subprocess
from pathlib import Path

TARGETS = [
    ("Lara-v0.2", Path("work/lara"), "libgrabkernel2.dylib"),
    ("Lara-v0.2", Path("work/lara"), "libxpf.dylib"),
    ("DSGames-2.5", Path("work/dsgames"), "libgrabkernel2.dylib"),
    ("DSGames-2.5", Path("work/dsgames"), "libxpf.dylib"),
]
OUT = Path("reports/metadata")
OUT.mkdir(parents=True, exist_ok=True)

LC_ID_DYLIB=0xd
LC_LOAD_DYLIB=0xc
LC_LOAD_WEAK_DYLIB=0x80000018
LC_REEXPORT_DYLIB=0x8000001f
LC_LOAD_UPWARD_DYLIB=0x80000023
LC_RPATH=0x8000001c
LC_BUILD_VERSION=0x32
LC_VERSION_MIN_IPHONEOS=0x24
LC_DYLD_INFO=0x22
LC_DYLD_INFO_ONLY=0x80000022
LC_DYLD_EXPORTS_TRIE=0x80000033
DYLIB_CMDS={LC_ID_DYLIB,LC_LOAD_DYLIB,LC_LOAD_WEAK_DYLIB,LC_REEXPORT_DYLIB,LC_LOAD_UPWARD_DYLIB}

def version(v):
    return f"{(v>>16)&0xffff}.{(v>>8)&0xff}.{v&0xff}"

def thin_slices(data):
    if len(data)<4: return []
    magic=data[:4]
    if magic in (b'\xca\xfe\xba\xbe',b'\xbe\xba\xfe\xca',b'\xca\xfe\xba\xbf',b'\xbf\xba\xfe\xca'):
        endian='>' if magic in (b'\xca\xfe\xba\xbe',b'\xca\xfe\xba\xbf') else '<'
        is64=magic in (b'\xca\xfe\xba\xbf',b'\xbf\xba\xfe\xca')
        n=struct.unpack_from(endian+'I',data,4)[0]
        pos=8; out=[]
        for _ in range(n):
            if is64:
                cputype,subtype,off,size,align,res=struct.unpack_from(endian+'iiQQII',data,pos); pos+=32
            else:
                cputype,subtype,off,size,align=struct.unpack_from(endian+'iiIII',data,pos); pos+=20
            cpu=cputype & 0xffffffff
            arch={0x0100000c:'arm64',0x0200000c:'arm64_32',0x01000007:'x86_64',12:'arm'}.get(cpu,hex(cpu))
            if arch=='arm64' and (subtype & 0xffffff)==2: arch='arm64e'
            out.append((arch,data[off:off+size]))
        return out
    return [('thin',data)]

def parse_thin(label, blob):
    if len(blob)<32: return {"slice":label,"error":"slice too small"}
    magic=blob[:4]
    if magic==b'\xcf\xfa\xed\xfe': endian='<'
    elif magic==b'\xfe\xed\xfa\xcf': endian='>'
    else: return {"slice":label,"error":f"unsupported Mach-O magic {magic.hex()}"}
    hdr=struct.unpack_from(endian+'IiiIIIII',blob,0)
    cputype,subtype,ncmds=hdr[1],hdr[2],hdr[4]
    pos=32; deps=[]; rpaths=[]; ident=None; minos=None; sdk=None; exports_trie=False; dyld_info=False
    for _ in range(ncmds):
        if pos+8>len(blob): break
        cmd,cmdsize=struct.unpack_from(endian+'II',blob,pos)
        if cmdsize<8 or pos+cmdsize>len(blob): break
        if cmd in DYLIB_CMDS:
            nameoff=struct.unpack_from(endian+'I',blob,pos+8)[0]
            raw=blob[pos+nameoff:pos+cmdsize].split(b'\0',1)[0].decode('utf-8','replace')
            if cmd==LC_ID_DYLIB: ident=raw
            else:
                kind={LC_LOAD_DYLIB:"load",LC_LOAD_WEAK_DYLIB:"weak",LC_REEXPORT_DYLIB:"reexport",LC_LOAD_UPWARD_DYLIB:"upward"}[cmd]
                deps.append({"kind":kind,"name":raw})
        elif cmd==LC_RPATH:
            off=struct.unpack_from(endian+'I',blob,pos+8)[0]
            rpaths.append(blob[pos+off:pos+cmdsize].split(b'\0',1)[0].decode('utf-8','replace'))
        elif cmd==LC_BUILD_VERSION:
            platform,minv,sd,ntools=struct.unpack_from(endian+'IIII',blob,pos+8)
            minos=version(minv); sdk=version(sd)
        elif cmd==LC_VERSION_MIN_IPHONEOS:
            minv,sd=struct.unpack_from(endian+'II',blob,pos+8)
            minos=version(minv); sdk=version(sd)
        elif cmd in (LC_DYLD_INFO,LC_DYLD_INFO_ONLY):
            dyld_info=True
            export_off,export_size=struct.unpack_from(endian+'II',blob,pos+40)
            exports_trie=exports_trie or bool(export_off and export_size)
        elif cmd==LC_DYLD_EXPORTS_TRIE:
            off,size=struct.unpack_from(endian+'II',blob,pos+8)
            exports_trie=exports_trie or bool(off and size)
        pos+=cmdsize
    cpu=cputype & 0xffffffff
    arch={0x0100000c:'arm64',0x0200000c:'arm64_32',0x01000007:'x86_64',12:'arm'}.get(cpu,hex(cpu))
    if arch=='arm64' and (subtype & 0xffffff)==2: arch='arm64e'
    return {"slice":label if label!='thin' else arch,"header_arch":arch,"install_name":ident,
            "dependencies":deps,"rpaths":rpaths,"minimum_os":minos,"sdk":sdk,
            "dyld_info_command":dyld_info,"has_export_trie_command_or_range":exports_trie}

def run(args):
    p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    return p.returncode,p.stdout

def objc_inventory(binary):
    rc,out=run(["llvm-objdump","--macho","--section-headers",str(binary)])
    wanted=("__objc_classlist","__objc_nlclslist","__objc_catlist","__objc_nlcatlist",
            "__objc_selrefs","__objc_classrefs","__objc_const","__objc_protolist",
            "__objc_superrefs","__swift5_types","__swift5_proto")
    found=sorted({name for name in wanted if name in out})
    rc2,syms=run(["llvm-nm","--extern-only","--defined-only",str(binary)])
    objc_symbols=sorted({line.split()[-1] for line in syms.splitlines()
                         if "_OBJC_CLASS_$_" in line or "_OBJC_METACLASS_$_" in line})
    return {"section_command_exit":rc,"metadata_sections_found":found,
            "symbol_command_exit":rc2,"exported_objc_class_symbols":objc_symbols}

inventory=[]
for app,root,name in TARGETS:
    matches=list(root.rglob(name))
    if len(matches)!=1:
        inventory.append({"app":app,"file":name,"error":f"expected one file, found {len(matches)}"})
        continue
    path=matches[0]; data=path.read_bytes()
    item={"app":app,"file":name,"path":str(path),"bytes":len(data),
          "sha256":hashlib.sha256(data).hexdigest(),"slices":[]}
    for arch,blob in thin_slices(data):
        item["slices"].append(parse_thin(arch,blob))
    item["objc_metadata"]=objc_inventory(path)
    inventory.append(item)

(OUT/"macho-dependency-objc-inventory.json").write_text(json.dumps(inventory,indent=2)+"\n")
lines=["# Mach-O dependency and Objective-C metadata inventory","",
       "Static metadata only. Dependency declarations and section names do not prove runtime loading or capability.",""]
for item in inventory:
    lines += [f"## {item['app']} — {item['file']}", ""]
    if "error" in item:
        lines += [f"ERROR: {item['error']}",""]; continue
    lines += [f"- Size: {item['bytes']} bytes",f"- SHA-256: {item['sha256']}",""]
    for s in item["slices"]:
        lines += [f"### Slice: {s.get('slice')}",f"- Header architecture: {s.get('header_arch','unknown')}",
                  f"- Install name: {s.get('install_name') or '(not declared)'}",
                  f"- Minimum OS: {s.get('minimum_os') or '(not declared)'}, SDK: {s.get('sdk') or '(not declared)'}",
                  f"- Export trie command/range present: {s.get('has_export_trie_command_or_range',False)}",
                  "- Rpaths: "+(", ".join(s.get("rpaths",[])) or "(none declared)"),
                  "- Dependencies:"]
        lines += [f"  - {d['kind']}: {d['name']}" for d in s.get("dependencies",[])] or ["  - (none declared)"]
        lines += [""]
    objc=item["objc_metadata"]
    lines += ["### Objective-C / Swift metadata evidence",
              "- Relevant sections: "+(", ".join(objc["metadata_sections_found"]) or "(none detected)"),
              "- Exported Objective-C class symbols: "+(", ".join(objc["exported_objc_class_symbols"]) or "(none detected)"),""]
(OUT/"macho-dependency-objc-inventory.md").write_text("\n".join(lines)+"\n")
