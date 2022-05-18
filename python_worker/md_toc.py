# md_toc.py - Markdown table of contents

import sys

# Global. Keep a count of anchor names for disambiguation. 
texts = {}

def anchor(txt):
    s = f'{txt.replace(" ", "-").replace("/", "")}'
    if txt in texts:
        texts[txt] += 1
        n = texts[txt]
        s += f'-{n}'
    else:
        texts[txt] = 0
    return s

def handle_file(f):
    s = ''
    for line in f:
        line = line.rstrip()
        if line.startswith('### '):
            level = 3
            txt = line[4:]
            s += f'    * [{txt}](#{anchor(txt)})\n'
        elif line.startswith('## '):
            level = 2
            txt = line[3:]
            s += f'  * [{txt}](#{anchor(txt)})\n'
        elif line.startswith('# '):
            level = 1
            txt = line[2:]
            s += f'* [{txt}](#{anchor(txt)})\n'
        else:
            continue
    return s

#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------

# Command line argument
if len(sys.argv) != 2:
    s += f'Usage: {sys.argv[0]} <filepath>'
    exit(-1)
filepath = sys.argv[1]

with open(filepath, encoding='utf-8') as f:
    s = handle_file(f)

t = filepath.rsplit('.', 1)
outpath = f'{t[0]}_toc.{t[1]}'
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(s)