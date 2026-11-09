#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path

IN_FILE = sys.argv[1]
GIT_REPO = Path().cwd() / '.git'
OUTPUT = sys.argv[2]

# distutils (and its copy_tree) has been removed from Python 3.12
shutil.copytree(Path(IN_FILE).parent.absolute(), Path(OUTPUT).parent.absolute(), dirs_exist_ok=True)
MANIFEST = json.load(open(IN_FILE, encoding='utf-8'))
MODULE = MANIFEST['modules'][-1]['sources'][0]
MODULE['url'] = str(GIT_REPO)
MODULE['commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
MODULE.pop('branch', None)
MODULE.pop('tag', None)
json.dump(MANIFEST, open(OUTPUT, 'w', encoding='utf-8'))
