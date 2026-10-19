# Widens out-of-range branches reported by MACRO.
#   python3 tools/fixbranch.py file.mar line [line...]
# brb becomes brw; a conditional branch bxx L becomes b(not xx) .+4 (. is the operand's address) / brw L.
import sys
inv = {'beql':'bneq','bneq':'beql','bgtr':'bleq','bleq':'bgtr','bgeq':'blss',
       'blss':'bgeq','bgtru':'blequ','blequ':'bgtru','bgequ':'blssu',
       'blssu':'bgequ','bvs':'bvc','bvc':'bvs','bcs':'bcc','bcc':'bcs'}
p = sys.argv[1]
lines = open(p).read().split('\n')
for n in sorted((int(x) for x in sys.argv[2:]), reverse=True):
    l = lines[n-1]
    head, sep, comment = l.partition(';')
    parts = head.split()
    label = ''
    if parts and parts[0].endswith(':'):
        label = parts.pop(0)
    op, target = parts[0], parts[1]
    c = ('\t; ' + comment.strip()) if sep else ''
    if op == 'brb':
        lines[n-1] = f'{label}\tbrw\t{target}{c}'
    elif op in inv:
        lines[n-1] = f'{label}\t{inv[op]}\t.+4{c}\n\tbrw\t{target}'
    else:
        print('cannot fix', p, n, l)
open(p, 'w').write('\n'.join(lines))
