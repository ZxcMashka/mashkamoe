#!/usr/bin/env python3
"""Build a WoT Python 2.7 wotmod; PYTHON2 may select the compiler."""
import hashlib, os, re, subprocess, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
VERSION='1.0.3'
package=ROOT/'package'
compiler=os.environ.get('PYTHON2','/workspace/python2/bin/python2.7')
source=ROOT/'src/mod_mashkamarks.py'
bytecode=package/'res/scripts/client/gui/mods/mod_mashkamarks.pyc'
subprocess.run([compiler,'-c','import py_compile,sys; py_compile.compile(sys.argv[1],sys.argv[2],"mod_mashkamarks.py",True)',str(source),str(bytecode)],check=True)
assert bytecode.read_bytes()[:4]==b'\x03\xf3\r\n'
meta=package/'meta.xml';text=meta.read_text();text=re.sub(r'<version>[^<]+</version>', '<version>'+VERSION+'</version>',text);meta.write_text(text)
assert '<version>'+VERSION+'</version>' in text
out=ROOT.parent/'output';out.mkdir(exist_ok=True)
target=out/('mashkamarks_'+VERSION+'.wotmod')
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_STORED) as z:
    for file in sorted(package.rglob('*')):
        if file.is_file():z.write(file,file.relative_to(package))
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    assert 'res/scripts/client/gui/mods/mod_mashkamarks.pyc' in z.namelist()
    assert ('<version>'+VERSION+'</version>').encode() in z.read('meta.xml')
print(str(target))
print('SHA256 '+hashlib.sha256(target.read_bytes()).hexdigest())
