import re,glob,os
files=[f.replace(os.sep,'/') for f in glob.glob('**/*.md',recursive=True)]
base={os.path.splitext(os.path.basename(f))[0]:f for f in files}
paths={os.path.splitext(f)[0]:f for f in files}
link_re=re.compile(r'\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]')
strip=lambda t: re.sub(r'`[^`]*`','',t)
broken=[]; total=0
for f in files:
    t=strip(open(f,encoding='utf-8').read())
    for tgt in (m.strip() for m in link_re.findall(t)):
        total+=1
        if tgt not in base and tgt not in paths: broken.append((f,tgt))
print(f"Notas: {len(files)} | Wikilinks: {total} | rotos: {len(broken)}")
for f,t in broken: print(f"  ROTO  {f} -> [[{t}]]")
# frontmatter minimo
bad=[f for f in files if not open(f,encoding='utf-8').read().startswith('---') and '/docs/' not in f and 'MOC' not in f and f not in ('Home.md','MEMORY.md')]
print("Sin frontmatter (notas de memoria):", bad or "ninguna")
