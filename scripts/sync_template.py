# Copy template/brief.html into every site/<slug>/ that has a data.js, as site/<slug>/index.html.
# Usage: python3 scripts/sync_template.py
import pathlib, shutil

root = pathlib.Path(__file__).resolve().parent.parent
tpl = root / 'template' / 'brief.html'
for d in sorted((root / 'site').iterdir()):
    if d.is_dir() and (d / 'data.js').exists():
        shutil.copyfile(tpl, d / 'index.html')
        print(f'synced {d.relative_to(root)}/index.html')
