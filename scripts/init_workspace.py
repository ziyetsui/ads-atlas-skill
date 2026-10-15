# Create (or upgrade) a brief workspace = the repo that GitHub Pages publishes.
#   python3 <skill>/scripts/init_workspace.py <dir>
# New dir: copies the skeleton (template, site assets, home page, Pages workflow, .gitignore) + all scripts.
# Existing workspace: refreshes scripts/, guide/, template/ and site/assets/ only; briefs/, site/<slug>/ and data/ are left alone.
# (An existing workspace = it has site/briefs.js.)
import os, shutil, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dst = os.path.abspath(os.path.expanduser(sys.argv[1]))
fresh = not os.path.exists(os.path.join(dst, 'site', 'briefs.js'))
os.makedirs(dst, exist_ok=True)

if fresh:
    shutil.copytree(os.path.join(SKILL, 'workspace'), dst, dirs_exist_ok=True)
    os.makedirs(os.path.join(dst, 'briefs'), exist_ok=True)
else:
    for sub in ('template', os.path.join('site', 'assets'), os.path.join('.github', 'workflows')):
        shutil.copytree(os.path.join(SKILL, 'workspace', sub), os.path.join(dst, sub), dirs_exist_ok=True)
shutil.copytree(os.path.join(SKILL, 'scripts'), os.path.join(dst, 'scripts'), dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('init_workspace.py', '__pycache__'))
for sub in ('agents', 'references'):  # the analyst / QA guides travel with the workspace, so a subagent there can read them
    shutil.copytree(os.path.join(SKILL, sub), os.path.join(dst, 'guide', sub), dirs_exist_ok=True)
print(('created' if fresh else 'upgraded') + f' workspace {dst}')
