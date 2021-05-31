# md_toc.py - Markdown table of contents

import sys

# Command line argument
if len(sys.argv) != 2:
    print(f'Usage: {sys.argv[0]} <filepath>')
    exit(-1)
filepath = sys.argv[1]

top = []
with open(filepath) as f:
    for line in f:
        line = line.rstrip()
        if line.startswith('### '):
            level = 3
            txt = line[4:]
            print(f'    * [{txt}](#{txt.replace(" ", "-")})')
        elif line.startswith('## '):
            level = 2
            txt = line[3:]
            print(f'  * [{txt}](#{txt.replace(" ", "-")})')
        elif line.startswith('# '):
            level = 1
            txt = line[2:]
            print(f'* [{txt}](#{txt.replace(" ", "-")})')
        else:
            continue
