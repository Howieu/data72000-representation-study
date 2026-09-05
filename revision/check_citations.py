"""Check live citation keys and bibliography coverage without rewriting sources."""
import re,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];tex=ROOT/'dissertation/overleaf'
seen=set();files=[]
def visit(p):
 if p in seen:return
 seen.add(p);files.append(p)
 for name in re.findall(r'\\input\{([^}]+)\}',p.read_text()):visit(tex/(name if name.endswith('.tex') else name+'.tex'))
visit(tex/'main.tex')
used=set()
for p in files:
 for keys in re.findall(r'\\cite\w*\*?(?:\[[^]]*\])*\{([^}]+)\}',p.read_text()):used.update(keys.split(','))
bib=set(re.findall(r'@\w+\{([^,]+),',(tex/'references.bib').read_text()))
rendered=set(re.findall(r'\\bibitem(?:\[[^]]*\])?\{([^}]+)\}',(tex/'references_harvard.tex').read_text()))
assert used<=bib and used<=rendered,(used-bib,used-rendered)
assert not re.search(r'\b(?:TODO|FIXME|TBD|PLACEHOLDER)\b','\n'.join(p.read_text() for p in files),re.I)
(ROOT/'revision/citation_key_check.json').write_text(json.dumps({'active_tex_files':len(files),'used_keys':sorted(used),'missing_bib_keys':sorted(used-bib),'missing_rendered_keys':sorted(used-rendered),'unused_rendered_keys':sorted(rendered-used),'placeholder_check':'pass'},indent=2)+'\n')
print(len(used),'citation keys present in both bibliographies; no placeholder markers.')
