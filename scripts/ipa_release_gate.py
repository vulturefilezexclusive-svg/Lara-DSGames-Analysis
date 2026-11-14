#!/usr/bin/env python3
"""Non-invasive IPA archive and release-metadata gate. No app code is executed."""
import hashlib, json, plistlib, shutil, subprocess, tempfile, zipfile
from pathlib import Path, PurePosixPath
TARGETS=[("Lara-v0.2",Path("lara_v0.2.ipa")),("DSGames-2.5",Path("DSGames_2.5.ipa"))]
OUT=Path("reports/validation"); OUT.mkdir(parents=True,exist_ok=True)
def inspect(label,ipa):
 r={"app":label,"ipa":str(ipa),"checks":[],"status":"FAIL"}
 def ck(n,ok,d): r["checks"].append({"name":n,"pass":bool(ok),"detail":str(d)})
 if not ipa.is_file() or ipa.stat().st_size==0:
  ck("IPA exists and is non-empty",False,"File missing or empty"); return r
 raw=ipa.read_bytes(); r["ipa_bytes"]=len(raw); r["ipa_sha256"]=hashlib.sha256(raw).hexdigest()
 try: z=zipfile.ZipFile(ipa)
 except Exception as e: ck("ZIP container opens",False,repr(e)); return r
 with z:
  bad=z.testzip(); ck("ZIP CRC integrity",bad is None,"All entries pass CRC" if bad is None else "Corrupt member: "+bad)
  names=z.namelist()
  unsafe=[n for n in names if PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts]
  ck("Archive paths are confined",not unsafe,str(len(unsafe))+" unsafe path(s)")
  plist_names=[n for n in names if n.startswith("Payload/") and n.endswith(".app/Info.plist")]
  ck("Exactly one app Info.plist",len(plist_names)==1,"Found "+str(len(plist_names)))
  if len(plist_names)!=1 or unsafe or bad is not None: return r
  plist_name=plist_names[0]; prefix=plist_name[:-len("Info.plist")]
  try: info=plistlib.loads(z.read(plist_name))
  except Exception as e: ck("Info.plist parses",False,repr(e)); return r
  exe=info.get("CFBundleExecutable"); bundle=info.get("CFBundleIdentifier")
  exe_name=prefix+str(exe or ""); exists=bool(exe) and exe_name in names
  ck("CFBundleExecutable exists in app bundle",exists,exe_name if exists else "Executable key/file missing")
  ck("Bundle identifier present",bool(bundle),bundle or "Missing")
  ck("Version/build metadata present",bool(info.get("CFBundleShortVersionString")) and bool(info.get("CFBundleVersion")),str(info.get("CFBundleShortVersionString"))+" / "+str(info.get("CFBundleVersion")))
  manifest=prefix+"_CodeSignature/CodeResources"
  ck("CodeResources manifest present",manifest in names,"Manifest found" if manifest in names else "No CodeResources manifest")
  profiles=[n for n in names if n==prefix+"embedded.mobileprovision"]
  ck("Provisioning profile status recorded",True,"Present (contents not decoded)" if profiles else "Absent; may be expected for unsigned/ad-hoc input")
  archs=None; detail="Executable unavailable"
  if exists:
   with tempfile.TemporaryDirectory() as td:
    p=Path(td)/"app-executable"; p.write_bytes(z.read(exe_name))
    tool=shutil.which("llvm-lipo") or shutil.which("lipo")
    if tool:
     q=subprocess.run([tool,"-archs",str(p)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
     archs=q.stdout.strip() if q.returncode==0 else None; detail=q.stdout.strip()
    else: detail="llvm-lipo/lipo unavailable"
  arm=bool(archs and any(a in archs.split() for a in ("arm64","arm64e")))
  ck("Device ARM64 architecture present",arm,archs or detail)
  r.update(bundle_id=bundle,version=info.get("CFBundleShortVersionString"),build=info.get("CFBundleVersion"),minimum_os=info.get("MinimumOSVersion"),architectures=archs)
  r["status"]="PASS" if all(c["pass"] for c in r["checks"]) else "FAIL"
 return r
results=[inspect(n,p) for n,p in TARGETS]
(OUT/"ipa-release-gate.json").write_text(json.dumps(results,indent=2)+"\n")
lines=["# IPA archive and release-metadata gate","","Static checks only. This does not execute either app or cryptographically verify Apple's signature on a device.",""]
for x in results:
 lines += ["## "+x["app"]+" — "+x["status"],""]
 for c in x["checks"]: lines += ["- ["+("x" if c["pass"] else " ")+"] **"+c["name"]+"** — "+c["detail"]]
 if "ipa_sha256" in x:
  for k,label in [("ipa_bytes","IPA size"),("ipa_sha256","IPA SHA-256"),("bundle_id","Bundle ID"),("version","Version"),("build","Build"),("minimum_os","Minimum iOS"),("architectures","Architectures")]:
   lines += ["- "+label+": "+str(x.get(k,"unknown"))]
 lines += [""]
lines += ["## Interpretation","","A CodeResources file or embedded profile is metadata evidence, not proof iOS will accept the signature.","Device installation still requires a valid signing chain, provisioning, entitlement authorization, and runtime validation.","The gate checks archive structure and declared metadata; it does not certify app behavior."]
(OUT/"ipa-release-gate.md").write_text("\n".join(lines)+"\n")
if any(x["status"]!="PASS" for x in results): raise SystemExit("IPA release gate failed; inspect reports/validation/ipa-release-gate.md")
